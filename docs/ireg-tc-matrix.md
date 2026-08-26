# Interview IREG TC matrix (TC-01 … TC-25)

**Purpose:** Map the user’s 25 interview TCs to lab artifacts, honest readiness, capture points, and checkable pass/fail.  
**Do not invent** AVPs/codes beyond user citations or already-flagged lab registries (`diameter_codes.py`, verification-register).  
**GSMA IR.24/IR.25/IR.88/NG.113** contents are member-restricted — suite *structure* is modelled; do not claim document conformance.

**Last updated:** 2026-08-26 (TC-05 LBO MEASURED `20260826T014834`)  
**Related:** `docs/runbooks/ireg-tc-execution.md`, `scripts/capture-ireg-tc.sh`, `scripts/run-ireg-tc.sh`, `harness/testcases/test_lab_ireg_*.py`, `docs/evidence/`

## Status legend

| Status | Meaning |
|--------|---------|
| **READY-LIVE** | Runnable on Ubuntu with current stacks; capture recipe exists; may already be MEASURED once |
| **PARTIAL** | Some steps/evidence possible; architecture or RAT incomplete |
| **MOCK-ONLY** | Mock/compose present; not production SGd/MAP/SCEF/TAP |
| **DEFERRED-TO-UBUNTU** | Needs component build/bring-up not done yet (LTE EPC, OAI, live Osmocom) |
| **BLOCKED** | Structural lab limit (document why) |

## Summary counts (interview gate)

| Status | Count | TCs |
|--------|------:|-----|
| READY-LIVE | 1 | TC-05 |
| RUNNABLE (script + capture) | 6 | TC-03, TC-06, TC-11, TC-16, TC-04, TC-15 |
| PARTIAL (manual confirm / architecture gap) | 0 | — (merged into RUNNABLE rows above where scripted) |
| MOCK-RUNNABLE | 8 | TC-07, TC-08, TC-09, TC-10, TC-12, TC-13, TC-20, TC-21 |
| DEFERRED-TO-UBUNTU | 9 | TC-01, TC-02, TC-14, TC-17, TC-18, TC-22, TC-23, TC-24, TC-25 |
| BLOCKED | 1 | TC-19 (SoR / VPLMN camp DEF-0014); TC-25 also gated on priors |

**Executable today for interview evidence:** TC-05 golden → `run-ireg-tc.sh TC-11` → negatives TC-03/06/16 → mocks TC-07/09/12/13/20 → TC-21 netem (REFERENCE) → TC-15 HR attempt (not claimed until 10.45.x MEASURED).

---

## Already MEASURED on Ubuntu (do not re-claim as new)

| Observation | Label |
|-------------|--------|
| Dual Open5GS home/visited + IPX Up; dual-home on `ntn-ipx-net`; single NRF client | MEASURED |
| B1 attach: SUCI `001-01`, Registration complete, PDU session, `uesimtun0` **10.46.0.5**, ping UPF GW **10.46.0.1** OK | MEASURED (earlier LBO-style run) |
| **2026-08-26 LBO MEASURED** `LAB-IREG-001/20260826T014834`: Reg+PDU OK; TUN **`10.46.0.3`**; GW ping **10.46.0.1** 3/3; Grafana ~87% / Auth·Reg·PDU success 100%; HOME=0 OK. Evidence: [`docs/evidence/TC-05-20260826T014834-LBO-MEASURED.md`](evidence/TC-05-20260826T014834-LBO-MEASURED.md). **Demo snaps** (Wireshark W1–W8 + Grafana G1–G7): [`docs/evidence/TC-05-20260826T014834-DEMO-SNAPS.md`](evidence/TC-05-20260826T014834-DEMO-SNAPS.md). Related: `20260826T014053` (**10.46.0.2**) | **MEASURED PASS (LBO)** |
| **2026-08-26 SUPERSEDED** `TC-05/20260826T010742`: UE **`10.45.0.3`** (HR-style) — PARTIAL. [`docs/evidence/TC-05-20260826T010742.md`](evidence/TC-05-20260826T010742.md) | SUPERSEDED / PARTIAL |
| Ping `8.8.8.8` fail (no NAT/default route on UPF) | MEASURED gap (earlier); **this** run’s UE log showed ping replies — do not overwrite without pcap confirmation |
| Stock UERANSIM cannot camp VPLMN **999/70** with home SUCI without patches | MEASURED / DEF-0014 |

