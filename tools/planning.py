"""Turn cached messages into a reviewable, reversible plan. No network here."""
from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from mailparse import choose_unsubscribe
from safety import flags_protected
from store import StoredMessage
from util import days_between, from_iso, human_bytes, to_iso, truncate, utcnow

PLAN_VERSION = 1
ARCHIVE = "__archive__"
JUNK = "__junk__"
TRASH = "__trash__"
KEEP_CATEGORIES = {"transactional", "personal"}


@dataclass
class Group:
    key: str
    category: str
    domain: str
    senders: list[str] = field(default_factory=list)
    count: int = 0
    actionable: int = 0
    unread: int = 0
    size: int = 0
    oldest: str | None = None
    newest: str | None = None
    confidence: int = 0
    protected: bool = False
    protected_reason: str | None = None
    reasons: list[str] = field(default_factory=list)
    samples: list[str] = field(default_factory=list)
    unsub: dict | None = None
    folder: str | None = None
    recommended: str = "keep"
    skipped: dict[str, int] = field(default_factory=dict)
    uids: dict[str, list[int]] = field(default_factory=dict)

    def to_dict(self, include_uids: bool = False) -> dict:
        data = {
            "key": self.key,
            "category": self.category,
            "domain": self.domain,
            "senders": self.senders[:12],
            "count": self.count,
            "actionable": self.actionable,
            "unread": self.unread,
            "size": self.size,
            "size_human": human_bytes(self.size),
            "oldest": self.oldest,
            "newest": self.newest,
            "confidence": self.confidence,
            "protected": self.protected,
            "protected_reason": self.protected_reason,
            "reasons": self.reasons,
            "samples": self.samples,
            "unsubscribe": self.unsub,
            "folder": self.folder,
            "recommended": self.recommended,
            "skipped": self.skipped,
        }
        if include_uids:
            data["uids"] = self.uids
        return data


@dataclass
class Plan:
    account: str
    mode: str
    groups: list[Group] = field(default_factory=list)
    actions: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)
    limits: dict = field(default_factory=dict)
    uidvalidity: dict[str, int] = field(default_factory=dict)
    generated: str = field(default_factory=lambda: to_iso(utcnow()))
    version: int = PLAN_VERSION

    def to_dict(self, include_uids: bool = True) -> dict:
        return {
            "version": self.version,
            "generated": self.generated,
            "account": self.account,
            "mode": self.mode,
            "limits": self.limits,
            "uidvalidity": self.uidvalidity,
            "stats": self.stats,
            "actions": self.actions,
            "groups": [group.to_dict(include_uids=include_uids) for group in self.groups],
        }


def build_plan(messages: list[StoredMessage], config, mode: str = "folders",
               only_categories: set[str] | None = None) -> Plan:
    policy = config.policy
    now = utcnow()
    buckets: dict[tuple[str, str, str], list[StoredMessage]] = defaultdict(list)

    for message in messages:
        category = message.category
        if only_categories and category not in only_categories:
            continue
        target = _target_key(message, config)
        buckets[(category, message.from_addr.rsplit("@", 1)[-1].lower(), target)].append(message)

    groups: list[Group] = []
    for (category, domain, _target), items in buckets.items():
        group = _build_group(category, domain, items, config, mode, now)
        if group:
            groups.append(group)

    groups.sort(key=lambda g: (not g.protected, -g.actionable, -g.count, g.category, g.domain))
    plan = Plan(account=config.account.email, mode=mode, groups=groups)
    plan.stats = _stats(messages, groups)
    plan.uidvalidity = {message.mailbox: message.uidvalidity for message in messages}
    plan.limits = {
        "min_age_days": policy.min_age_days,
        "max_messages_per_group": policy.max_messages_per_group,
        "max_messages_per_run": policy.max_messages_per_run,
        "mode": mode,
    }
    plan.actions = _actions(plan, config)
    return plan


def _target_key(message: StoredMessage, config) -> str:
    chosen = choose_unsubscribe(message.list_unsub, message.list_unsub_post,
                                config.unsubscribe)
    if chosen:
        if chosen.get("mode") == "mailto":
            return "mailto:" + chosen.get("address", "")
        return chosen.get("url", "") or "none"
    return "none"


