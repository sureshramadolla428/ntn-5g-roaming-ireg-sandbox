# IREG TC execution runbook (interview suite TC-01…TC-25)

**Matrix:** [`docs/ireg-tc-matrix.md`](../ireg-tc-matrix.md)  
**Capture:** `scripts/capture-ireg-tc.sh`  
**Golden path:** TC-05 (5G SA B1) → TC-11 (GW ping) → next staged TCs below.

Labels: **MEASURED** only from Ubuntu pcaps/logs. Windows = scaffold only.

---

## 0. Ordered bring-up (Ubuntu)

```bash
# Sync from Windows share (adjust path)
sudo mkdir -p /mnt/hgfs
sudo vmhgfs-fuse .host:/ /mnt/hgfs -o allow_other 2>/dev/null || true
rsync -av --exclude '.venv' --exclude '__pycache__' --exclude '.git' \
  /mnt/hgfs/MVNOs_and_MNOs/ntn-roaming-lab/ ~/ntn-roaming-lab/

cd ~/ntn-roaming-lab
python3 scripts/fix_crlf.py
chmod +x scripts/*.sh

# Docker group: ONE line (sg uses dash — never bare `source` inside sg -c)
sg docker -c 'cd ~/ntn-roaming-lab && bash scripts/ubuntu-sg-bootstrap.sh'

# Or if already bootstrapped:
sg docker -c "bash -lc 'cd ~/ntn-roaming-lab && source .venv/bin/activate && make verify-live && make provision-subscribers'"

docker ps
lsmod | grep sctp
```

Expected: home + visited Open5GS + IPX Up; dual-home on `ntn-ipx-net`; `make verify-live` PASS.

Optional mocks / SS7 (SMS/NIDD/billing capture only):

```bash
sg docker -c 'cd ~/ntn-roaming-lab && make up-mocks'
sg docker -c 'cd ~/ntn-roaming-lab && make up-ss7'   # Osmocom — UNVERIFIED runtime
```

---

## 1. What is runnable **today**

| Priority | TC | Status | Ubuntu command |
|----------|-----|--------|----------------|
| 1 | **TC-05** | READY-LIVE | `bash scripts/run-tc-05-golden.sh --with-capture` |
| 2 | **TC-11** | RUNNABLE | `bash scripts/run-ireg-tc.sh TC-11 --with-capture` |
| 3 | **TC-03** | RUNNABLE | `bash scripts/run-ireg-tc.sh TC-03 --with-capture` |
| 4 | **TC-06** | RUNNABLE | `bash scripts/run-ireg-tc.sh TC-06 --with-capture` |
| 5 | **TC-16** | RUNNABLE | `bash scripts/run-ireg-tc.sh TC-16 --with-capture` |
| 6 | **TC-04** | RUNNABLE | `bash scripts/run-ireg-tc.sh TC-04 --with-capture --attach` |
| 7 | **TC-15** | RUNNABLE (attempt) | `bash scripts/run-ireg-tc.sh TC-15 --with-capture` |
| 8 | TC-07/08/12/20 | MOCK-RUNNABLE | `make up-mocks && bash scripts/run-ireg-tc.sh TC-07` |
| 9 | TC-09/13 | MOCK-RUNNABLE | `bash scripts/run-ireg-tc.sh TC-09 --with-capture` |
| 10 | TC-10 | MOCK-RUNNABLE | `bash scripts/run-ireg-tc.sh TC-10 --with-capture` |
| 11 | TC-21 | MOCK-RUNNABLE (netem) | `sudo bash scripts/run-ireg-tc.sh TC-21 --with-capture` |
| — | TC-01/02 | DEFERRED | `bash scripts/run-tc-01-lte-deferred.sh` (offline only) |
| — | TC-14/17–19/22–25 | DEFERRED/BLOCKED | See matrix |

---

## 2. Golden path — TC-05 (5G SA B1) + capture

**Full N2 + SBI + N4/PFCP checklist** (run `014834` had **0 PFCP** in multi-point): [`tc-05-full-capture-checklist.md`](tc-05-full-capture-checklist.md). Prefer `capture-ireg-tc.sh` bridges (`visited-net.pcap` on `ntn-visited-net`) or a multi-point filter that includes SMF/UPF `10.10.2.12`/`10.10.2.13`. Verify `tshark -Y pfcp` count **> 0** before claiming PFCP MEASURED.

