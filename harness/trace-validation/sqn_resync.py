"""Scan lab logs for SQN resynchronization markers (TC-04 observation helper).

Does not inject AUTS — observation only. TS 33.102 §6.3.5 / TS 29.272
Re-Synchronization-Info cited in matrix; pattern list is UNVERIFIED heuristic.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# UNVERIFIED — log substring heuristics; confirm against MEASURED pcaps
RESYNC_PATTERNS: tuple[str, ...] = (
    r"resync",
    r"re-?synchron",
    r"AUTS",
    r"synch failure",
    r"SQN",
    r"mac.?failure.*synch",
    r"Authentication reject",
    r"5G-AKA.*fail",
)

RESYNC_RE = re.compile("|".join(f"({p})" for p in RESYNC_PATTERNS), re.IGNORECASE)

DEFAULT_CONTAINERS: tuple[str, ...] = (
    "home-ausf",
    "home-udm",
    "home-udr",
    "home-hss",
    "visited-amf",
)


@dataclass
class ScanResult:
    """Aggregated resync scan output."""

    hits: list[tuple[str, str]] = field(default_factory=list)

    @property
    def found(self) -> bool:
        return bool(self.hits)


def scan_text(label: str, text: str, result: ScanResult) -> None:
    """Record matching lines from *text* under *label*."""
    for line in text.splitlines():
        if RESYNC_RE.search(line):
            result.hits.append((label, line.strip()))


def scan_file(path: Path, result: ScanResult) -> None:
    """Scan a local log or NOTES file."""
    if not path.is_file():
        return
    scan_text(str(path), path.read_text(encoding="utf-8", errors="replace"), result)


def scan_docker(container: str, tail: int, result: ScanResult) -> None:
    """Tail docker logs for *container* if present."""
    try:
        proc = subprocess.run(
            ["docker", "logs", "--tail", str(tail), container],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        print(f"SKIP docker {container}: {exc}", file=sys.stderr)
        return
    body = (proc.stdout or "") + (proc.stderr or "")
    if body.strip():
        scan_text(container, body, result)


def scan_pcap_dir(pcap_dir: Path, result: ScanResult) -> None:
    """Scan docker-logs under a capture directory."""
    logs = pcap_dir / "docker-logs"
    if logs.is_dir():
        for log in sorted(logs.glob("*.log")):
            scan_file(log, result)
    notes = pcap_dir / "NOTES.md"
    scan_file(notes, result)


def main(argv: list[str] | None = None) -> int:
    """CLI entry: scan files and/or docker containers for resync markers."""
    parser = argparse.ArgumentParser(description="TC-04 SQN resync log observer")
    parser.add_argument("--scan-docker", action="store_true", help="Tail known NF containers")
    parser.add_argument("--tail", type=int, default=400, help="Docker log tail lines")
    parser.add_argument("--pcap-dir", type=Path, help="Capture dir (pcaps/TC-04/<ts>)")
    parser.add_argument("paths", nargs="*", type=Path, help="Extra log files")
    args = parser.parse_args(argv)

    result = ScanResult()
    if args.pcap_dir:
        scan_pcap_dir(args.pcap_dir, result)
    for path in args.paths:
        if path.is_dir():
            scan_pcap_dir(path, result)
        else:
            scan_file(path, result)
    if args.scan_docker:
        for c in DEFAULT_CONTAINERS:
            scan_docker(c, args.tail, result)

    if result.found:
        print("TC-04 resync markers FOUND (manual confirm before MEASURED claim):")
        for label, line in result.hits[:40]:
            print(f"  [{label}] {line[:200]}")
        if len(result.hits) > 40:
            print(f"  ... and {len(result.hits) - 40} more")
        return 0
    print("TC-04 resync markers NOT found in scanned inputs (PARTIAL — may need forced AUTS replay)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
