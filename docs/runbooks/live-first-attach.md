# Live first attach — LAB-IREG-001

**Status:** PENDING until trace-verified on Ubuntu.  
**Tier:** 1 (UERANSIM). **Architecture (intent):** HOME IMSI `001010000000001` via VISITED AMF (SBI to home AUSF/UDM).  
**Active attach track:** **B1** same-PLMN camp (UE+gNB `001/01`) for correct SUCI + auth path — **not** true VPLMN `999/70` camping.

## Root cause (MEASURED Ubuntu smoking gun)

```
[suci-0-999-70-0000-0-0-0000000001] Cannot find SUCI [404]
Registration reject [7]
[ausf] Cannot find SUPI [404]
```

Subscriber in Mongo is `001010000000001`. AUSF/UDM/NRF path works.

**Cause:** UERANSIM UE `mcc`/`mnc` are **HPLMN** fields (wiki: must be consistent with SUPI). `generateSuci()` (`src/ue/nas/mm/identity.cpp`) puts **config `hplmn`** into SUCI and takes MSIN as IMSI digits after HPLMN length — **not** from parsing SUPI MCC/MNC separately.

Lab had wrongly set `mcc`/`mnc: 999/70` "so the cell is SUITABLE" while `supi: imsi-001010000000001` → SUCI `999/70` + MSIN `0000000001` → lookup `imsi-999700000000001` → 404 → cause **#7**.

Earlier with UE `001/01` on gNB `999/70`: cell **ACCEPTABLE** only → **LIMITED-SERVICE** (no Registration).

### Option A — not available in stock UERANSIM

Wiki UE keys: `supi`, `mcc`, `mnc`, `key`, `op`, `opType`, `amf`, `imei`, `imeiSv`, `gnbSearchList`, `uac*`, `sessions`, `configured-nssai`, `default-nssai`, `integrity`/`ciphering`, `integrityMaxRate`, `tun*`, SUCI crypto fields. **No** equivalent-PLMN / preferred-PLMN / serving-PLMN override. Option A (HPLMN 001/01 + camp VPLMN 999/70) requires **patches** — not implemented here.

### Track B1 (default, preferred honest path)

| Piece | Value |
|-------|--------|
| UE | `ran/ueransim/ue-home-roamer.yaml` — `mcc`/`mnc` **001/01**, SUPI `imsi-001010000000001` |
| gNB | `ran/ueransim/gnb-home-plmn-auth.yaml` — broadcast **001/01**, AMF still `10.10.4.11` |
| AMF | `plmn_support` + `tai` include HOME **001/01** (NG Setup) + visited **999/70** (kept for later) |
| Expected AMF log | `suci-0-001-01-0000-0-0-0000000001` |

This proves home-IMSI auth via visited AMF → home AUSF. It is **single-PLMN camp**, not roaming camp. Do **not** label as MEASURED Registration Accept until Ubuntu traces say so.

### Track B2 (last resort MOCK)

Provision `home-network/subscribers/lab-subscribers-mock-vplmn-imsi.ndjson` (`imsi-999700000000001`) **only** if you must camp gNB `999/70` with stock UERANSIM without patches. Labelled **MOCK** — not home-PLMN identity; **not** auto-provisioned by `provision_subscribers.sh`.

## What `PAYLOAD_NOT_FORWARDED` means here

UERANSIM (v3.3.0) reports **Initial Registration failed [PAYLOAD_NOT_FORWARDED]** when the gNB still has a UE NAS PDU but **cannot send it on NGAP** because the AMF has already released the UE context.

In this lab that is **not** (by itself) an SCTP-stream bug: reference `open5gs-gnb.yaml` sets `ignoreStreamIds: true`, and the lab gNB already has that. NG Setup to `10.10.4.11:38412` **MEASURED SUCCESS** means N2 is up.

Typical B1 sequence:

1. UE camps **SUITABLE** on same-PLMN gNB **001/01** (`gnb-home-plmn-auth.yaml`).
2. UE sends Initial Registration with SUCI `suci-0-001-01-…-0000000001`.
3. Visited AMF starts 5G-AKA: NRF-discover **AUSF** for SUPI PLMN **001-01**.
4. If discovery/connect fails (often HTTP **504**), Open5GS maps that to 5GMM cause **#65 Payload was not forwarded**; AMF **UE Context Release**; gNB then returns `PAYLOAD_NOT_FORWARDED` on the T3511 retry loop (~10s).

