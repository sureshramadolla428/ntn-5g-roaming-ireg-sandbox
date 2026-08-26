"""Streamlit dashboard — every metric cites C8/C9/D3/D4."""
from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "harness" / "reports"

st.set_page_config(page_title="NTN Roaming Lab Gate", layout="wide")
st.title("NTN Roaming IREG Gate Dashboard")
st.caption("Educational lab metrics — not production market readiness.")

col1, col2, col3, col4 = st.columns(4)
# Placeholder numbers until reports exist
passed, executed = 0, 0
if REPORTS.exists():
    for p in REPORTS.glob("*.json"):
        data = json.loads(p.read_text(encoding="utf-8"))
        passed += int(data.get("passed", 0))
        executed += int(data.get("executed", 0))

rate = (passed / executed) if executed else 0.0
col1.metric("Pass rate (C8)", f"{rate:.1%}", help="C8: passed/executed")
col2.metric("Automation coverage (D4.2)", "n/a", help="D4.2 = automated/total × 100")
col3.metric("Flake rate (D4.4)", "n/a", help="D4.4 inconsistent/executed × 100")
col4.metric("Signalling success (D3)", "n/a", help="D3 successes/attempts")

st.subheader("Billing reconciliation (C9)")
st.write("Missing / orphan / duplicate / field-mismatch counts from mocks/billing — educational JSON only (V20).")

st.subheader("Fault domains")
st.write("HOME / IPX / VISITED / INDETERMINATE from harness.trace-validation.fault_domain")