### 2.1 Start capture

**Must be root** (`CAP_NET_RAW`). `sg docker` alone is not enough — that caused
`014710` / `030211` / `031413` empty `ran-net.pcap` (`sudo: a password is required`)
while visited/ipx bridges still showed PFCP → Grafana `domains.ran=0`.

```bash
cd ~/ntn-roaming-lab
sudo -E bash scripts/capture-ireg-tc.sh TC-05
# Note the printed pcaps/TC-05/<timestamp>/ directory
# VERIFY before attach: grep listening pcaps/TC-05/<ts>/ran-net.pcap.tcpdump.log
```

Prefer one-shot golden (sudo first, then capture + LBO recreate + attach):

```bash
sudo -E bash scripts/run-tc-05-golden.sh --with-capture
```

After syncing `dashboard/exporters/flow_catalog.py`, recreate exporter (catalog is
bind-mounted; restart picks up multi-point RAN fallback):

```bash
sg docker -c 'cd ~/ntn-roaming-lab/dashboard && docker compose up -d --force-recreate flow-exporter'
```

### 2.2 Attach (keep UE for user-plane)

```bash
export UERANSIM_BIN=~/UERANSIM/build   # adjust
export ATTACH_MODE=b1-home-plmn
export KEEP_UE=1
sudo -E bash scripts/live-first-attach.sh
# or: sudo -E bash scripts/run-tc-05-golden.sh
```

Expect:

- UE/gNB: SUITABLE camp; Registration / PDU success markers
- AMF: `suci-0-001-01-0000-0-0-0000000001` (not `999-70`)
- Architecture: **B1** same-PLMN camp — **not** true VPLMN 999/70 roaming camp
- SEPP: **absent** — dual-home / SBI stand-in (V14)

### 2.3 Confirm logs into capture dir

```bash
# Refresh NF logs into latest TC-05 dir (snapshot-only creates a *new* ts —
# prefer copying into the running capture dir, or stop+note path from STATE)
sg docker -c 'docker logs visited-amf --tail 200' | tee -a /tmp/amf-tail.txt
# Fill pcaps/TC-05/<ts>/NOTES.md checkboxes
```

### 2.4 Stop capture

```bash
bash scripts/capture-ireg-tc.sh TC-05 --stop
```

### 2.5 Pass criteria (checkable)

| Check | Evidence |
|-------|----------|
| Correct SUCI | AMF log `suci-0-001-01-…` |
| Registration complete | UE `MM-REGISTERED` / Registration accept + AMF |
| Auth chain | home-ausf / home-udm logs without HTTP 404/504 |
| Inter-PLMN path | traffic on ipx-net (dual-home), not claiming N32 |

---

## 3. TC-11 — user plane (same attach)

With `KEEP_UE=1` and root:

```bash
ip addr show uesimtun0
# MEASURED pattern: 10.46.0.5/… ; GW 10.46.0.1
ping -I uesimtun0 10.46.0.1 -c 3
ping -I uesimtun0 8.8.8.8 -c 3   # expect FAIL without NAT — document gap
```

**Honesty:** This is **visited LBO pool** (`UE_IPV4_INTERNET=10.46.0.0/16`), not proven home-routed 10.45. Capture under `TC-11` if running a dedicated capture session.

Stop RAN when done: `pkill -x nr-ue; pkill -x nr-gnb`

---

## 4. Negatives — TC-03 / TC-06 / TC-16

### TC-03 wrong key (5G)

```bash
bash scripts/capture-ireg-tc.sh TC-03
# Point live-first-attach at wrong-key UE (edit or env if script supports; else):
# Temporarily: UE_YAML override — use:
UERANSIM_BIN=~/UERANSIM/build KEEP_UE=0 \
  sudo -E bash -c 'export UE_OVERRIDE=ran/ueransim/ue-home-roamer-wrong-key.yaml
  # If override unsupported, run nr-gnb/nr-ue manually with that YAML while capture runs
  '
```

Preferred manual:

```bash
export UERANSIM_BIN=~/UERANSIM/build
$UERANSIM_BIN/nr-gnb -c ran/ueransim/gnb-home-plmn-auth.yaml &
$UERANSIM_BIN/nr-ue -c ran/ueransim/ue-home-roamer-wrong-key.yaml
# Expect auth failure; no lasting PDU. Do not invent Diameter experimental codes.
bash scripts/capture-ireg-tc.sh TC-03 --stop
```

