# TC-05 full capture checklist (N2 + SBI + N4/PFCP)

**Why:** Run `20260826T014834` was LBO MEASURED on N2/SBI, but `multi-point.pcap` had **0 PFCP** frames. Root cause: host-filtered `tcpdump` omitted visited SMF/UPF N4 addresses. Do not claim PFCP MEASURED until frames exist.

**Related:** [LBO MEASURED evidence](../evidence/TC-05-20260826T014834-LBO-MEASURED.md) · [DEMO-SNAPS](../evidence/TC-05-20260826T014834-DEMO-SNAPS.md) · [ireg-tc-execution](ireg-tc-execution.md) · [TC-05-spec](../specs/TC-05-spec.md)

Labels: MEASURED only from Ubuntu pcaps. Windows = review/archive only.

---

## N4 / PFCP capture targets (from lab configs)

| Item | Value | Source |
|------|--------|--------|
| Docker network | `ntn-visited-net` | `visited-network/docker-compose.yml` (`name: ntn-visited-net`) |
| Bridge iface | `br-<first-12-of-network-Id>` | `scripts/capture-ireg-tc.sh` `bridge_for_net` |
| Subnet | `10.10.2.0/24` | `network-plan.yaml` `networks.visited-net` |
| Visited SMF (N4) | `10.10.2.12` | `network-plan.yaml` `hosts.visited.smf`; `visited-network/configs/smf/open5gs-smf.yaml` `pfcp.server` |
| Visited UPF (N4) | `10.10.2.13` | `network-plan.yaml` `hosts.visited.upf`; `open5gs-upf.yaml` `pfcp.server` |
| PFCP port | UDP/8805 | `network-plan.yaml` `hosts.visited.upf.ports.pfcp` |

Also capture: RAN/N2 (`ntn-ran-net`, gNB `10.10.4.10`, AMF `10.10.4.11`); IPX/SBI (`ntn-ipx-net`, AUSF/UDM `10.10.3.21`/`.22`); visited SBI+N4 on `ntn-visited-net` (AMF `.11`, SMF `.12`, UPF `.13`).

---

## Ordered steps (next TC-05 / LAB-IREG-001 run)

### 1. Start capture before attach

Prefer bridge multi-file capture (includes N4 when `ntn-visited-net` exists):

```bash
cd ~/ntn-roaming-lab
sg docker -c 'bash scripts/capture-ireg-tc.sh TC-05'
# Note printed pcaps/TC-05/<timestamp>/
```

Or golden wrapper:

```bash
sudo -E bash scripts/run-tc-05-golden.sh --with-capture
```

If using `live-first-attach.sh` alone: ensure its `multi-point` host filter includes **`10.10.2.12` and `10.10.2.13`** (local patch 2026-08-26). Old filter (AMF + home AUSF/UDM only) yields **0 PFCP**.

### 2. Verify capture points before attach

```bash
source pcaps/.capture-state/TC-05.env
ls -la "$PCAP_DIR"/*.pcap 2>/dev/null || true
cat "$PCAP_DIR/tcpdump.pids"
docker network inspect ntn-visited-net -f '{{.Id}}' | cut -c1-12
```

- [ ] RAN / N2 (`ran-net.pcap` or multi-point with `10.10.4.10`/`10.10.4.11`)
- [ ] IPX / SBI (`ipx-net.pcap` or multi-point with `10.10.3.2x`)
- [ ] **N4 SMF↔UPF** (`visited-net.pcap` **or** multi-point hosts include `10.10.2.12` **and** `10.10.2.13`)

### 3. Attach (LBO)

```bash
export UERANSIM_BIN=~/UERANSIM/build ATTACH_MODE=b1-home-plmn KEEP_UE=1 ROAMING_MODE=LBO
sudo -E bash scripts/run-tc-05-golden.sh
# or, if capture already running:
sudo -E bash scripts/live-first-attach.sh
```

Expect `uesimtun0` in **10.46.0.0/16**, GW ping `10.46.0.1` OK. Do not claim DN `8.8.8.8`.

### 4. Before stop — prove PFCP present

