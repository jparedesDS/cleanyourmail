"""Protected mail and classification vocabulary. Rules are intentionally conservative."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from mailparse import ParsedHeaders, auth_failed, clean_subject

# Words that mean "a human, a bill or an account depends on this". When in doubt,
# we protect: a missed newsletter is a nuisance, a missed bank notice is not.
PROTECTED_SUBJECT = re.compile(
    r"(?:\b(?:security|verify|verification|code|otp|one[- ]time|password|passcode|2fa|two[- ]factor|"
    r"sign[- ]?in|login|account|alert|statement|invoice|receipt|payment|paid|refund|tax|payroll|"
    r"payslip|bank|card|loan|mortgage|insurance|policy|claim|appointment|prescription|medical|"
    r"lab result|visa|passport|boarding|flight|booking|reservation|itinerary|order|shipment|"
    r"delivery|contract|legal|court|government|immigration|social security|tuition|rent|utility)\b|"
    r"\b(?:seguridad|verificaci[oó]n|c[oó]digo|contrase[nñ]a|cuenta|alerta|extracto|factura|recibo|"
    r"pago|pagado|reembolso|impuesto|n[oó]mina|banco|tarjeta|pr[eé]stamo|hipoteca|seguro|p[oó]liza|"
    r"reclamaci[oó]n|cita|receta|m[eé]dico|resultado|visado|pasaporte|embarque|vuelo|reserva|"
    r"itinerario|pedido|env[ií]o|entrega|contrato|legal|juzgado|gobierno|inmigraci[oó]n|"
    r"matr[ií]cula|alquiler|luz|agua|gas)\b)",
    re.IGNORECASE,
)

TRANSACTIONAL = re.compile(
    r"(?:\b(?:order\s*(?:#|no\.?|number|confirmation)|your order|order confirmed|"
    r"invoice|receipt|payment received|payment confirmation|statement|shipped|tracking|"
    r"delivery|booking|reservation|itinerary|boarding pass|check[- ]in|verification code|"
    r"security code|one[- ]time code|otp|password reset|security alert|sign[- ]in attempt|"
    r"refund|tax|payroll|payslip|policy renewal|claim|appointment|prescription)\b|"
    r"\b(?:pedido|factura|recibo|pago recibido|confirmaci[oó]n de pago|extracto|enviado|"
    r"seguimiento|entrega|reserva|itinerario|tarjeta de embarque|facturaci[oó]n|"
    r"c[oó]digo de (?:verificaci[oó]n|seguridad)|alerta de seguridad|reembolso|"
    r"impuesto|n[oó]mina|p[oó]liza|reclamaci[oó]n|cita|receta)\b)",
    re.IGNORECASE,
)

PROMOTION = re.compile(
    r"(?:\b(?:sale|deal|deals|offer|offers|discount|coupon|promo|promotion|voucher|"
    r"free shipping|limited time|last chance|don'?t miss|exclusive|save|% off|"
    r"black friday|cyber monday|prime day|new arrival|shop now|buy now|upgrade|trial|"
    r"webinar|newsletter|digest|price drop|clearance|bogo)\b|"
    r"\b(?:oferta|ofertas|descuento|cup[oó]n|promoci[oó]n|env[ií]o gratis|"
    r"tiempo limitado|[uú]ltima oportunidad|no te lo pierdas|exclusivo|rebaja|"
    r"rebajas|gratis|novedad|comprar|suscr[ií]bete|bolet[ií]n|newsletter)\b|"
    r"[€$£]\s?\d|\d+\s?%\s?(?:off|de descuento|dto)|(?:^|\s)-\d+%)",
    re.IGNORECASE,
)

NEWSLETTER = re.compile(
    r"(?:\b(?:newsletter|digest|weekly|daily|monthly|briefing|bulletin|roundup|"
    r"this week|in case you missed|issue\s*#|vol\.?\s*\d|edition|update|"
    r"noticias|bolet[ií]n|resumen|semanario|edici[oó]n|novedades)\b)",
    re.IGNORECASE,
)

SPAM = re.compile(
    r"(?:\b(?:winner|prize|lottery|congratulations|you have been selected|"
    r"crypto|bitcoin|investment opportunity|viagra|pharmacy|weight loss|"
    r"work from home|earn (?:money|from home)|urgent|act now|"
    r"wire transfer|inheritance|unclaimed|risk[- ]free|guaranteed)\b|"
    r"\b(?:ganador|premio|loter[ií]a|felicidades|has sido seleccionado|"
    r"criptomoneda|inversi[oó]n|p[eé]rdida de peso|trabaja desde casa|"
    r"gana dinero|urgente|act[uú]a ahora|transferencia|herencia|"
    r"sin riesgo|garantizado)\b)",
    re.IGNORECASE,
)

COLD = re.compile(
    r"(?:\b(?:quick question|following up|follow[- ]up|partnership|opportunity|"
    r"book a call|schedule a call|demo|pricing|are you the right person|"
    r"reaching out|saw your|helping companies|solutions for|limited slots|"
    r"would love to|circle back|touch base|introduction)\b)",
    re.IGNORECASE,
)

SOCIAL_DOMAINS = {
    "facebookmail.com", "facebook.com", "linkedin.com", "twitter.com", "x.com",
    "instagram.com", "tiktok.com", "reddit.com", "redditmail.com", "pinterest.com",
    "meetup.com", "nextdoor.com", "discord.com", "discordapp.com", "quora.com",
    "snapchat.com", "threads.net", "mastodon.social",
}

NOTIFICATION_LOCAL = {
    "no-reply", "noreply", "no_reply", "donotreply", "do-not-reply", "do_not_reply",
    "notifications", "notification", "notify", "alerts", "alert", "updates", "update",
    "mailer-daemon", "postmaster", "bounces", "bounce", "support", "hello",
}

AUTOMATED_LOCAL = NOTIFICATION_LOCAL - {"support", "hello"}


@dataclass
class Verdict:
    protected: bool = False
    reason: str | None = None


def protect_verdict(headers: ParsedHeaders, protect_domains: list[str] | None = None,
                    protect_addresses: list[str] | None = None) -> Verdict:
    reason = sender_protected(headers.from_addr, protect_domains, protect_addresses)
    if reason:
        return Verdict(True, reason)
    subject = clean_subject(headers.subject)
    match = PROTECTED_SUBJECT.search(subject)
    if match:
        return Verdict(True, f"subject looks transactional ({match.group(0).lower()!r})")
    return Verdict(False, None)


def sender_protected(from_addr: str, protect_domains: list[str] | None = None,
                     protect_addresses: list[str] | None = None) -> str | None:
    """Check the configured sender allow-list. Used again at apply time."""
    domains = {d.strip().lower() for d in (protect_domains or []) if d}
    addresses = {a.strip().lower() for a in (protect_addresses or []) if a}
    sender = (from_addr or "").strip().lower()
    if not sender or "@" not in sender:
        return None
    if sender in addresses:
        return f"sender {sender} is on your protected list"
    domain = sender.rsplit("@", 1)[1].strip(">").strip()
    if domain in domains:
        return f"domain {domain} is on your protected list"
    if any(domain.endswith("." + protected) for protected in domains):
        return f"domain {domain} is on your protected list"
    return None


def flags_protected(flags: list[str], policy) -> str | None:
    upper = {flag.upper() for flag in flags}
    if policy.protect_flagged and "\\FLAGGED" in upper:
        return "message is starred"
    if policy.protect_answered and "\\ANSWERED" in upper:
        return "you already replied to this message"
    return None


@dataclass
class Classification:
    category: str = "personal"
    confidence: int = 0
    reasons: list[str] = field(default_factory=list)
    protected: bool = False
    protected_reason: str | None = None
    bulk: bool = False

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "confidence": self.confidence,
            "reasons": self.reasons,
            "protected": self.protected,
            "protected_reason": self.protected_reason,
            "bulk": self.bulk,
        }


PRIORITY = {
    "social": 8,
    "transactional": 7,
    "spam": 6,
    "newsletter": 5,
    "promotion": 4,
    "notification": 3,
    "cold": 2,
    "personal": 1,
}


def classify(headers: ParsedHeaders, mailbox: str = "INBOX", policy=None) -> Classification:
    """Score the headers against known bulk-mail shapes and pick one category."""
    verdict = protect_verdict(
        headers,
        getattr(policy, "protect_domains", []) if policy else [],
        getattr(policy, "protect_addresses", []) if policy else [],
    )
    scores: dict[str, int] = {name: 0 for name in PRIORITY}
    reasons: dict[str, list[str]] = {name: [] for name in PRIORITY}

    def add(category: str, points: int, reason: str) -> None:
        scores[category] += points
        if reason not in reasons[category]:
            reasons[category].append(reason)

    local = (headers.from_addr.split("@", 1)[0].lower() if "@" in headers.from_addr else "")
    subject = clean_subject(headers.subject)
    bulk = headers.is_bulk

    if headers.list_unsub:
        add("newsletter", 20, "has a List-Unsubscribe header")
        add("promotion", 20, "has a List-Unsubscribe header")
    if headers.list_id:
        add("newsletter", 30, "is a mailing list (List-ID)")
    if headers.feedback_id or headers.x_campaign:
        add("promotion", 20, "has campaign/bulk identifiers")
    if (headers.precedence or "") in {"bulk", "list", "junk"}:
        add("newsletter", 10, f"Precedence: {headers.precedence}")
    if headers.auto_submitted.startswith("auto-"):
        add("notification", 35, "Auto-Submitted header")
    if local in AUTOMATED_LOCAL:
        add("notification", 25, f"sender is automated ({local}@)")
        add("transactional", 5, f"sender is automated ({local}@)")

    promo_hits = PROMOTION.findall(subject)
    if promo_hits:
        add("promotion", min(45, 25 + 10 * len(promo_hits)),
            f"promotional subject ({promo_hits[0]})")
        add("newsletter", 5, "promotional wording")
    newsletter_hits = NEWSLETTER.findall(subject)
    if newsletter_hits:
        add("newsletter", 30, f"newsletter wording ({newsletter_hits[0]})")
    transactional_hits = TRANSACTIONAL.findall(subject)
    if transactional_hits:
        add("transactional", 55, f"transactional subject ({transactional_hits[0]})")
    if verdict.protected:
        add("transactional", 20, verdict.reason or "protected sender")

    if headers.from_domain in SOCIAL_DOMAINS or any(
            headers.from_domain.endswith("." + domain) for domain in SOCIAL_DOMAINS):
        add("social", 70, "social network sender")

    spam_hits = SPAM.findall(subject)
    if spam_hits:
        add("spam", 25, f"spam-like wording ({spam_hits[0]})")
    if auth_failed(headers.auth_results):
        add("spam", 55, "SPF/DKIM/DMARC authentication failed")
        add("promotion", 10, "authentication failed")
    if mailbox.upper() in {"JUNK", "SPAM", "BULK MAIL", "[GMAIL]/SPAM"}:
        add("spam", 60, "message is already in the spam folder")

    if bulk:
        add("newsletter", 15, "bulk mail shape")
        add("promotion", 10, "bulk mail shape")
        add("notification", 5, "bulk mail shape")
    else:
        add("personal", 25, "not bulk mail")
        if headers.subject.lower().startswith(("re:", "re :", "aw:", "sv:")):
            add("personal", 20, "looks like a reply")
        if headers.to_addrs and not headers.list_id and not headers.list_unsub:
            add("personal", 10, "addressed to you directly")
        cold_hits = COLD.findall(subject)
        if cold_hits:
            add("cold", 30, f"sales outreach wording ({cold_hits[0]})")
            add("personal", -5, "sales outreach wording")
            if headers.reply_to and headers.from_domain and \
                    headers.reply_to.rsplit("@", 1)[-1] != headers.from_domain:
                add("cold", 10, "Reply-To is on a different domain")

    # A newsletter-looking subject with no bulk headers is still personal mail.
    if not bulk and newsletter_hits and not promo_hits:
        add("personal", 15, "no bulk headers")

    best = max(scores, key=lambda name: (scores[name], PRIORITY[name]))
    if scores[best] <= 0:
        best = "personal"
        scores[best] = 10
        reasons[best] = ["no strong signals"]
    confidence = max(0, min(100, scores[best]))
    ordered = reasons[best][:4] or ["no strong signals"]
    return Classification(
        category=best,
        confidence=confidence,
        reasons=ordered,
        protected=verdict.protected,
        protected_reason=verdict.reason,
        bulk=bulk,
    )


def is_transactional(category: str) -> bool:
    return category in {"transactional", "personal"}


def needs_human(category: str) -> bool:
    return category in {"transactional", "personal", "cold", "spam"}