**User-plane note:** Lab pools **10.46.0.0/16** = visited LBO (TC-05 default `ROAMING_MODE=LBO`); **10.45.0.0/16** = HR target (TC-15). Run **20260826T014834** = **LBO MEASURED** (`10.46.0.3`). Run **20260826T010742** (`10.45.0.3`) is **SUPERSEDED** historical PARTIAL (then-default HR + UPF desync).

**SEPP/N32:** Absent (V14). Lab uses dual-home + SBI proxy stand-in — **not** real N32.

---

## Category A — Registration & Authentication

### TC-01 — LTE Initial Attach with S6a Authentication (Positive)

| Field | Value |
|-------|--------|
| **Refs (user)** | TS 23.401 §5.3.2; TS 29.272 AIR/AIA; GSMA IR.24/IR.25 (structure only) |
| **Lab artifact** | `home-hss` in `home-network/docker-compose.yml`; Diameter DRA `ipx/`; **no visited MME/SGW compose** |
| **Harness** | LAB-IREG-003/005 offline Diameter/realm; no live S6a attach case |
| **Status** | **DEFERRED-TO-UBUNTU** — full LTE EPC (MME/SGW-C/U) not brought up; HSS/DRA only |
| **Capture** | When EPC exists: S6a on HSS `10.10.1.14:3868`, DRA `10.10.3.10`, MME (planned `10.10.2.14`) |
| **Pass/fail in lab** | Not checkable E2E today. Offline: `pytest -k LAB-IREG-003` (success code 2001 RFC 6733 only) |

### TC-02 — S6a Update Location / ULA profile

| Field | Value |
|-------|--------|
| **Refs** | TS 29.272 §7.2.3/§7.3; TS 23.008 |
| **Lab artifact** | Subscribers `home-network/subscribers/lab-subscribers.ndjson`; HSS |
| **Status** | **DEFERRED-TO-UBUNTU** (needs TC-01 path) |
| **Pass/fail** | Compare ULA AVPs to provisioned slice/APN — requires live ULA pcap |

### TC-03 — Authentication Failure — Invalid Key (Negative)

| Field | Value |
|-------|--------|
| **Refs** | TS 24.301 §5.4.2 cause #20; TS 33.401 (LTE). 5G analogous: failed 5G-AKA |
| **Lab artifact** | `ran/ueransim/ue-home-roamer-wrong-key.yaml` (UE K ≠ Mongo); harness marker LAB-IREG / TC-03 |
| **Status** | **RUNNABLE** — `scripts/run-tc-03-wrong-key.sh`; 5G B1 wrong-key attach; LTE S6a **DEFERRED** |
| **Capture** | `bash scripts/run-ireg-tc.sh TC-03 --with-capture` or `ATTACH_MODE=tc03-wrong-key` |
| **Pass/fail** | Auth fail + no lasting PDU; **do not** assert Diameter experimental codes without V1/V2 citation |
| **Divergence** | User TC is LTE MAC failure; lab primary path is 5G-AKA |

### TC-04 — SQN Resynchronization (Synch Failure Recovery)

| Field | Value |
|-------|--------|
| **Refs** | TS 33.102 §6.3.5; TS 29.272 AIR Re-Synchronization-Info |
| **Lab artifact** | Home AUSF/UDM/UDR; B1 attach path; SQN in Mongo subscriber |
| **Status** | **RUNNABLE** — `scripts/run-tc-04-sqn-resync.sh` + `harness/trace-validation/sqn_resync.py`; re-run + pcap for MEASURED claim |
| **Capture** | `bash scripts/run-ireg-tc.sh TC-04 --with-capture [--attach]` |
| **Pass/fail** | One resync then success; fail on resync loop — **manual** log/pcap check |

### TC-05 — 5G SA Registration from VPLMN (SUCI / 5G-AKA) — GOLDEN PATH

