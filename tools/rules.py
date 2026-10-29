"""Export server-side rules from a plan: Gmail filter XML and Sieve."""
from __future__ import annotations

from xml.sax.saxutils import escape, quoteattr

from planning import Plan
from util import unique


def _eligible(plan: Plan, config) -> list:
    out = []
    for group in plan.groups:
        if group.protected or group.category in {"transactional", "personal", "spam"}:
            continue
        if not group.senders:
            continue
        folder = config.folder_for(group.category)
        if not folder:
            continue
        out.append((group, folder))
    return out


def gmail_filters(plan: Plan, config) -> str:
    entries: list[str] = []
    seen: set[str] = set()
    for group, folder in _eligible(plan, config):
        for sender in group.senders[:25]:
            if sender in seen:
                continue
            seen.add(sender)
            entries.append(
                "  <entry>\n"
                "    <category term=\"filter\"/>\n"
                f"    <title>{escape('CleanYourMail: ' + sender)}</title>\n"
                f"    <apps:property name=\"from\" value={quoteattr(sender)}/>\n"
                "    <apps:property name=\"shouldArchive\" value=\"true\"/>\n"
                f"    <apps:property name=\"label\" value={quoteattr(folder)}/>\n"
                "  </entry>"
            )
    body = "\n".join(entries)
    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        "<feed xmlns=\"http://www.w3.org/2005/Atom\" "
        "xmlns:apps=\"http://schemas.google.com/apps/2006\">\n"
        "  <title>CleanYourMail filters</title>\n"
        f"{body}\n"
        "</feed>\n"
    )


def sieve(plan: Plan, config) -> str:
    lines = [
        "# CleanYourMail rules. Review before uploading.",
        "require [\"fileinto\"];",
        "",
    ]
    seen: set[str] = set()
    for group, folder in _eligible(plan, config):
        target = _sieve_string(folder)
        addresses = []
        for sender in group.senders[:25]:
            if sender in seen:
                continue
            seen.add(sender)
            addresses.append(sender)
        if not addresses:
            continue
        if len(addresses) == 1:
            condition = f'address :is "from" {_sieve_string(addresses[0])}'
        else:
            joined = ", ".join(_sieve_string(item) for item in addresses)
            condition = f'address :is "from" [{joined}]'
        lines.append(f"if {condition} {{")
        lines.append(f"    fileinto {target};")
        lines.append("    stop;")
        lines.append("}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _sieve_string(value: str) -> str:
    # Sieve quoted strings only need quote and backslash escaped.
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def filter_candidates(plan: Plan, config) -> int:
    return len(unique(sender for group, _folder in _eligible(plan, config)
                      for sender in group.senders[:25]))
