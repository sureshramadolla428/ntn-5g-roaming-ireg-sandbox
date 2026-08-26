# Phase status & START HERE (Skylo IREG / Network Test Engineer narrative)

**Last updated:** 2026-08-24  
**Writable lab:** `~/ntn-roaming-lab`  
**Read-only refs:** `~/reference/`  
**Live runtime:** Ubuntu 22.04 VM (SCTP + Docker)

**Interview TC suite:** [`docs/ireg-tc-matrix.md`](ireg-tc-matrix.md) (TC-01…TC-25)  
**Execution runbook:** [`docs/runbooks/ireg-tc-execution.md`](runbooks/ireg-tc-execution.md)  
**Capture:** `scripts/capture-ireg-tc.sh` / `scripts/run-tc-05-golden.sh`

---

## Executive summary

| Layer | Status |
|-------|--------|
| **Scaffold (Windows → portable repo)** | **DONE** — phases -1…14 artifacts, offline tests pass |
| **Ubuntu VM prep** | **DONE** — SCTP, venv, Docker, lab + references copied |
| **Live Docker stacks** | **MEASURED Up** — dual Open5GS home/visited + IPX; dual-home on ipx-net; single NRF client |
| **Live roaming attach (B1)** | **MEASURED** — SUCI 001-01, Registration complete, PDU, `uesimtun0` 10.46.0.5, ping GW 10.46.0.1 OK; DN 8.8.8.8 fail (no NAT) |
| **True VPLMN 999/70 camp** | **BLOCKED** without UERANSIM patches (DEF-0014) — B1 is same-PLMN camp |
| **Interview IREG TC-01…25** | **Matrix READY** — 1 READY-LIVE (TC-05), 6 PARTIAL, 7 MOCK-ONLY, 10 DEFERRED |
| **NTN Tier-2 (OAI)** | **PENDING** — clone @ `38dc378` |
| **Interview-ready demo** | **PARTIAL** — golden TC-05 + capture; LTE/SMS/NTN staged honestly |

---

## Architecture (target)

```
HOME 001-01          IPX (DRA + SBI proxy)          VISITED 999-70
UDM/HSS/AUSF/…  ◄────────────────────────────►  AMF/SMF/UPF
                         │
                  UERANSIM Tier-1  |  OAI RFSIM Tier-2 (NTN)
```

**Fault domains:** HOME | IPX | VISITED | RAN/UE | NTN impairment (netem)

**Live attach track:** B1 same-PLMN gNB `001/01` + home SUCI via visited AMF (not SEPP/N32).

---

## Phase matrix

| Phase | Deliverable | Offline | Live Ubuntu |
|-------|-------------|---------|-------------|
| -1 | Reference inventory, verification register | DONE | N/A |
| 0 | `network-plan.yaml`, `make check-network` | PASS | PASS |
| 1 | Dual Open5GS HOME/VISITED, HR/LBO configs | DONE | **MEASURED Up** (user plane LBO 10.46; HR not proven) |
| 2 | IPX DRA, SBI proxy, fault API | DONE | **MEASURED Up** (DRA peer depth varies) |
| 3 | OAI NTN configs, netem B4 | DONE | **PENDING** OAI build |
| 4 | Osmocom SS7 stubs | DONE | optional `make up-ss7` UNVERIFIED |
| 5–6 | SGd, SCEF mocks | DONE (mock) | `make up-mocks` — not live NAS SMS |
| 7 | IR.21 YAML/XSD + validators | DONE | N/A |
| 8 | Billing reconcile (JSON model) | DONE | MOCK-ONLY |
| 9 | pytest LAB-IREG-* + user TC matrix | offline + matrix tests | **TC-05 LIVE path documented** |
| 10 | CI (GitHub Actions) | DONE | Hosted SCTP limited (V17) |
| 11 | Streamlit/Grafana | DONE (scaffold) | **PENDING** live scrape |
| 12 | Docs, limitations, demo script | DONE | + IREG matrix/runbook |
| 13 | IMSI trace, Jira CSV | DONE (tool) | **PENDING** multi-point logs archive |
| 14 | NTN suite + rationale | DONE (artifacts) | **PENDING** MEASURED RTT |

---

## Validation type legend

| Label | Meaning |
|-------|---------|
| **DONE (offline)** | Code/config/tests pass without live network |
| **PASS (live) / MEASURED** | Verified on Ubuntu with traces |
| **PENDING** | Not yet run on live stack |
| **UNVERIFIED** | In Appendix E; do not assert in tests |
| **MOCK** | Stand-in; divergence documented |

---

## Job requirement → artifact map (interview)

