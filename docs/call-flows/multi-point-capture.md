# Multi-point capture design

Capture points for fault attribution:

1. **visited-edge** — NGAP/N1N2 + Diameter/SBI toward IPX
2. **ipx-ingress / ipx-egress** — both DRA legs (10.10.1.30 / 10.10.2.30)
3. **home-edge** — HSS/UDM facing IPX

Correlate by Diameter Session-Id / End-to-End ID (must match across IPX) and IMSI/SUPI.

Single-point capture is insufficient for `fault_domain()` — incomplete evidence → INDETERMINATE.