def _build_group(category: str, domain: str, items: list[StoredMessage],
                 config, mode: str, now) -> Group | None:
    if not items:
        return None
    policy = config.policy
    group = Group(key="", category=category, domain=domain or "unknown")
    group.count = len(items)
    group.size = sum(max(0, item.size or 0) for item in items)
    group.unread = sum(1 for item in items if "\\Seen" not in {f.upper() for f in item.flags})
    group.confidence = max(item.confidence for item in items)
    group.senders = sorted({item.from_addr for item in items if item.from_addr})[:12]
    dates = sorted(item.date for item in items if item.date)
    group.oldest = dates[0] if dates else None
    group.newest = dates[-1] if dates else None
    group.protected = any(item.protected for item in items)
    group.protected_reason = next((item.protected_reason for item in items if item.protected), None)
    for item in items:
        for reason in item.reasons:
            if reason not in group.reasons:
                group.reasons.append(reason)
    group.reasons = group.reasons[:4]
    seen_subjects: list[str] = []
    for item in items:
        subject = truncate(item.subject, 90)
        if subject and subject not in seen_subjects:
            seen_subjects.append(subject)
        if len(seen_subjects) >= 3:
            break
    group.samples = seen_subjects

    chosen = None
    headers = Counter()
    for item in items:
        if item.list_unsub:
            headers[(item.list_unsub, item.list_unsub_post)] += 1
    if headers:
        header, post = headers.most_common(1)[0][0]
        chosen = choose_unsubscribe(header, post, config.unsubscribe)
        if chosen:
            group.unsub = {key: value for key, value in chosen.items() if key != "raw"}

    allowed_domain = domain.lower() not in {
        d.lower() for d in (policy.never_unsubscribe_domains or [])}
    if chosen and not allowed_domain:
        chosen = None
        group.unsub = None

    skip: Counter = Counter()
    uids: dict[str, list[int]] = defaultdict(list)
    dated: list[tuple[str, str, int]] = []
    for item in items:
        if item.protected:
            skip["protected"] += 1
            continue
        if category in KEEP_CATEGORIES:
            skip["kept_by_category"] += 1
            continue
        flag_reason = flags_protected(item.flags, policy)
        if flag_reason:
            skip[flag_reason] += 1
            continue
        age = days_between(from_iso(item.date), now)
        if age is None:
            skip["unknown_date"] += 1
            continue
        if age < policy.min_age_days:
            skip["too_recent"] += 1
            continue
        dated.append((item.date or "", item.mailbox, item.uid))

    dated.sort()  # oldest first
    per_group = max(0, int(policy.max_messages_per_group))
    for _date, mailbox, uid in dated[:per_group]:
        uids[mailbox].append(uid)
    if len(dated) > per_group:
        skip["group_limit"] += len(dated) - per_group

    group.uids = {mailbox: sorted(values) for mailbox, values in uids.items() if values}
    group.actionable = sum(len(values) for values in group.uids.values())
    group.skipped = dict(skip)
    group.folder = config.folder_for(category) if category != "spam" else JUNK
    if mode == "archive" and category != "spam":
        group.folder = ARCHIVE

    if group.protected:
        group.recommended = "keep (protected)"
    elif category in KEEP_CATEGORIES:
        group.recommended = "keep"
    elif category == "spam" and not policy.move_spam_to_junk:
        group.folder = None
        group.recommended = "keep (policy)"
    elif category == "spam":
        group.recommended = "move to Junk"
        if all(item.mailbox.upper() in {"JUNK", "SPAM", "BULK MAIL", "[GMAIL]/SPAM"}
               for item in items):
            group.folder = TRASH
            group.recommended = "move to Trash"
    elif group.actionable == 0:
        if group.unsub and group.unsub.get("automatic"):
            group.recommended = "unsubscribe only"
        elif group.unsub:
            group.recommended = "unsubscribe manually"
        else:
            group.recommended = "nothing to do"
    elif group.unsub and group.unsub.get("automatic"):
        group.recommended = "unsubscribe + file"
    elif group.unsub:
        group.recommended = "unsubscribe manually + file"
    else:
        group.recommended = "file"
    if mode == "archive" and group.actionable and category != "spam" \
            and group.recommended not in {"keep", "keep (protected)", "keep (policy)"}:
        group.recommended = ("unsubscribe + archive" if group.unsub and group.unsub.get("automatic")
                             else "archive")

    fingerprint = f"{category}|{domain}|{'|'.join(group.senders[:3])}"
    group.key = f"{category}-{domain or 'unknown'}-{hashlib.sha1(fingerprint.encode()).hexdigest()[:6]}"
    return group


def _stats(messages: list[StoredMessage], groups: list[Group]) -> dict:
    by_category = Counter(message.category for message in messages)
    return {
        "messages": len(messages),
        "groups": len(groups),
        "actionable": sum(group.actionable for group in groups),
        "protected": sum(1 for message in messages if message.protected),
        "categories": dict(by_category),
        "unread": sum(1 for message in messages
                      if "\\SEEN" not in {f.upper() for f in message.flags}),
        "bytes": sum(max(0, message.size or 0) for message in messages),
    }