| Field | Value |
|-------|--------|
| **Refs** | TS 23.502 §4.2.2; TS 33.501 §6.1; GSMA NG.113 (structure) · **Spec:** [`docs/specs/TC-05-spec.md`](specs/TC-05-spec.md) |
| **Lab artifact** | `scripts/live-first-attach.sh`, `ran/ueransim/ue-home-roamer.yaml`, `gnb-home-plmn-auth.yaml`; LAB-IREG-001 |
| **Status** | **READY-LIVE** — **MEASURED PASS (LBO)** on `20260826T014834` (UE **10.46.0.3**, GW ping OK) |
| **Architecture honesty** | B1 = same-PLMN camp **001/01** on visited AMF with home SUCI auth via ipx-net. **Not** true VPLMN **999/70** camp (BLOCKED without UERANSIM patches — DEF-0014). **No SEPP** — dual-home stand-in (V14). HOME Grafana tile **0** OK (IPX counts home SBI). HR PDU steps PARTIAL/N/A. DN **8.8.8.8** not claimed |
| **Capture** | `bash scripts/capture-ireg-tc.sh TC-05` then `KEEP_UE=1 sudo -E bash scripts/live-first-attach.sh` (or `scripts/run-tc-05-golden.sh`) |
| **Evidence (2026-08-26)** | **Primary:** [`docs/evidence/TC-05-20260826T014834-LBO-MEASURED.md`](evidence/TC-05-20260826T014834-LBO-MEASURED.md) (`LAB-IREG-001/20260826T014834`, UE **10.46.0.3**). **Demo snaps:** [`TC-05-20260826T014834-DEMO-SNAPS.md`](evidence/TC-05-20260826T014834-DEMO-SNAPS.md). Related LBO: `20260826T014053` (**10.46.0.2**). **SUPERSEDED:** [`TC-05-20260826T010742.md`](evidence/TC-05-20260826T010742.md) (**10.45.0.3**) |
| **NF logs** | `visited-amf`, `visited-scp`, `visited-nrf`, `home-ausf`, `home-udm`, `home-udr`, `home-pcf` |
| **Pass/fail** | SUCI `suci-0-001-01-…-0000000001`; Registration Accept / MM-REGISTERED; AUSF/UDM 2xx; no plaintext SUPI on air (protectionScheme lab may be 0 — note in NOTES.md). Golden **PASS** also requires UE **10.46.x** per `docs/specs/TC-05-spec.md` |

### TC-06 — Roaming Not Allowed — Barred Subscriber (Negative)

