"""Microsoft OAuth 2.0 for IMAP and SMTP.

CleanYourMail uses the OAuth 2.0 device-code flow, which is designed for public
clients: there is no client secret, no browser callback and no local web server.
The person opens a Microsoft page, enters a short code and approves the request.

Only the refresh token is stored on disk. Access tokens live in memory for the
duration of one command. The file is created with owner-only permissions where
the platform supports them.
"""
from __future__ import annotations

import base64
import json
import os
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

AUTHORITY = "https://login.microsoftonline.com/common/oauth2/v2.0"
DEVICE_CODE_URL = AUTHORITY + "/devicecode"
TOKEN_URL = AUTHORITY + "/token"

# IMAP is required. SMTP is only used for mailto: unsubscribe requests; including
# the scope is harmless when a tenant disables SMTP AUTH.
DEFAULT_SCOPE = (
    "openid profile email offline_access "
    "https://outlook.office.com/IMAP.AccessAsUser.All "
    "https://outlook.office.com/SMTP.Send"
)

CLIENT_ID_ENV = "CYM_MS_CLIENT_ID"
# Public client ID for the CleanYourMail application. It is not a secret.
# Leave empty until the project application is registered, or let each person
# set CYM_MS_CLIENT_ID / account.oauth_client_id.
PROJECT_CLIENT_ID = ""
STORE_ENV = "CYM_OAUTH_STORE"
STORE_FILENAME = "cleanyourmail-oauth.json"
DEVICE_FILENAME = "cleanyourmail-device.json"
PROVIDER = "microsoft"


class OAuthError(Exception):
    """Microsoft sign-in failed or the local token store is unusable."""


@dataclass(frozen=True)
class DeviceCode:
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int
    message: str


@dataclass(frozen=True)
class Token:
    access_token: str
    refresh_token: str
    expires_in: int
    scope: str = ""
    id_token: str = ""


def client_id_from_env() -> str:
    return os.environ.get(CLIENT_ID_ENV, "").strip() or PROJECT_CLIENT_ID


def store_path(explicit: str | Path | None = None) -> Path:
    if explicit:
        return Path(os.path.expanduser(str(explicit)))
    override = os.environ.get(STORE_ENV, "").strip()
    if override:
        return Path(os.path.expanduser(override))
    return Path.home() / ".secrets" / STORE_FILENAME


def _clean(value: object, limit: int = 300) -> str:
    text = " ".join(str(value or "").split())
    return text[:limit]


def _describe_error(payload: dict, status: int) -> OAuthError:
    code = _clean(payload.get("error") or "oauth_error", 80)
    description = _clean(payload.get("error_description") or "sign-in failed")
    suffix = f", HTTP {status}" if status else ""
    return OAuthError(f"Microsoft sign-in failed ({code}{suffix}): {description}")


def _token_from_payload(payload: dict, fallback_refresh: str = "") -> Token:
    access = payload.get("access_token")
    refresh = payload.get("refresh_token") or fallback_refresh
    if not isinstance(access, str) or not access:
        raise OAuthError("Microsoft sign-in did not return an access token.")
    if not isinstance(refresh, str) or not refresh:
        raise OAuthError("Microsoft sign-in did not return a refresh token.")
    try:
        expires = int(payload.get("expires_in") or 3600)
    except (TypeError, ValueError):
        expires = 3600
    return Token(
        access_token=access,
        refresh_token=refresh,
        expires_in=max(60, expires),
        scope=_clean(payload.get("scope"), 500),
        id_token=str(payload.get("id_token") or ""),
    )


def account_from_id_token(id_token: str) -> str:
    """Read the sign-in name from an ID token. The token comes directly from Microsoft."""
    if not id_token or id_token.count(".") != 2:
        return ""
    payload = id_token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    try:
        data = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return ""
    if not isinstance(data, dict):
        return ""
    for key in ("preferred_username", "email", "upn", "unique_name"):
        value = data.get(key)
        if isinstance(value, str) and "@" in value:
            return value
    return ""