def _actions(plan: Plan, config) -> list[dict]:
    actions: list[dict] = []
    seen_unsub: set[str] = set()
    counter = 0
    for group in plan.groups:
        if group.protected or group.category in KEEP_CATEGORIES:
            continue
        if group.category == "spam":
            # A spam unsubscribe target is untrusted and often confirms the address.
            continue
        if group.unsub and group.unsub.get("automatic") and config.unsubscribe.enabled:
            target = group.unsub.get("url") or group.unsub.get("address") or ""
            if target and target not in seen_unsub:
                seen_unsub.add(target)
                counter += 1
                actions.append({
                    "id": f"u{counter}",
                    "type": "unsubscribe",
                    "group": group.key,
                    "category": group.category,
                    "domain": group.domain,
                    "sender": (group.senders or [""])[0],
                    "target": target,
                    "mode": group.unsub.get("mode"),
                })
    total = 0
    for group in plan.groups:
        if group.protected or not group.uids:
            continue
        dest = group.folder
        if not dest:
            continue
        remaining = max(0, int(config.policy.max_messages_per_run) - total)
        if remaining <= 0:
            break
        for mailbox, uids in group.uids.items():
            if not uids or remaining <= 0:
                continue
            take = uids[:remaining]
            remaining -= len(take)
            total += len(take)
            counter += 1
            actions.append({
                "id": f"a{counter}",
                "type": "move",
                "group": group.key,
                "category": group.category,
                "mailbox": mailbox,
                "uids": take,
                "dest": dest,
            })
    return actions


def plan_from_dict(data: dict) -> Plan:
    if not isinstance(data, dict) or data.get("version") != PLAN_VERSION:
        raise ValueError("unsupported plan file (expected version 1)")
    mode = data.get("mode", "folders")
    if mode not in {"folders", "archive"}:
        raise ValueError(f"unsupported plan mode: {mode!r}")
    plan = Plan(account=str(data.get("account", "")), mode=mode)
    plan.generated = str(data.get("generated", ""))
    raw_actions = data.get("actions", []) or []
    if not isinstance(raw_actions, list):
        raise ValueError("plan actions must be an array")
    plan.actions = [_validated_action(action) for action in raw_actions]
    plan.stats = data.get("stats", {}) or {}
    plan.limits = data.get("limits", {}) or {}
    plan.uidvalidity = {str(k): int(v) for k, v in (data.get("uidvalidity") or {}).items()}
    for raw in data.get("groups", []):
        group = Group(
            key=raw.get("key", ""), category=raw.get("category", "personal"),
            domain=raw.get("domain", ""), senders=raw.get("senders", []),
            count=raw.get("count", 0), actionable=raw.get("actionable", 0),
            unread=raw.get("unread", 0), size=raw.get("size", 0),
            oldest=raw.get("oldest"), newest=raw.get("newest"),
            confidence=raw.get("confidence", 0), protected=bool(raw.get("protected")),
            protected_reason=raw.get("protected_reason"),
            reasons=raw.get("reasons", []), samples=raw.get("samples", []),
            unsub=raw.get("unsubscribe"), folder=raw.get("folder"),
            recommended=raw.get("recommended", "keep"), skipped=raw.get("skipped", {}),
        )
        plan.groups.append(group)
    return plan


def _validated_action(action) -> dict:
    if not isinstance(action, dict):
        raise ValueError("each plan action must be an object")
    kind = action.get("type")
    if kind not in {"move", "unsubscribe"}:
        raise ValueError(f"unknown plan action type: {kind!r}")
    result = dict(action)
    if kind == "move":
        uids = action.get("uids")
        if not isinstance(uids, list) or not uids:
            raise ValueError("a move action needs a non-empty uids array")
        clean = []
        for uid in uids:
            if isinstance(uid, bool) or not isinstance(uid, int) or uid <= 0:
                raise ValueError("move action uids must be positive integers")
            clean.append(uid)
        result["uids"] = clean
        if not isinstance(action.get("mailbox"), str) or not action.get("mailbox"):
            raise ValueError("a move action needs a mailbox")
        if not isinstance(action.get("dest"), str) or not action.get("dest"):
            raise ValueError("a move action needs a destination")
    else:
        if not isinstance(action.get("target"), str) or not action.get("target"):
            raise ValueError("an unsubscribe action needs a target")
        if action.get("mode") not in {"one-click", "http", "mailto", "manual"}:
            raise ValueError("an unsubscribe action has an unknown mode")
    return result


def plan_summary_lines(plan: Plan, limit: int = 25) -> list[str]:
    lines = []
    for group in plan.groups[:limit]:
        if group.actionable == 0 and group.category in KEEP_CATEGORIES:
            continue
        shield = "PROTECTED " if group.protected else ""
        lines.append(
            f"{shield}{group.category:<12} {group.domain[:34]:<34} "
            f"{group.count:>5} msgs  {group.unread:>5} unread  "
            f"{group.recommended:<22} {truncate('; '.join(group.samples[:1]), 48)}"
        )
    return lines
