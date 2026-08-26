"""
MOCK: educational CDR JSON model.
Production equivalent: TAP3 / BCE roaming settlement records (GSMA TD.57).
per lab policy V20 — NEVER claim TAP3 BER conformance.
Divergences: JSON fields only; RAP-style reject is a lab enum, not ASN.1 RAP.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import json


@dataclass
class LabCdr:
    record_id: str
    imsi: str
    tadig_serving: str
    tadig_home: str
    volume_bytes: int
    sequence: int


def to_json(cdr: LabCdr) -> str:
    return json.dumps(asdict(cdr), indent=2)


def reconcile(home_records: list[LabCdr], visited_records: list[LabCdr]) -> dict[str, Any]:
    """C9-style reconciliation: missing/orphan/duplicate/field mismatch (educational)."""
    h = {r.record_id: r for r in home_records}
    v = {r.record_id: r for r in visited_records}
    missing = sorted(set(h) - set(v))
    orphan = sorted(set(v) - set(h))
    mismatched = []
    for rid in set(h) & set(v):
        if h[rid].volume_bytes != v[rid].volume_bytes:
            mismatched.append(rid)
    seqs = [r.sequence for r in visited_records]
    gaps = [i for i in range(min(seqs), max(seqs) + 1) if i not in seqs] if seqs else []
    return {
        "missing_at_visited": missing,
        "orphan_at_visited": orphan,
        "field_mismatched": mismatched,
        "sequence_gaps": gaps,
        "conformance": "NOT_TAP3_BER",
    }


class RapRejectCode(str):
    """LAB RAP-style reject codes — not GSMA RAP ASN.1."""

    DUPLICATE = "LAB_RAP_DUPLICATE"
    SEQ_GAP = "LAB_RAP_SEQ_GAP"
    FIELD_MISMATCH = "LAB_RAP_FIELD_MISMATCH"