### TC-06 barred / roaming not allowed

- User cites Diameter **5004** — lab **V1 UNVERIFIED**; do **not** assert as oracle.
- **5G stand-in (MOCK divergence):** temporarily remove HOME `001/01` from visited AMF `access_control`, recreate `visited-amf`, attempt B1 attach → expect cause **#11** (PLMN not allowed), not necessarily 5004.
- Stub file: `home-network/subscribers/lab-subscribers-tc06-barred.ndjson` (documentation marker — ODB bit semantics UNVERIFIED; not auto-provisioned).

### TC-16 unknown DNN

Copy `ue-home-roamer.yaml` → set session DNN to e.g. `internet-bogus` → attach → read **live** 5GSM cause from UE/AMF/SMF logs (expect #27 per user ref — **confirm MEASURED**, do not hardcode pass).

---

## 5. TC-15 HR vs LBO (`ROAMING_MODE`)

| Item | Reality in lab |
|------|----------------|
| `visited-network/docker-compose.yml` | `ROAMING_MODE: ${ROAMING_MODE:-LBO}` on **visited-smf and visited-upf** |
| `smf_init.sh` / `upf_init.sh` | Select HR (**10.45**) or LBO (**10.46**) into `session.subnet` / `session.gateway` before sed |
| `visited-network/.env` | `ROAMING_MODE=LBO`; `UE_IPV4_INTERNET_HR` / `_LBO` pools |
| TC-05 golden | **Must** use LBO — `run-tc-05-golden.sh` recreates SMF+UPF with `ROAMING_MODE=LBO` |
| TC-15 | Explicit `ROAMING_MODE=HR` + recreate **both** SMF and UPF (`run-tc-15-hr.sh`) |
| MEASURED B1 (historical) | UE **10.46.0.5**, GW **10.46.0.1** → visited UPF LBO path |
| Run `20260826T010742` | UE **10.45.0.3** because default was HR and UPF stayed on 10.46 → ping fail (fixed 2026-08-26) |

**Open5GS keys (lab yaml, not invented):** `smf.session[].subnet|gateway|dnn`, `upf.session[].subnet|gateway|dnn` in `visited-network/configs/{smf,upf}/*.yaml`.

Attempt HR (TC-15 only — do **not** leave this as default for golden):

```bash
bash scripts/run-ireg-tc.sh TC-15 --with-capture
# Confirm 10.45.x on uesimtun0 before claiming MEASURED HR
# Address alone ≠ full HR (N16/N9/hUPF still PARTIAL — DEF-0016)
```

Restore LBO for TC-05:

```bash
ROAMING_MODE=LBO docker compose -f visited-network/docker-compose.yml \
  up -d --force-recreate visited-smf visited-upf
# or: bash scripts/run-tc-05-golden.sh
```

---

## 6. SMS / NIDD / SS7 — how to capture (MOCK)

```bash
make up-mocks
bash scripts/capture-ireg-tc.sh TC-07
curl -s http://127.0.0.1:8000/health   # SCEF mock (host port from compose)
# SGd mock listens inside mocks-net :3868 — use docker exec or attach capture on mocks bridge
bash scripts/capture-ireg-tc.sh TC-07 --stop
```

Label every report: **MOCK** — production SGd/T6a/SCEF per cited TS; divergences in mock module headers.

```bash
make up-ss7   # optional; syntax UNVERIFIED
bash scripts/capture-ireg-tc.sh TC-10
```

---

## 7. NTN TC-21…25

1. Clone/build OAI @ commit in `versions.lock` / phase docs (`38dc378`).
2. Overlay `ran/oai/configs/`; apply `ran/oai/netem/apply-netem.sh` (REFERENCE delays).
3. Capture with `capture-ireg-tc.sh TC-21`.
4. Until OAI Up: status remains **DEFERRED-TO-UBUNTU**; offline `pytest -k LAB-IREG-NTN`.

---

## 8. Next 3 TCs after TC-05 golden

1. **TC-11** — GW ping + document no-NAT DN failure  
2. **TC-03** — wrong-key negative (5G)  
3. **TC-07** or **TC-12** — mock SMS/NIDD health + mocks-net pcap (interview “breadth”)

Then: TC-04 synch re-capture if reproducible; TC-15 only after HR wiring verified.