| Field | Value |
|-------|--------|
| **Refs** | User cites TS 29.272 `DIAMETER_ERROR_ROAMING_NOT_ALLOWED` **5004** (lab **V1 UNVERIFIED**); TS 24.301/24.501 cause **#11** |
| **Lab artifact** | Stub recipe in runbook; `home-network/subscribers/lab-subscribers-tc06-barred.ndjson` (marker only); `diameter_codes.EXPERIMENTAL_ROAMING_NOT_ALLOWED` gated |
| **Status** | **RUNNABLE** — `scripts/run-tc-06-barred.sh` toggles AMF `access_control` (5G #11 stand-in); **5004 V1 UNVERIFIED** |
| **Pass/fail** | Reject with documented cause; no attach storm — manual |

---

## Category B — SMS (SGd / MAP)

### TC-07 — MT-SMS over SGd

| Field | Value |
|-------|--------|
| **Refs** | TS 29.338 TFR/TFA; TS 23.272 §8; TS 23.040; GSMA NG.111 considerations |
| **Lab artifact** | `mocks/sgd-smsc/` (**MOCK**); LAB-IREG-015/017 |
| **Status** | **MOCK-ONLY** — framing ACK `MOCK-SGD-ACK`; not live NAS SMS |
| **Capture** | `make up-mocks` + `capture-ireg-tc.sh TC-07` (mocks-net `10.10.6.11:3868`) |
| **Pass/fail** | Mock health / harness offline only |

### TC-08 — MO-SMS over SGd

| Field | Value |
|-------|--------|
| **Same as TC-07** | **MOCK-ONLY**; LAB-IREG-018 |

### TC-09 — MT-SMS Retry / Alert-SC (PSM)

| Field | Value |
|-------|--------|
| **Refs** | TS 29.338 §5.3; TS 23.682 |
| **Status** | **MOCK-RUNNABLE** — Alert-SC/PSM HTTP sidecar on SGd mock `:8081`; `scripts/run-tc-09-alert-sc.sh` |

### TC-10 — Legacy MAP SMS (SRI-SM)

| Field | Value |
|-------|--------|
| **Refs** | TS 29.002; GSMA IR.21 GT ranges |
| **Lab artifact** | `mocks/map-sri-sm/` TCP stub @ `10.10.6.12:2906`; Osmocom templates in `ss7-map/` |
| **Status** | **MOCK-RUNNABLE** — ASCII SRI-SM stub + optional `make up-ss7`; `scripts/run-tc-10-map-sri-sm.sh` |

---

## Category C — Data / PDU / NIDD

### TC-11 — E2E IP Data Path (default bearer / PDU)

| Field | Value |
|-------|--------|
| **Refs** | TS 23.401 §5.3.1; GSMA IR.25 data; IR.33/IR.34 |
| **Lab artifact** | B1 PDU + `uesimtun0`; visited UPF `10.10.2.13`; LAB-IREG-006/007 |
| **Status** | **RUNNABLE** — `scripts/run-tc-11-userplane.sh`; MEASURED GW **10.46.0.1** OK; DN **8.8.8.8** fail |
| **Capture** | `bash scripts/run-ireg-tc.sh TC-11 --with-capture` |
| **Pass/fail** | TUN up; ping GW; label HR vs LBO honestly |

### TC-12 — MO NIDD via SCEF (T6a)

| Field | Value |
|-------|--------|
| **Refs** | TS 23.682 §5.13; TS 29.128; TS 24.301 CIoT |
| **Lab artifact** | `mocks/scef/` T8 HTTP mock (**not T6a**); V11/V12 UNVERIFIED; LAB-IREG-019/020 |
| **Status** | **MOCK-RUNNABLE** — `scripts/run-tc-12-mock-scef.sh` |
| **Pass/fail** | HTTP mock accept/size boundary only |

### TC-13 — MT NIDD buffering (PSM)

| Field | Value |
|-------|--------|
| **Status** | **MOCK-RUNNABLE** — SCEF `mt-buffer` API + `scripts/run-tc-13-nidd-buffer.sh` |

### TC-14 — PSM / eDRX timer negotiation

| Field | Value |
|-------|--------|
| **Refs** | TS 24.301 §9.9.3; TS 23.682; GSMA TS.34 |
| **Status** | **DEFERRED-TO-UBUNTU** — no LTE IoT UE / timer negotiation harness |

### TC-15 — 5G SA Home-Routed PDU

| Field | Value |
|-------|--------|
| **Refs** | TS 23.502 §4.3.2.2.2; GSMA NG.113 §5 |
| **Lab artifact** | `visited-network/configs/variants/smf-hr.yaml` (10.45); `smf-lbo.yaml` (10.46); compose `ROAMING_MODE`; home SMF/UPF |
| **Status** | **RUNNABLE (attempt)** — `smf_init.sh` wires `ROAMING_MODE`; `scripts/run-tc-15-hr.sh`. Historical UE **`10.45.0.3`** on superseded TC-05 `20260826T010742` — **address alone ≠ full HR**; still need N16/N9 + hUPF. Current golden is **LBO 10.46** (`20260826T014834`) |
| **Pass/fail** | HR claim requires UE IP from **10.45** pool **and** user plane via home UPF / HR signaling — path **not** fully MEASURED (V25). See superseded [`TC-05-20260826T010742.md`](evidence/TC-05-20260826T010742.md); LBO evidence [`TC-05-20260826T014834-LBO-MEASURED.md`](evidence/TC-05-20260826T014834-LBO-MEASURED.md) |

### TC-16 — Unknown/Unsubscribed DNN (Negative)

| Field | Value |
|-------|--------|
| **Refs** | TS 24.301 ESM #27; TS 24.501 5GSM #27 |
| **Lab artifact** | Recipe: set UE session DNN ≠ `internet` in a copy of UE YAML; runbook |
| **Status** | **RUNNABLE** — `scripts/run-tc-16-unknown-dnn.sh`; cause from live logs only |

---

## Category D — Mobility / Security / Charging

### TC-17 — TAU periodic / mobility

| Field | Value |
|-------|--------|
| **Status** | **DEFERRED-TO-UBUNTU** — no multi-TA LTE; 5G mobility Registration Update not instrumented |

### TC-18 — Detach / Cancel Location (CLR)

| Field | Value |
|-------|--------|
| **Status** | **DEFERRED** for S6a CLR; 5G deregister **PARTIAL** (manual UE stop + AMF logs) |

### TC-19 — Network selection / SoR

| Field | Value |
|-------|--------|
| **Status** | **BLOCKED** / **DEFERRED** — stock UERANSIM no preferred-PLMN / SoR (DEF-0014 / V23) |

### TC-20 — Roaming charging / TAP correlation

| Field | Value |
|-------|--------|
| **Refs** | TS 32.251/32.298; GSMA TD.57 (lab V20 educational JSON only) |
| **Lab artifact** | `mocks/billing/`; LAB-IREG-022/023 |
| **Status** | **MOCK-RUNNABLE** — `scripts/run-tc-20-mock-billing.sh` |

---

## Category E — NTN custom

### TC-21 — Attach under NTN latency / extended timers

| Field | Value |
|-------|--------|
| **Refs** | TS 24.301/24.501 NTN timers Rel-17; TS 38.300 §16.14; GSMA NG.129 considerations |
| **Lab artifact** | `ran/oai/netem/`; LAB-IREG-NTN-001/024; `docs/ntn-test-rationale.md` |
| **Status** | **MOCK-RUNNABLE (netem)** / **DEFERRED (OAI RAN)** — `scripts/run-tc-21-ntn-netem.sh` applies REFERENCE delays; OAI @ `38dc378` not built |

### TC-22 — MT-SMS discontinuous coverage

| Field | Value |
|-------|--------|
| **Status** | **DEFERRED** / depends on MOCK SMS + coverage simulation |

### TC-23 — NIDD × PSM × coverage

| Field | Value |
|-------|--------|
| **Status** | **DEFERRED** / MOCK SCEF only |

### TC-24 — Moving-cell TA / Registration storms

| Field | Value |
|-------|--------|
| **Status** | **DEFERRED-TO-UBUNTU** — needs OAI NTN TA sweep |

### TC-25 — E2E regression under combined impairments

| Field | Value |
|-------|--------|
| **Status** | **BLOCKED** until TC-01…24 individually pass (user gate); harness flake/signoff only offline today |

---

## LAB-IREG ↔ User TC crosswalk (approximate)

| User TC | Closest LAB-IREG / script |
|---------|---------------------------|
| Topology guard | LAB-IREG-000 |
| TC-05 | LAB-IREG-001 + `run-tc-05-golden.sh` |
| TC-03 | `run-tc-03-wrong-key.sh` |
| TC-04 | `run-tc-04-sqn-resync.sh` + `sqn_resync.py` |
| TC-06 | `run-tc-06-barred.sh` |
| TC-07/08 | `run-tc-07-mock-sgd.sh` |
| TC-09 | `run-tc-09-alert-sc.sh` + SGd HTTP :8081 |
| TC-10 | `run-tc-10-map-sri-sm.sh` |
| TC-11 | LAB-IREG-007 + `run-tc-11-userplane.sh` |
| TC-12 | `run-tc-12-mock-scef.sh` |
| TC-13 | `run-tc-13-nidd-buffer.sh` |
| TC-15 | `run-tc-15-hr.sh` + `smf_init.sh` ROAMING_MODE |
| TC-16 | `run-tc-16-unknown-dnn.sh` |
| TC-20 | `run-tc-20-mock-billing.sh` |
| TC-21 | `run-tc-21-ntn-netem.sh` |
| All | `scripts/run-ireg-tc.sh TC-XX` |
| Auth codes / realm | LAB-IREG-003, 004, 005 |
| IPX fault | LAB-IREG-008…014 |
| SMS | LAB-IREG-015…018 |
| NIDD | LAB-IREG-019, 020 |
| Billing | LAB-IREG-022, 023 |
| NTN | LAB-IREG-024, 025, LAB-IREG-NTN-* |

---

## Capture directory convention

```
pcaps/TC-XX/<timestamp>/
  ran-net.pcap | visited-net.pcap | home-net.pcap | ipx-net.pcap | multi-point.pcap
  docker-logs/*.log
  NOTES.md          # pass/fail, MEASURED vs REFERENCE, architecture (B1/LBO/HR)
```

Also keep legacy `pcaps/LAB-IREG-001/<ts>/` from `live-first-attach.sh`.
