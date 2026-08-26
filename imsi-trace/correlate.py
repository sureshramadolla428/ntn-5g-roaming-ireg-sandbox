"""Cross-domain IMSI/SUPI correlation (best-effort)."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

IMSI_RE = re.compile(r"\b(0010100000000\d{2})\b")


@dataclass
class Event:
    ts: str
    domain: str
    imsi: str
    line: str


def parse_log(path: Path, domain: str) -> list[Event]:
    events = []
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines()):
        m = IMSI_RE.search(line)
        if m:
            events.append(Event(ts=str(i), domain=domain, imsi=m.group(1), line=line[:200]))
    return events


def correlate(logs: Iterable[tuple[str, Path]]) -> list[Event]:
    out: list[Event] = []
    for domain, path in logs:
        if path.exists():
            out.extend(parse_log(path, domain))
    return sorted(out, key=lambda e: (e.imsi, e.ts))


def export_jira_csv(events: list[Event], dest: Path) -> None:
    with dest.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Summary", "Description", "IMSI", "Domain", "Labels"])
        for e in events:
            w.writerow([f"IMSI event {e.imsi}", e.line, e.imsi, e.domain, "imsi-trace,lab"])
