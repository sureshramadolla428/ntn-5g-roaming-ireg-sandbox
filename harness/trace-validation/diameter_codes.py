"""Diameter result codes with verification flags.

Never treat UNVERIFIED values as authoritative pass/fail oracles.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DiameterCode:
    code: int
    name: str
    verified: bool
    citation: Optional[str]
    note: str = ""


# Base protocol (RFC 6733) — widely cited; still mark carefully
DIAMETER_SUCCESS = DiameterCode(2001, "DIAMETER_SUCCESS", True, "RFC 6733", "Base success")
DIAMETER_UNABLE_TO_DELIVER = DiameterCode(3002, "DIAMETER_UNABLE_TO_DELIVER", True, "RFC 6733")
DIAMETER_REALM_NOT_SERVED = DiameterCode(3003, "DIAMETER_REALM_NOT_SERVED", True, "RFC 6733")

# 3GPP Experimental — UNVERIFIED until TS 29.272 read (V1/V2)
EXPERIMENTAL_USER_UNKNOWN = DiameterCode(
    5001, "DIAMETER_ERROR_USER_UNKNOWN", False, "TS 29.272 UNVERIFIED (V2)", "Do not assert without citation"
)
# V1: 5004 vs 5420 naming unresolved
EXPERIMENTAL_ROAMING_NOT_ALLOWED = DiameterCode(
    5004, "DIAMETER_ERROR_ROAMING_NOT_ALLOWED", False, "TS 29.272 UNVERIFIED (V1)",
    "Confirm exact name/code before using in auth negative tests",
)
EXPERIMENTAL_UNKNOWN_EPS_SUBSCRIPTION = DiameterCode(
    5420, "DIAMETER_ERROR_UNKNOWN_EPS_SUBSCRIPTION", False, "TS 29.272 UNVERIFIED (V1)",
)

# SGd / TS 29.338 — UNVERIFIED (V3)
SGD_ABSENT_USER = DiameterCode(5550, "ABSENT_USER_PLACEHOLDER", False, "TS 29.338 UNVERIFIED (V3)")
SGD_USER_BUSY = DiameterCode(5551, "USER_BUSY_PLACEHOLDER", False, "TS 29.338 UNVERIFIED (V3)")


def require_verified(code: DiameterCode) -> None:
    if not code.verified:
        raise AssertionError(f"Refusing to use UNVERIFIED Diameter code {code.code} ({code.name})")