## What `FIVEG_SERVICES_NOT_ALLOWED` / `5U3-ROAMING-NOT-ALLOWED` means here

UERANSIM names 5GMM cause **#7** as `FIVEG_SERVICES_NOT_ALLOWED`. Per TS 24.501, the UE then sets 5GS update status to **5U3 ROAMING NOT ALLOWED** (UERANSIM state `5U3-ROAMING-NOT-ALLOWED`).

**Open5GS AMF mapping (verified in upstream `src/amf/nas-path.c` `gmm_cause_from_sbi` and `gmm-sm.c`):**

| Cause | Typical Open5GS trigger | Log hint |
|-------|-------------------------|----------|
| **#7** 5GS services not allowed | HTTP **404** from AUSF/UDM (`Cannot find SUCI`, nudm-uecm/sdm error) or `Registration rejected due to RAT restrictions` | `Registration reject [7]`, `Cannot find SUCI`, `HTTP response error [404]` |
| **#11** PLMN not allowed | Home PLMN **not** in `amf.access_control` (default reject) | `Rejected by PLMN-ID access control` |
| **#65** Payload was not forwarded | HTTP **504** / AUSF unreachable | Often surfaces as UERANSIM `PAYLOAD_NOT_FORWARDED` after UE context release |

So progress from `PAYLOAD_NOT_FORWARDED` → `#7` with SUCI **999-70** meant: N2 + AUSF reachability OK, but wrong SUCI PLMN (UE `mcc`/`mnc` 999/70). After B1 fix, expect SUCI **001-01**; remaining #7 would be real missing subscriber/keys, not HPLMN mis-encode.

**Subscriber Mongo fields (home-mongo):** Open5GS default `access_restriction_data: 32` is bit5 *HO to non-3GPP not allowed* — **not** NR barred. `subscriber_status: 0` = SERVICE_GRANTED. Confirm IMSI `001010000000001` is in `open5gs.subscribers` and UDR uses `mongodb://10.10.1.20/open5gs`.

**Config evidence (Windows, not MEASURED logs):** Open5GS **MEASURED** constraint: `Only one NRF client can be set` (`lib/sbi/context.c`) — each NF may list **exactly one** `sbi.client.nrf` URI. Lab design: visited AMF/SCP → visited NRF `10.10.2.10`; home AUSF/UDM/UDR/PCF → same visited NRF via IPX `10.10.3.30`. Visited AMF `access_control` + `guami` + `tai`/`plmn_support` include HOME **001-01**.

Reference private-5g is **single PLMN** (UE IMSI `99970…` + AMF 999/70). Copy **schema** only; roaming IPs stay lab.

## Prerequisites

1. **Recreate stacks with docker group via `sg` + bash** (not `newgrp` in a multi-line paste — it swallows following commands; not bare `source` inside `sg -c` — dash has no `source`):
   ```bash
   sg docker -c 'cd ~/ntn-roaming-lab && bash scripts/ubuntu-sg-bootstrap.sh'
   ```
   That runs `make bootstrap-docker` (home NRF/AUSF/UDM/UDR/PCF/SCP + visited NRF/AMF/SCP on **ipx-net**, `--force-recreate`), `make provision-subscribers`, and `make verify-live` (checks IPX IPs + single-NRF-client YAML + UE HPLMN 001/01).
2. UERANSIM built on VM (`nr-gnb`, `nr-ue` in PATH or `UERANSIM_BIN`) — configs must match **v3.3.x** schema
3. Host has `10.10.4.10/24` on `ntn-ran-net` bridge; gNB AMF address is `10.10.4.11`
4. SCTP loaded: `lsmod | grep sctp`
5. Visited AMF `access_control` **and** HOME `guami`/`tai`/`plmn_support` include HOME PLMN **001-01** after sed

## Sequence (B1 — Ubuntu paste)

