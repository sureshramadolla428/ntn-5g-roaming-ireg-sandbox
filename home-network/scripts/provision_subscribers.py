#!/usr/bin/env python3
"""Provision lab subscribers into Open5GS Mongo (Ubuntu / live stack)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "subscribers" / "provision.json"


def main() -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    print(f"Would provision {len(data['imsis'])} IMSIs with lab K/OPc into Mongo.")
    print("DEFERRED-TO-UBUNTU: requires pymongo against home-mongo 10.10.1.20")
    print("PASS criteria: WebUI lists IMSI 001010000000001..020; auth vectors obtainable.")
    if "--dry-run" in sys.argv or True:
        for imsi in data["imsis"][:3]:
            print(f"  dry-run {imsi}")
        print(f"  ... ({len(data['imsis'])} total)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
