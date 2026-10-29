"""Unsubscribe with an SSRF guard. Never follows redirects, never sends cookies."""
from __future__ import annotations

import ipaddress
import re
import smtplib
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from email.message import EmailMessage

from config import Account
from util import domain_of

USER_AGENT = "CleanYourMail/1.0 (local unsubscribe)"
MAX_BYTES = 32768
MAX_URL_LENGTH = 2048
ALLOWED_PORTS = {443}
ALLOWED_PORTS_HTTP = {80, 443}

KNOWN_ESP_MAILTO = {
    "mailchimp.com", "sendgrid.net", "sendgrid.com", "constantcontact.com",
    "hubspot.com", "salesforce.com", "exacttarget.com", "mcsv.net",
    "rsgsv.net", "list-manage.com", "campaign-archive.com", "klaviyo.com",
    "mailerlite.com", "convertkit.com", "substack.com", "beehiiv.com",
    "customeriomail.com", "braze.com", "iterable.com", "mailgun.org",
    "mandrillapp.com", "sparkpostmail.com", "amazonses.com",
}


class UnsafeURL(ValueError):
    pass


@dataclass
class UnsubResult:
    status: str          # sent | manual | skipped | failed
    mode: str
    target: str
    code: int | None = None
    note: str = ""
    manual_url: str | None = None

    def to_dict(self) -> dict:
        return {
            "status": self.status, "mode": self.mode, "target": self.target,
            "code": self.code, "note": self.note, "manual_url": self.manual_url,
        }


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_url(url: str, allow_http: bool = False) -> str:
    """Reject anything that is not a public HTTPS endpoint."""
    if not url or len(url) > MAX_URL_LENGTH:
        raise UnsafeURL("unsubscribe URL is empty or too long")
    if any(ord(char) < 0x20 or char == "\x7f" for char in url):
        raise UnsafeURL("unsubscribe URL contains control characters")
    try:
        parsed = urllib.parse.urlsplit(url.strip())
    except ValueError as exc:
        raise UnsafeURL("unsubscribe URL is not valid") from exc
    scheme = parsed.scheme.lower()
    allowed = {"https"} | ({"http"} if allow_http else set())
    if scheme not in allowed:
        raise UnsafeURL(f"scheme {scheme!r} is not allowed")
    if parsed.username or parsed.password or "@" in parsed.netloc:
        raise UnsafeURL("URL contains credentials")
    host = parsed.hostname
    if not host:
        raise UnsafeURL("URL has no host")
    host = host.rstrip(".").lower()
    if host in {"localhost", "localhost.localdomain"} or host.endswith((".local", ".internal", ".localhost")):
        raise UnsafeURL("URL points to a local host")
    try:
        port = parsed.port or (443 if scheme == "https" else 80)
    except ValueError as exc:
        raise UnsafeURL("URL has an invalid port") from exc
    allowed_ports = ALLOWED_PORTS_HTTP if allow_http else ALLOWED_PORTS
    if port not in allowed_ports:
        raise UnsafeURL(f"port {port} is not allowed")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        ip = None
    if ip is not None:
        if not ip.is_global:
            raise UnsafeURL("URL points to a non-public IP address")
    else:
        try:
            ascii_host = host.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise UnsafeURL("URL host is not valid") from exc
        try:
            infos = socket.getaddrinfo(ascii_host, port, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise UnsafeURL(f"cannot resolve URL host: {exc}") from exc
        if not infos:
            raise UnsafeURL("URL host did not resolve")
        for info in infos:
            address = info[4][0]
            try:
                resolved = ipaddress.ip_address(address)
            except ValueError as exc:
                raise UnsafeURL("URL host resolved to an invalid address") from exc
            if not resolved.is_global:
                raise UnsafeURL("URL host resolves to a non-public address")
    clean = parsed._replace(fragment="")
    return urllib.parse.urlunsplit(clean)


def perform(account: Account, secret: str, chosen: dict, options,
            dry_run: bool = False) -> UnsubResult:
    mode = chosen.get("mode") or "manual"
    if mode in {"one-click", "http"}:
        url = chosen.get("url") or ""
        try:
            safe_url = validate_url(url, allow_http=bool(options.allow_http))
        except UnsafeURL as exc:
            return UnsubResult("skipped", mode, url, note=str(exc))
        if dry_run:
            return UnsubResult("skipped", mode, safe_url, note="dry run")
        return http_unsubscribe(safe_url, one_click=(mode == "one-click"),
                                timeout=int(options.timeout_seconds))
    if mode == "mailto":
        address = chosen.get("address") or ""
        if not _mailto_allowed(address, chosen.get("sender") or account.email):
            return UnsubResult("manual", "mailto", address,
                               note="mailto domain is unrelated to the sender; open it manually",
                               manual_url="mailto:" + address)
        if dry_run:
            return UnsubResult("skipped", "mailto", address, note="dry run")
        return mailto_unsubscribe(account, secret, address,
                                  subject=chosen.get("subject") or "unsubscribe",
                                  body=chosen.get("body") or "unsubscribe",
                                  timeout=int(options.timeout_seconds))
    return UnsubResult("manual", mode, chosen.get("url") or chosen.get("address") or "",
                       note=chosen.get("reason") or "manual confirmation required",
                       manual_url=chosen.get("url") or (
                           "mailto:" + chosen["address"] if chosen.get("address") else None))


def _mailto_allowed(address: str, sender: str) -> bool:
    target_domain = domain_of(address)
    sender_domain = domain_of(sender)
    if not target_domain:
        return False
    if target_domain == sender_domain:
        return True
    if _base_domain(target_domain) == _base_domain(sender_domain):
        return True
    return any(target_domain == esp or target_domain.endswith("." + esp)
               for esp in KNOWN_ESP_MAILTO)


def _base_domain(domain: str) -> str:
    parts = [part for part in (domain or "").lower().split(".") if part]
    if len(parts) <= 2:
        return ".".join(parts)
    # Good enough for the common two-level public suffixes we see in mail.
    two_level = {"co.uk", "com.au", "co.jp", "com.br", "co.nz", "co.za", "com.mx",
                 "com.ar", "com.co", "com.es", "com.tr", "co.in", "com.sg"}
    if ".".join(parts[-2:]) in two_level:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def http_unsubscribe(url: str, one_click: bool = True, timeout: int = 15) -> UnsubResult:
    data = b"List-Unsubscribe=One-Click" if one_click else None
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/plain, text/html;q=0.5",
    }
    if data is not None:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    request = urllib.request.Request(url, data=data, headers=headers,
                                     method="POST" if data is not None else "GET")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            code = getattr(response, "status", None) or response.getcode()
            response.read(MAX_BYTES)
    except urllib.error.HTTPError as exc:
        code = exc.code
        if code in {301, 302, 303, 307, 308}:
            location = exc.headers.get("Location") if exc.headers else None
            return UnsubResult("manual", "one-click" if one_click else "http", url,
                               code=code, note="redirects are not followed; confirm in the browser",
                               manual_url=location or url)
        if code in {404, 410}:
            return UnsubResult("sent", "one-click" if one_click else "http", url,
                               code=code, note="the sender says this address is already unsubscribed")
        if code in {405, 501}:
            return UnsubResult("manual", "one-click" if one_click else "http", url,
                               code=code, note="the server does not support this method",
                               manual_url=url)
        if code == 429:
            return UnsubResult("failed", "one-click" if one_click else "http", url,
                               code=code, note="rate limited; try again tomorrow")
        return UnsubResult("failed", "one-click" if one_click else "http", url,
                           code=code, note=f"HTTP {code}")
    except (urllib.error.URLError, TimeoutError, ssl.SSLError, OSError, ValueError) as exc:
        return UnsubResult("failed", "one-click" if one_click else "http", url,
                           note=f"network error: {exc}")
    if 200 <= int(code) < 300:
        return UnsubResult("sent", "one-click" if one_click else "http", url,
                           code=int(code), note="request accepted")
    return UnsubResult("failed", "one-click" if one_click else "http", url,
                       code=int(code), note=f"HTTP {code}")


