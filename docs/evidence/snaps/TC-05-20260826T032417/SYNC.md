# TC-05 snap pack — `20260826T032417` (PFCP MEASURED attach)

**Sync status: NOT SYNCED on this Windows tree**

## Why

- Ubuntu MEASURED: NGAP=13, NAS=9, PFCP=42, UE `10.46.0.2`, GW ping OK  
  ([`../../TC-05-20260826T032417-LBO-MEASURED.md`](../../TC-05-20260826T032417-LBO-MEASURED.md)).
- **Pcaps for this stamp are not present** under the Windows workspace (`pcaps/TC-05/20260826T032417/` missing).
- Pre-fix Grafana showed `domains.ran=0` due to exporter `tshark -c 1` bug — **do not** pair that Grafana state with W* from another run.

## Required before claiming SYNC

1. Rsync `pcaps/TC-05/20260826T032417/` (or LAB-IREG path) to this tree / Ubuntu `~/ntn-roaming-lab`.
2. Deploy fixed exporter (`no -c`, nr-ue fallback, compose bind-mount).
3. `chmod -R a+rX` + `PCAP_DIR=.../20260826T032417 bash scripts/refresh-flow-dashboard.sh TC-05`
4. Confirm `domains.ran > 0` and health `pcap_dir` ends with `20260826T032417`.
5. Capture W1–W9 from **that** run’s pcaps only (W9 PFCP allowed only if `tshark -Y pfcp` > 0).
6. Capture G1–G7 from Grafana after step 3.

**Honesty:** B1 001/01; no SEPP; LBO 10.46. Until steps 1–6 complete, **do not claim** W/G sync for 032417. Prefer documenting 014834 pack as the synced Wireshark demo.