```bash
PCAP="${PCAP_DIR}/visited-net.pcap"
# If only multi-point: PCAP="${PCAP_DIR}/multi-point.pcap"

ls -la "$PCAP" "$PCAP_DIR"/*.pcap

tshark -r "$PCAP" -Y pfcp 2>/dev/null | wc -l
# MUST be > 0 before claiming PFCP MEASURED

tshark -r "$PCAP" -Y 'pfcp && (ip.addr == 10.10.2.12 || ip.addr == 10.10.2.13)' \
  -T fields -e frame.number -e ip.src -e ip.dst -e pfcp.msg_type 2>/dev/null | head -40
```

Optional: `tshark -r "$PCAP" -Y 'udp.port == 8805' | wc -l`

If count is **0**: do not stop and invent PFCP — fix capture and re-run with capture already running.

### 5. PFCP messages to look for (lab docs / Open5GS N4)

Names match `docs/specs/TC-05-spec.md` — do not invent Wireshark `msg_type` integers beyond what you see:

| When | Message | Notes |
|------|---------|--------|
| Often at SMF/UPF start / recreate | PFCP Association Setup Request/Response | May appear when golden script force-recreates SMF+UPF during capture |
| During PDU (required for N4 claim) | PFCP Session Establishment Request/Response | Spec step `pdu-3`; filter `pfcp && (ip.addr == 10.10.2.12 \|\| ip.addr == 10.10.2.13)` |
| After SM context / N3 programming | PFCP Session Modification Request/Response | Spec step `pdu-9`; `pfcp.msg_type == 50/51` is UNVERIFIED (V27) — generic `pfcp` is enough |

```bash
docker logs visited-smf --tail 200 2>&1 | grep -iE 'pfcp|session'
docker logs visited-upf --tail 200 2>&1 | grep -iE 'pfcp|session'
```

### 6. Stop + archive

```bash
KEEP_FLOW_METRICS=1 bash scripts/capture-ireg-tc.sh TC-05 --stop
```

Ubuntu → Windows (adjust share path):

```bash
DEST=/mnt/hgfs/MVNOs_and_MNOs/ntn-roaming-lab
TS=<timestamp>
mkdir -p "$DEST/pcaps/TC-05/$TS" "$DEST/pcaps/LAB-IREG-001/$TS"
rsync -av ~/ntn-roaming-lab/pcaps/TC-05/$TS/ "$DEST/pcaps/TC-05/$TS/"
rsync -av ~/ntn-roaming-lab/pcaps/LAB-IREG-001/$TS/ "$DEST/pcaps/LAB-IREG-001/$TS/"
```

### 7. Honesty gate

| Claim | Allowed only if |
|-------|-----------------|
| N2 / NAS / PDU Accept MEASURED | Frames in ran-net / multi-point (as in 014834) |
| Home AUSF/UDM SBI MEASURED | Frames on ipx-net / multi-point |
| **PFCP / N4 MEASURED** | `tshark -Y pfcp` count **> 0** on `visited-net.pcap` or multi-point that includes `10.10.2.12`/`10.10.2.13` |
| Snap **W9** (PFCP Session Establishment) | Pending until that pcap exists — see DEMO-SNAPS |

Run `014834`: do **not** claim PFCP from that `multi-point.pcap`. Next run: use this checklist.

---

## Script notes (private `scripts/` — gitignored in public tree)

| Script | Behavior | Patch |
|--------|----------|-------|
| `capture-ireg-tc.sh` | TC-05 dumps `visited-net.pcap` on `ntn-visited-net` — correct for N4 when bridges exist | Fallback `multi-point` host list must include `10.10.2.12` and `10.10.2.13` |
| `live-first-attach.sh` | Wrote LAB-IREG-001 `multi-point.pcap` for 014834 | Was missing N4 hosts — add `10.10.2.12` `10.10.2.13` |
| `run-tc-05-golden.sh` | `--with-capture` then LBO recreate + attach | Prefer over attach-only multi-point |

Public repo documents the checklist; operational patches live in the private companion / local `scripts/` after sync.