| Skylo-style need | Lab proof |
|------------------|-----------|
| IREG onboarding gate | `docs/ireg-tc-matrix.md`, `harness/testcases/LAB-IREG-*`, `docs/test-strategy.md` |
| Multi-domain fault isolation | `harness/trace-validation/fault_domain.py` |
| 5G SA roaming HR/LBO | Phase 1 configs; **MEASURED B1/LBO**; HR PARTIAL (`variants/README.md`) |
| 4G / SS7 / MAP | Phase 4 Osmocom — DEFERRED live; HSS present |
| Diameter / IPX | Phase 2 IPX, freeDiameter DRA |
| NTN delay / timers | Phase 3/14, netem B3/B4, LAB-IREG-NTN-* |
| Automation + CI | pytest + `ci/`, `make test-fast` |
| Metrics / portfolio | `dashboard/`, C8/D3/D4 formulas |
| IR.21 / partner profiles | `ir21/` |
| Defect → regression | `docs/defect-log.md`, `make defect-coverage` |
| Limitations honesty | `docs/limitations.md` |

---

## START HERE — ordered checklist (Ubuntu VM)

### A. Sync → CRLF fix → verify stacks (if already Up, skip recreate)

```bash
sudo mkdir -p /mnt/hgfs
sudo vmhgfs-fuse .host:/ /mnt/hgfs -o allow_other 2>/dev/null || true
cd ~/ntn-roaming-lab && source .venv/bin/activate
rsync -av --exclude '.venv' --exclude '__pycache__' --exclude '.git' \
  /mnt/hgfs/MVNOs_and_MNOs/ntn-roaming-lab/ ~/ntn-roaming-lab/
python3 scripts/fix_crlf.py
chmod +x scripts/*.sh
sg docker -c "bash -lc 'cd ~/ntn-roaming-lab && source .venv/bin/activate && make verify-live'"
docker ps
```

First-time / recreate:

```bash
sg docker -c 'cd ~/ntn-roaming-lab && bash scripts/ubuntu-sg-bootstrap.sh'
```

### B. If docker permission denied

**Do not** paste `newgrp docker` then more commands. Use:

```bash
sg docker -c 'cd ~/ntn-roaming-lab && bash scripts/ubuntu-sg-bootstrap.sh'
```

### C. Golden interview path — TC-05 capture + B1 attach

```bash
export UERANSIM_BIN=~/UERANSIM/build
sg docker -c 'cd ~/ntn-roaming-lab && bash scripts/capture-ireg-tc.sh TC-05'
sudo -E bash scripts/run-tc-05-golden.sh
# ping GW (TC-11 partial):
ping -I uesimtun0 10.46.0.1 -c 3
bash scripts/capture-ireg-tc.sh TC-05 --stop
```

Details: [`ireg-tc-execution.md`](runbooks/ireg-tc-execution.md), [`live-first-attach.md`](runbooks/live-first-attach.md).

### D. Expand regression

```bash
make test-fast          # offline tier1 + user TC matrix scaffolding
NTN_LIVE_NET=1 pytest -k LAB-IREG-000 -v   # when stacks up
make report
```

### E. NTN Tier-2 (later)

Clone OAI @ `38dc378`, overlay `ran/oai/configs/`, run LAB-IREG-024/025 with **MEASURED** ping RTT.

---

## Known gaps (do not over-claim)

- **SEPP / N32:** SBI **proxy stand-in** only (V14 VERIFIED-ABSENT)
- **TAP3 BER:** JSON educational model only (V20)
- **GSMA IREG docs:** structure modelled; member specs not read
- **~20 Appendix E items:** still UNVERIFIED
- **4G LTE full stack:** DEFERRED; 5G SA is primary path
- **HR PDU:** `ROAMING_MODE` not wired to variants; MEASURED pool is **10.46 LBO**
- **No UPF NAT:** DN ping fail is expected until NAT/routing added
- **UERANSIM HPLMN limit:** DEF-0014 / V23

---

## Repository structure (confirmed)

```
ntn-roaming-lab/
├── network-plan.yaml          # IP/port SSOT
├── home-network/              # PLMN 001-01
├── visited-network/           # PLMN 999-70
├── ipx/                       # DRA + SBI proxy + fault API
├── ran/ueransim/              # Tier-1 RAN configs
├── ran/oai/                   # Tier-2 NTN configs
├── harness/                   # pytest + trace validation
├── mocks/                     # SGd, SCEF, billing
├── ir21/                      # partner profiles
├── scripts/                   # bootstrap, provision, capture-ireg-tc
├── docs/                      # ireg-tc-matrix, runbooks, limitations
└── pcaps/                     # MEASURED captures (Ubuntu only) TC-XX/ or LAB-IREG-*
```

---

## What to tell an interviewer

1. **Built** a portable three-domain roaming lab from existing reference configs without mutating originals.
2. **Separated** offline scaffold validation from live trace validation; **MEASURED** B1 5G registration + PDU + GW ping.
3. **Mapped** 25 interview TCs to READY / PARTIAL / MOCK / DEFERRED with capture recipes.
4. **Documented** limitations (no SEPP, no real TAP3, UERANSIM VPLMN camp blocked, LBO vs HR honesty).
5. **Next:** archive TC-05/TC-11 pcaps → TC-03 negative → mocks SMS/NIDD → OAI NTN.
