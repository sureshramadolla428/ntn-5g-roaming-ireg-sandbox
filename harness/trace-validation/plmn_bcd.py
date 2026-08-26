"""PLMN ID BCD encode/decode per TS 24.008 / E.212 (lab Appendix C1).

PLMN ID, 3 octets, nibble-swapped BCD; 2-digit MNC uses filler 0xF:
  Octet1 = MCC2<<4 | MCC1
  Octet2 = (MNC3 or 0xF)<<4 | MCC3
  Octet3 = MNC2<<4 | MNC1

Worked examples (must match unit tests; pcap byte assert = DEFERRED-TO-UBUNTU):
  HOME 001-01 → 00 F1 10
  VISITED 999-70 → 99 F9 07
"""
from __future__ import annotations


def encode_plmn_bcd(mcc: str, mnc: str) -> bytes:
    """Encode MCC/MNC to 3-octet PLMN ID (nibble-swapped BCD)."""
    if len(mcc) != 3 or not mcc.isdigit():
        raise ValueError(f"MCC must be 3 digits, got {mcc!r}")
    if len(mnc) not in (2, 3) or not mnc.isdigit():
        raise ValueError(f"MNC must be 2 or 3 digits, got {mnc!r}")
    mcc1, mcc2, mcc3 = (int(d) for d in mcc)
    if len(mnc) == 2:
        mnc1, mnc2 = (int(d) for d in mnc)
        mnc3 = 0xF
    else:
        mnc1, mnc2, mnc3 = (int(d) for d in mnc)
    octet1 = (mcc2 << 4) | mcc1
    octet2 = (mnc3 << 4) | mcc3
    octet3 = (mnc2 << 4) | mnc1
    return bytes((octet1, octet2, octet3))


def decode_plmn_bcd(raw: bytes) -> tuple[str, str]:
    """Decode 3-octet PLMN ID to (mcc, mnc) strings."""
    if len(raw) != 3:
        raise ValueError("PLMN BCD must be exactly 3 octets")
    o1, o2, o3 = raw
    mcc1 = o1 & 0x0F
    mcc2 = (o1 >> 4) & 0x0F
    mcc3 = o2 & 0x0F
    mnc3 = (o2 >> 4) & 0x0F
    mnc1 = o3 & 0x0F
    mnc2 = (o3 >> 4) & 0x0F
    mcc = f"{mcc1}{mcc2}{mcc3}"
    if mnc3 == 0xF:
        mnc = f"{mnc1}{mnc2}"
    else:
        mnc = f"{mnc1}{mnc2}{mnc3}"
    return mcc, mnc


def plmn_bcd_hex(mcc: str, mnc: str) -> str:
    """Return spaced hex like '00 F1 10' for docs/assertions."""
    return " ".join(f"{b:02X}" for b in encode_plmn_bcd(mcc, mnc))