```bash
# After sync + fix_crlf (see ubuntu-bootstrap.md), recreate if needed:
sg docker -c 'cd ~/ntn-roaming-lab && bash scripts/ubuntu-sg-bootstrap.sh'

cd ~/ntn-roaming-lab
# confirm dual-home (verify-live already checks these) — expect ntn-ipx-net=
sg docker -c "docker inspect -f '{{.Name}} {{range \$k,\$v := .NetworkSettings.Networks}}{{\$k}}={{\$v.IPAddress}} {{end}}' \
  home-nrf home-ausf home-udm home-udr home-pcf home-scp visited-nrf visited-amf visited-scp"

# Confirm UE HPLMN + B1 gNB on disk after sync
grep -E "^(supi|mcc|mnc):" ran/ueransim/ue-home-roamer.yaml
grep -E "^(mcc|mnc):" ran/ueransim/gnb-home-plmn-auth.yaml

source .venv/bin/activate
export UERANSIM_BIN=~/UERANSIM/build   # adjust
export ATTACH_MODE=b1-home-plmn        # default; uses gnb-home-plmn-auth.yaml
bash scripts/live-first-attach.sh

# Expect in visited-amf (use sg docker):
sg docker -c 'docker logs visited-amf --tail 200 2>&1 | grep -E "suci-0-|Registration"'
# Want: suci-0-001-01-0000-0-0-0000000001
# Not:  suci-0-999-70-0000-0-0-0000000001
```

## User-plane TUN (Ubuntu paste)

Default `live-first-attach.sh` **tears down** nr-gnb/nr-ue on EXIT (CI-friendly). That kills the session → gNB “signal lost” / UE Context Release → **`uesimtun0` never exists** afterward.

For TUN / ping, keep RAN up and run as root so nr-ue can create the interface:

```bash
export ATTACH_MODE=b1-home-plmn KEEP_UE=1
sudo -E bash scripts/live-first-attach.sh
# wait for PDU success, then in another terminal:
ip addr show uesimtun0
ping -I uesimtun0 <ue-ip-or-dn> -c 3
```

Notes:

- `KEEP_RUNNING=1` is an alias for `KEEP_UE=1`. On **failure**, the script still cleans up.
- Tcpdump / stderr logs go under `pcaps/LAB-IREG-001/<timestamp>/` (not `/tmp`) so sudo vs user do not clash on log ownership.
- Script preflight adds `10.10.4.10/24` on the `ntn-ran-net` bridge if missing, and kills stale `nr-gnb`/`nr-ue` at start.
- Read the PDU IPv4 from `uesimtun0` (do not invent). Ping the **UPF session gateway** for that UE pool if needed (lab home pool GW is configured as `10.45.0.1` in home UPF YAML; confirm from your live UPF/session, not from memory alone).
- DN ping (e.g. `8.8.8.8`) may **fail** if the UPF has no NAT / default route — that is a user-plane routing gap, not proof that TUN is missing.
- Stop when done: `pkill -x nr-ue; pkill -x nr-gnb` (or the PIDs printed by the script).

## Pass criteria (trace-evidenced)

| Check | Evidence |
|-------|----------|
| Correct SUCI | AMF log `suci-0-001-01-0000-0-0-0000000001` |
| Cell camping | UE log: cell category **SUITABLE** (B1 same-PLMN) |
| Registration Accept | NAS in pcap or AMF/UE log (`MM-REGISTERED`) — **do not claim MEASURED until seen** |
| Auth success | AIA / 5G-AKA completion |
| Domain | Visited AMF reaches Home AUSF/UDM/PCF via **ipx-net** |
| User plane | PDU session + `uesimtun0` present while nr-ue still running (`KEEP_UE=1`) |

Do **not** label Registration Accept **MEASURED** until AMF/AUSF logs or pcap show 5G-AKA + NAS Accept.

**TUN / user-plane note (MEASURED):** After Registration Accept + PDU Session Establishment Accept, (1) EXIT teardown of the attach script kills nr-ue → no `uesimtun0`; use `KEEP_UE=1`. (2) Without root/`CAP_NET_ADMIN`, UERANSIM may log TUN `Permission denied` — use `sudo -E`. Control-plane Registration/PDU Accept do not require TUN.

## Failure attribution