def _post(url: str, data: dict[str, str], opener=None, timeout: int = 30) -> tuple[int, dict]:
    """POST a form and return (status, JSON). Never raises for OAuth error payloads."""
    body = urllib.parse.urlencode(data).encode("ascii")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "User-Agent": "CleanYourMail/1.0",
        },
    )
    open_fn = opener or urllib.request.urlopen
    try:
        with open_fn(request, timeout=timeout) as response:
            status = int(getattr(response, "status", 200) or 200)
            raw = response.read()
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        raw = exc.read()
    except (urllib.error.URLError, OSError) as exc:
        raise OAuthError(f"Cannot reach Microsoft sign-in: {_clean(exc)}") from exc
    try:
        payload = json.loads(raw.decode("utf-8", "replace"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise OAuthError("Microsoft sign-in returned an invalid response.") from exc
    if not isinstance(payload, dict):
        raise OAuthError("Microsoft sign-in returned an unexpected response.")
    return status, payload


def start_device_flow(client_id: str, scope: str = DEFAULT_SCOPE, login_hint: str = "",
                      opener=None) -> DeviceCode:
    if not client_id:
        raise OAuthError("No Microsoft application ID configured.")
    data = {"client_id": client_id, "scope": scope}
    if login_hint:
        data["login_hint"] = login_hint
    status, payload = _post(DEVICE_CODE_URL, data, opener=opener)
    if status >= 400 or "error" in payload:
        raise _describe_error(payload, status)
    try:
        return DeviceCode(
            device_code=str(payload["device_code"]),
            user_code=str(payload["user_code"]),
            verification_uri=str(payload.get("verification_uri")
                                 or payload.get("verification_url") or ""),
            expires_in=int(payload.get("expires_in") or 900),
            interval=int(payload.get("interval") or 5),
            message=_clean(payload.get("message"), 500),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise OAuthError("Microsoft sign-in did not return a device code.") from exc


def poll_for_token(device_code: str, client_id: str, interval: int, expires_in: int,
                   opener=None, sleep=time.sleep, clock=time.monotonic) -> Token:
    """Wait for the person to approve the request. Returns a refreshable token."""
    deadline = clock() + max(1, int(expires_in))
    wait = max(1, int(interval))
    while True:
        if clock() >= deadline:
            raise OAuthError(
                "The Microsoft sign-in code expired. Run `python tools/mail.py connect outlook` again."
            )
        sleep(wait)
        status, payload = _post(TOKEN_URL, {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": client_id,
            "device_code": device_code,
        }, opener=opener)
        error = str(payload.get("error") or "")
        if not error:
            return _token_from_payload(payload)
        if error == "authorization_pending":
            continue
        if error == "slow_down":
            wait += 5
            continue
        if error in {"expired_token", "code_expired"}:
            raise OAuthError(
                "The Microsoft sign-in code expired. Run `python tools/mail.py connect outlook` again."
            )
        if error == "authorization_declined":
            raise OAuthError("Microsoft sign-in was declined.")
        raise _describe_error(payload, status)


def refresh_access_token(refresh_token: str, client_id: str, scope: str = DEFAULT_SCOPE,
                         opener=None) -> Token:
    if not refresh_token:
        raise OAuthError("No Microsoft refresh token is stored.")
    if not client_id:
        raise OAuthError("No Microsoft application ID configured.")
    status, payload = _post(TOKEN_URL, {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token,
        "scope": scope or DEFAULT_SCOPE,
    }, opener=opener)
    if status >= 400 or "error" in payload:
        error = str(payload.get("error") or "")
        if error == "invalid_grant":
            raise OAuthError(
                "The saved Microsoft sign-in expired or was revoked. "
                "Run `python tools/mail.py connect outlook` again."
            )
        raise _describe_error(payload, status)
    return _token_from_payload(payload, fallback_refresh=refresh_token)


def load_store(path: str | Path | None = None) -> dict:
    file = store_path(path)
    try:
        text = file.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"version": 1}
    except OSError as exc:
        raise OAuthError(f"Cannot read the saved Microsoft sign-in: {_clean(exc)}") from exc
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise OAuthError(
            "The saved Microsoft sign-in file is not valid JSON. "
            "Run `python tools/mail.py connect outlook` again."
        ) from exc
    if not isinstance(data, dict):
        raise OAuthError(
            "The saved Microsoft sign-in file is invalid. "
            "Run `python tools/mail.py connect outlook` again."
        )
    return data


def save_store(data: dict, path: str | Path | None = None) -> Path:
    file = store_path(path)
    temp: Path | None = None
    try:
        created = not file.parent.exists()
        file.parent.mkdir(parents=True, exist_ok=True)
        if created:
            try:
                os.chmod(file.parent, 0o700)
            except OSError:
                pass
        descriptor, temp_name = tempfile.mkstemp(prefix=file.name + ".", dir=str(file.parent))
        temp = Path(temp_name)
        text = json.dumps(data, indent=2, sort_keys=True) + "\n"
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.chmod(temp, 0o600)
        os.replace(temp, file)
    except OSError as exc:
        if temp is not None:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass
        raise OAuthError(f"Cannot save the Microsoft sign-in locally: {_clean(exc)}") from exc
    return file


def save_token(client_id: str, token: Token, email: str = "",
               path: str | Path | None = None) -> Path:
    data = load_store(path)
    data["version"] = 1
    data[PROVIDER] = {
        "client_id": client_id,
        "email": email,
        "scope": token.scope or DEFAULT_SCOPE,
        "refresh_token": token.refresh_token,
        "obtained_at": int(time.time()),
    }
    return save_store(data, path)


def stored_token(path: str | Path | None = None) -> dict | None:
    entry = load_store(path).get(PROVIDER)
    return entry if isinstance(entry, dict) else None


def device_path(path: str | Path | None = None) -> Path:
    if path:
        return Path(os.path.expanduser(str(path)))
    return store_path().with_name(DEVICE_FILENAME)


def save_device(device: DeviceCode, client_id: str, email: str = "",
                scope: str = DEFAULT_SCOPE, path: str | Path | None = None) -> Path:
    data = {
        "version": 1,
        "device_code": device.device_code,
        "client_id": client_id,
        "email": email,
        "scope": scope,
        "interval": device.interval,
        "expires_at": int(time.time()) + max(60, device.expires_in),
        "verification_uri": device.verification_uri,
        "user_code": device.user_code,
    }
    return save_store(data, device_path(path))


def load_device(path: str | Path | None = None) -> dict | None:
    file = device_path(path)
    if not file.exists():
        return None
    data = load_store(file)
    if not data.get("device_code") or not data.get("client_id"):
        return None
    return data


def clear_device(path: str | Path | None = None) -> None:
    try:
        device_path(path).unlink(missing_ok=True)
    except OSError:
        pass


def access_token(client_id: str = "", path: str | Path | None = None, opener=None,
                 email: str = "") -> str:
    """Return a fresh access token, refreshing the stored refresh token."""
    entry = stored_token(path)
    if not entry or not entry.get("refresh_token"):
        raise OAuthError(
            "No Microsoft sign-in found. Run `python tools/mail.py connect outlook` first."
        )
    stored_email = str(entry.get("email") or "").strip()
    if email and stored_email and stored_email.lower() != email.lower():
        raise OAuthError(
            f"The saved Microsoft sign-in belongs to a different account ({stored_email}). "
            f"Run `python tools/mail.py connect outlook` again for {email}."
        )
    stored_client = str(entry.get("client_id") or "").strip()
    configured_client = str(client_id or "").strip()
    if configured_client and stored_client and configured_client != stored_client:
        raise OAuthError(
            "The saved Microsoft sign-in belongs to a different Microsoft application. "
            "Run `python tools/mail.py connect outlook` again."
        )
    resolved_client = stored_client or configured_client
    if not resolved_client:
        raise OAuthError("No Microsoft application ID configured.")
    token = refresh_access_token(
        str(entry["refresh_token"]),
        resolved_client,
        scope=str(entry.get("scope") or DEFAULT_SCOPE),
        opener=opener,
    )
    if token.refresh_token != entry.get("refresh_token"):
        entry["refresh_token"] = token.refresh_token
        data = load_store(path)
        data[PROVIDER] = entry
        save_store(data, path)
    return token.access_token