def mailto_unsubscribe(account: Account, secret: str, address: str, subject: str,
                       body: str, timeout: int = 15) -> UnsubResult:
    if not account.smtp_host:
        return UnsubResult("manual", "mailto", address,
                           note="no SMTP host configured", manual_url="mailto:" + address)
    subject = _clean_header(subject) or "unsubscribe"
    body = _clean_body(body) or "unsubscribe"
    message = EmailMessage()
    message["From"] = account.email
    message["To"] = _clean_header(address)
    message["Subject"] = subject
    message["Auto-Submitted"] = "auto-generated"
    message.set_content(body)
    try:
        if account.smtp_ssl:
            smtp = smtplib.SMTP_SSL(account.smtp_host, int(account.smtp_port),
                                    timeout=timeout, context=ssl.create_default_context())
        else:
            smtp = smtplib.SMTP(account.smtp_host, int(account.smtp_port), timeout=timeout)
        with smtp:
            if not account.smtp_ssl and account.smtp_starttls:
                smtp.starttls(context=ssl.create_default_context())
            if secret:
                smtp.login(account.email, secret)
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError, ssl.SSLError) as exc:
        return UnsubResult("failed", "mailto", address, note=f"SMTP error: {exc}")
    return UnsubResult("sent", "mailto", address, note="email sent")


def _clean_header(value: str) -> str:
    return re.sub(r"[\r\n]+", " ", value or "").strip()[:200]


def _clean_body(value: str) -> str:
    return re.sub(r"[\r\n]+", " ", value or "").strip()[:500]


def polite_delay(seconds: float, sleeper=time.sleep) -> None:
    if seconds > 0:
        sleeper(seconds)