| Symptom | Likely domain |
|---------|----------------|
| SCTP timeout to AMF | VISITED / RAN |
| Restart loop + `Only one NRF client can be set` | Dual `sbi.client.nrf` URIs — sync fix + recreate |
| `PAYLOAD_NOT_FORWARDED` + UE Context Release | AUSF unreachable / HTTP 504 — dual-home + single NRF |
| SUCI `999-70` + `Cannot find SUCI` + #7 | UE `mcc`/`mnc` still 999/70 — resync B1 YAML |
| `LIMITED-SERVICE` / ACCEPTABLE | UE HPLMN ≠ gNB broadcast (visited gNB 999/70 + UE 001/01) |
| `FIVEG_SERVICES_NOT_ALLOWED` + SUCI `001-01` + #7 | Real 404 / nudm — collect AMF+AUSF+UDM+UDR |
| `Rejected by PLMN-ID access control` / cause #11 | Visited AMF `access_control` missing **001-01** after sed |
| Unknown subscriber | HOME (Mongo / UDR) |
| Auth failure (MAC/RES*) | HOME keys vs `ue-home-roamer.yaml` |
| No NGAP / unknown-PLMN on B1 gNB | AMF missing HOME in `plmn_support` — recreate visited-amf |

## Collect if still failing (paste back)

Prefer `sg docker` so the docker group applies:

```bash
sg docker -c 'bash -lc '"'"'
set -e
cd ~/ntn-roaming-lab

# Dual-home sanity
docker inspect -f "{{.Name}} {{range \$k,\$v := .NetworkSettings.Networks}}{{\$k}}={{\$v.IPAddress}} {{end}}" \
  home-nrf home-ausf home-udm home-udr home-pcf home-scp visited-nrf visited-amf visited-scp

# Rendered AMF access_control + guami + plmn_support (expect mcc 001 / mnc 01 after sed)
docker exec visited-amf grep -A40 access_control /open5gs/install/etc/open5gs/amf.yaml || true
docker exec visited-amf grep -A25 guami /open5gs/install/etc/open5gs/amf.yaml || true
docker exec visited-amf grep -A30 plmn_support /open5gs/install/etc/open5gs/amf.yaml || true

# Subscriber fields that matter for deny
docker exec home-mongo mongosh open5gs --quiet --eval \
  "db.subscribers.findOne({imsi:\"001010000000001\"},{imsi:1,access_restriction_data:1,subscriber_status:1,operator_determined_barring:1,slice:1})"

# Focused reject / discovery lines — confirm SUCI is 001-01 not 999-70
docker logs visited-amf --tail 300 2>&1 | grep -Ei "reject|access_control|SUCI|SUPI|AUSF|UDM|404|NSSAI|RAT|PLMN|HTTP response|Cannot find|suci-0-" || true
docker logs home-ausf --tail 200 2>&1 | grep -Ei "error|warn|404|SUCI|UDM|auth" || true
docker logs home-udm --tail 150 2>&1 | grep -Ei "error|warn|404|UDR|SUPI" || true
docker logs home-udr --tail 100 2>&1 | grep -Ei "error|warn|404|mongo|imsi" || true
docker logs home-pcf --tail 80 2>&1 | grep -Ei "error|warn|nrf|register" || true
docker logs visited-nrf --tail 80 2>&1 | grep -Ei "AUSF|UDM|UDR|PCF|error" || true

# Full tails if grep is empty
docker logs visited-amf --tail 200
docker logs home-ausf --tail 120
docker logs home-udm --tail 80
docker logs home-udr --tail 80
'"'"'
```

Grep hints (do not invent codes): `Only one NRF`, `No [AUSF]`, `NF discover`, `Cannot find NF`, `Cannot find SUCI`, `suci-0-001-01`, `suci-0-999-70`, `Registration reject [7]`, `Rejected by PLMN-ID access control`, `HTTP response error [404]`, `access_control`, `Failed to connect`.

## Limitations

- **UERANSIM:** no dual-PLMN (HPLMN SUCI + VPLMN camp) without patches. B1 ≠ true roaming camp.
- Open5GS **SEPP/N32 is not deployed** in this lab (V14). Inter-PLMN SBI is **ipx-net dual-home + single visited NRF registration**, not N32-c/N32-f.
- Open5GS allows **one NRF client per NF** (MEASURED). Do not list home+visited NRF URIs together.
- `ipx-sbi-proxy` is HTTP/1 FastAPI — Open5GS SBI is HTTP/2; proxy is **not** the attach data path.
- Full HR roaming auth via IPX DRA may be **UNVERIFIED** until freeDiameter peers configured.
- Reference Open5GS tutorial uses FQDN + SEPP; this stand-in uses **IPs on ipx-net**. UNVERIFIED until Ubuntu traces.
