"""Append-only action journal. This is the undo log."""
from __future__ import annotations

import json
import secrets
from pathlib import Path

from util import atomic_write_text, ensure_dir, ensure_private_file, from_iso, to_iso, utcnow

JOURNAL_NAME = "journal.jsonl"


class Journal:
    def __init__(self, state_dir: Path):
        self.state_dir = ensure_dir(Path(state_dir))
        self.path = self.state_dir / JOURNAL_NAME
        if not self.path.exists():
            atomic_write_text(self.path, "", private=True)

    @staticmethod
    def new_run_id() -> str:
        return utcnow().strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)

    def append(self, entry: dict) -> None:
        entry = dict(entry)
        entry.setdefault("ts", to_iso(utcnow()))
        line = json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n"
        with open(self.path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(line)
        ensure_private_file(self.path)

    def entries(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        with open(self.path, "r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
        return out

    def runs(self) -> list[dict]:
        grouped: dict[str, dict] = {}
        for entry in self.entries():
            run = entry.get("run") or "unknown"
            info = grouped.setdefault(run, {
                "run": run, "ts": entry.get("ts"), "ops": 0, "messages": 0,
                "unsubs": 0, "account": entry.get("account", ""),
            })
            info["ops"] += 1
            info["ts"] = entry.get("ts") or info["ts"]
            if entry.get("op") == "unsubscribe":
                info["unsubs"] += 1
            else:
                info["messages"] += len(entry.get("uids") or [])
        return sorted(grouped.values(), key=lambda item: item.get("ts") or "", reverse=True)

    def latest_run(self) -> str | None:
        runs = self.runs()
        return runs[0]["run"] if runs else None

    def run_entries(self, run_id: str) -> list[dict]:
        return [entry for entry in self.entries() if entry.get("run") == run_id]

    def summary(self, limit: int = 10) -> list[dict]:
        return self.runs()[:limit]

    def last_action_at(self) -> str | None:
        entries = self.entries()
        return entries[-1].get("ts") if entries else None

    def is_recent(self, within_seconds: int = 60) -> bool:
        last = from_iso(self.last_action_at())
        if not last:
            return False
        return (utcnow() - last).total_seconds() < within_seconds
