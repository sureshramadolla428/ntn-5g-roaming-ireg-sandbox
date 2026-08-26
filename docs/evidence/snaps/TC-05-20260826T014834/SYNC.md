# SYNC status — TC-05 run `20260826T014834`

**Run id:** `TC-05-20260826T014834`  
**Pcap:** `pcaps/LAB-IREG-001/20260826T014834/multi-point.pcap` (+ `nr-ue.log`)  
**Verdict claim:** MEASURED PASS (LBO) — see [`../../TC-05-20260826T014834-LBO-MEASURED.md`](../../TC-05-20260826T014834-LBO-MEASURED.md)

## Sync matrix (this pack only)

| Artifact | Same run id? | Status |
|----------|--------------|--------|
| W1–W8 Wireshark PNGs | YES — frames from this `multi-point.pcap` | **SYNCED** |
| W9 PFCP | N/A — `tshark -Y pfcp` = **0** on this pcap | **NOT CLAIMED** (do not invent) |
| G-health-offline.json | YES — exporter parse of same dir | **SYNCED (offline)** |
| G1–G7 Grafana GUI PNGs | — | **PENDING** — operator after Ubuntu `KEEP_FLOW_METRICS=1` refresh of **this** `PCAP_DIR` |

**Exporter offline (Windows 2026-08-26, post `-c` fix + nr-ue fallback):**  
`domains.ran=8`, observed≈18, backend=`tshark`. Gate `domains.ran > 0` with NGAP=13 **PASS**.

**Honesty:** B1 **001/01**; **no SEPP**; UE **10.46.0.3** LBO; not HR **10.45**; not DN 8.8.8.8.

**Do not mix** with `20260826T032417` (PFCP MEASURED on Ubuntu — separate pack) or SUPERSEDED `20260826T010742` (10.45).
