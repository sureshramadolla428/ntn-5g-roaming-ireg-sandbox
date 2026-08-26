# 5G SA roaming reference flows → lab evidence map

**Purpose:** Map the user’s four interview sequence diagrams (5G SA roaming) to **checkable** lab artifacts — pcaps, docker logs, and TC status — without overstating what B1 proves.

**Related:** [`docs/ireg-tc-matrix.md`](../ireg-tc-matrix.md) · [`docs/limitations.md`](../limitations.md) · [`docs/defect-log.md`](../defect-log.md) (DEF-0014, DEF-0016) · [`docs/runbooks/ireg-tc-execution.md`](../runbooks/ireg-tc-execution.md) · [`docs/runbooks/grafana-5g-flow.md`](../runbooks/grafana-5g-flow.md) (Grafana ladder dashboard)

**Spec refs in matrix rows:** cited there only where already documented; **do not treat this file as a 3GPP clause oracle**. Unverified procedure names are marked **UNVERIFIED**.

---

## Lab honesty (read before interview)

| Topic | Lab reality |
|-------|-------------|
| **Roaming camp** | **B1** = UE/gNB broadcast **001/01** (same PLMN); home subscriber auth via ipx-net. **Not** true VPLMN **999/70** camp — [DEF-0014](../defect-log.md). |
| **SEPP / N32** | **Absent.** Home NFs register on `ntn-ipx-net`; SBI is direct HTTP/2 between dual-home IPs. `ipx-sbi-proxy` exists but is a labelled stand-in — **not** N32 ([V14](../../ipx/docker-compose.yml)). |
| **TC-05 (golden)** | **MEASURED PASS (LBO):** 5G-AKA + registration + PDU; UE **10.46.0.3** (`20260826T014834`). Default `ROAMING_MODE=LBO`. Prior `20260826T010742` (**10.45.0.3**) SUPERSEDED. |
| **TC-15 (HR attempt)** | **RUNNABLE** (`ROAMING_MODE=HR` on visited-smf+upf); **not MEASURED** until `uesimtun0` shows **10.45.x** and N16/N9 honesty ([DEF-0016](../defect-log.md)). |
| **Evidence label** | **MEASURED** only from Ubuntu pcaps/logs reviewed on host. Windows scaffold = **DEFERRED-TO-UBUNTU**. |

### NF anchor IPs (ipx-net / primary)

| NF | Container | visited-net / home-net | ipx-net |
|----|-----------|------------------------|---------|
| Visited AMF | `visited-amf` | 10.10.2.11 (+ 10.10.4.11 ran) | **10.10.3.31** |
| Visited SMF / UPF | `visited-smf` / `visited-upf` | 10.10.2.12 / 10.10.2.13 | — |
| Visited NRF / SCP | `visited-nrf` / `visited-scp` | 10.10.2.10 / 10.10.2.21 | 10.10.3.30 / 10.10.3.32 |
| Home AUSF / UDM / UDR | `home-ausf` / `home-udm` / `home-udr` | 10.10.1.11 / .12 / .13 | **10.10.3.21 / .22 / .24** |
| Home PCF / SMF / UPF | `home-pcf` / `home-smf` / `home-upf` | 10.10.1.15 / .23 / .24 | 10.10.3.25 / — / — |
| Home NRF | `home-nrf` | 10.10.1.10 | 10.10.3.20 |
| IPX DRA / SBI stand-in | `ipx-dra` / `ipx-sbi-proxy` | .30 legs on home/visited | 10.10.3.10 / 10.10.3.11 |

UE pools: **LBO** `10.46.0.0/16` (MEASURED B1) · **HR** `10.45.0.0/16` (TC-15 target, unproven).

---

## Quick Ubuntu workflow (sync → capture → stop)

```bash
# 1) Sync from Windows share (adjust path)
rsync -av --exclude '.venv' --exclude '__pycache__' \
  /mnt/hgfs/MVNOs_and_MNOs/ntn-roaming-lab/ ~/ntn-roaming-lab/
cd ~/ntn-roaming-lab && python3 scripts/fix_crlf.py && chmod +x scripts/*.sh

# 2) Stack + golden TC-05 with capture
sg docker -c 'cd ~/ntn-roaming-lab && make verify-live && make provision-subscribers'
bash scripts/run-tc-05-golden.sh --with-capture
# Or manually: bash scripts/capture-ireg-tc.sh TC-05
#              export UERANSIM_BIN=~/UERANSIM/build ATTACH_MODE=b1-home-plmn KEEP_UE=1
#              sudo -E bash scripts/live-first-attach.sh

# 3) Refresh logs into capture dir (optional)
bash scripts/capture-ireg-tc.sh TC-05 --snapshot-only

# 4) Stop capture + fill NOTES.md checkboxes
bash scripts/capture-ireg-tc.sh TC-05 --stop

# 5) Refresh Grafana flow ladder (optional — see docs/runbooks/grafana-5g-flow.md)
bash scripts/refresh-flow-dashboard.sh TC-05
```

**Output layout:** `pcaps/TC-05/<YYYYMMDDTHHMMSS>/`

| Artifact | Path |
|----------|------|
| RAN (NGAP/N1) | `ran-net.pcap` |
| Visited PLMN | `visited-net.pcap` |
| Home PLMN | `home-net.pcap` |
| IPX / dual-home SBI | `ipx-net.pcap` |
| NF logs | `docker-logs/{visited-amf,home-ausf,…}.log` |
| Interview checklist | `NOTES.md` (auto-seeded by capture script) |

**HR attempt:** replace `TC-05` with `TC-15` and `bash scripts/run-ireg-tc.sh TC-15 --with-capture`.

---

## Flow 1 — Subscriber Authentication from VPLMN (5G-AKA)

Reference: UE → gNB → AMF; AMF → AUSF → UDM; 5G-AKA.  
**Primary TC:** TC-05 · **Capture TC id:** `TC-05` (or `TC-15` if re-running attach under HR).

| Step # | Message / procedure | Source → Destination | Protocol (HTTP/2 path, NGAP, PFCP, NAS) | PCAP file + Wireshark display filter | Docker log + grep pattern | TC-05 | TC-15 HR | Lab divergence note |
|--------|---------------------|----------------------|-------------------------------------------|--------------------------------------|----------------------------|-------|----------|------------------------|
| 1 | Registration Request (incl. SUCI) | UE → gNB → AMF | NAS-5GS (`nas-5gs.mm.message_type == 0x41` Registration Request) | `ran-net.pcap` · `ngap \|\| nas-5gs` | UE stdout / `grep -iE 'registration\|suci'` in attach log | **MEASURED** | PARTIAL (same B1 attach recipe) | B1 SUCI `suci-0-001-01-…` — not VPLMN 999/70 camp (DEF-0014) |
| 2 | Initial UE Message / NAS transport | gNB → AMF | NGAP (`ngap`) | `ran-net.pcap` · `ngap && (ip.addr == 10.10.4.11 \|\| ip.addr == 10.10.2.11)` | `visited-amf.log` · `grep -iE 'Initial|NGAP|Registration'` | **MEASURED** | PARTIAL | gNB on ran-net; AMF dual-homed |
| 3 | Nausf_UEAuthentication create | AMF → AUSF | HTTP/2 `POST /nausf-auth/v1/ue-authentications` | `ipx-net.pcap` · `http2 && ip.addr == 10.10.3.31 && ip.addr == 10.10.3.21` | `visited-amf.log` · `grep -i ausf`; `home-ausf.log` · `grep -iE 'ue-authentication\|5G-AKA'` | **MEASURED** | PARTIAL | No SEPP — direct ipx-net SBI (V14) |
| 4 | Nudm_UEAuthentication_Get (auth data) | AUSF → UDM | HTTP/2 `GET /nudm-ueau/v1/...` **UNVERIFIED** exact path | `ipx-net.pcap` · `http2 && ip.addr == 10.10.3.21 && ip.addr == 10.10.3.22` | `home-ausf.log` · `grep -i udm`; `home-udm.log` · `grep -iE 'auth\|vector'` | **MEASURED** | PARTIAL | Home NFs on ipx-net toward visited NRF |
| 5 | Nudr_DR query (subscription/auth) | UDM → UDR | HTTP/2 `/nudr-dr/v2/...` **UNVERIFIED** | `ipx-net.pcap` · `http2 && ip.addr == 10.10.3.22 && ip.addr == 10.10.3.24` | `home-udm.log` · `grep -i udr`; `home-udr.log` · `grep -iE 'subscription\|auth'` | **MEASURED** | PARTIAL | Same dual-home path |
| 6 | 5G-AKA challenge (RAND/AUTN) | AMF → UE | NAS-5GS (`nas-5gs`) | `ran-net.pcap` · `nas-5gs` | `visited-amf.log` · `grep -iE 'Authentication\|RAND'` | **MEASURED** | PARTIAL | protectionScheme may be 0 in lab — note in NOTES.md |
| 7 | Authentication Response | UE → AMF | NAS-5GS | `ran-net.pcap` · `nas-5gs.mm.message_type == 0x57` | UE log · `grep -i auth` | **MEASURED** | PARTIAL | — |
| 8 | Nausf_UEAuthentication confirm | AMF → AUSF | HTTP/2 `PUT …/5g-aka-confirmation` **UNVERIFIED** | `ipx-net.pcap` · `http2 && ip.addr == 10.10.3.31 && ip.addr == 10.10.3.21` | `home-ausf.log` · `grep -iE 'confirm\|success'` | **MEASURED** | PARTIAL | Expect HTTP 2xx; no 404 on `suci-0-001-01-…` |
| 9 | Security Mode Command / Complete | AMF ↔ UE | NAS-5GS + NGAP | `ran-net.pcap` · `nas-5gs \|\| ngap` | `visited-amf.log` · `grep -i 'Security Mode'` | **MEASURED** | PARTIAL | Completes auth phase before registration |

---

## Flow 2 — Subscriber Registration from VPLMN

Reference: AMF → NRF; Nudm_UECM_Registration; Nudm_SDM_Get/Subscribe; Nudr_DR.  
**Primary TC:** TC-05.

| Step # | Message / procedure | Source → Destination | Protocol | PCAP + filter | Docker log + grep | TC-05 | TC-15 HR | Lab divergence note |
|--------|---------------------|----------------------|----------|---------------|-------------------|-------|----------|------------------------|
| 1 | NF discovery (AUSF/UDM/PCF) | AMF → NRF | HTTP/2 `/nnrf-nfm/v1/nf-instances` | `ipx-net.pcap` · `http2 && (ip.addr == 10.10.3.31 && ip.addr == 10.10.3.30)` | `visited-amf.log` · `grep -i nrf`; `visited-nrf.log` · `grep -i instance` | **MEASURED** | PARTIAL | Visited NRF on ipx; home NFs also register here |
| 2 | Nudm_UECM_Registration | AMF → UDM | HTTP/2 `PUT /nudm-uecm/v1/.../registrations/amf-3gpp-access` **UNVERIFIED** | `ipx-net.pcap` · `http2 && ip.addr == 10.10.3.31 && ip.addr == 10.10.3.22` | `home-udm.log` · `grep -iE 'uecm\|registration\|amf-3gpp'` | **MEASURED** | PARTIAL | Roaming registration at home UDM — not visited UDM |
| 3 | Nudm_SDM_Get (subscription data) | AMF → UDM | HTTP/2 `GET /nudm-sdm/v1/...` | `ipx-net.pcap` · `http2 && frame contains "nudm-sdm"` | `home-udm.log` · `grep -i sdm` | **MEASURED** | PARTIAL | Slice/DNN from home profile |
| 4 | Nudm_SDM_Subscribe | AMF → UDM | HTTP/2 `POST /nudm-sdm/v1/.../sdm-subscriptions` **UNVERIFIED** | `ipx-net.pcap` · `http2 && ip.addr == 10.10.3.22` | `home-udm.log` · `grep -i subscribe` | **PARTIAL** | PARTIAL | Confirm in pcap if needed for interview depth |
| 5 | Nudr_DR (read/update UE context) | UDM → UDR | HTTP/2 `/nudr-dr/v2/...` | `ipx-net.pcap` · `http2 && ip.addr == 10.10.3.24` | `home-udr.log` · `grep -iE 'uecm\|sdm\|subscription'` | **MEASURED** | PARTIAL | Mongo via UDR on home-net + ipx |
| 6 | Npcf_AMPolicyControl (if triggered) | AMF → PCF | HTTP/2 `/npcf-am-policy-control/...` **UNVERIFIED** | `ipx-net.pcap` · `http2 && ip.addr == 10.10.3.25` | `home-pcf.log` · `grep -i policy` | **PARTIAL** | PARTIAL | PCF dual-home 10.10.3.25 |
| 7 | Registration Accept | AMF → UE | NAS-5GS + NGAP | `ran-net.pcap` · `nas-5gs.mm.message_type == 0x42` | UE · `MM-REGISTERED`; `visited-amf.log` · `grep -i 'Registration accept'` | **MEASURED** | PARTIAL | B1: registration succeeds on 001/01 camp |

---

## Flow 3 — PDU Session Establishment (1/2) Home Routed

Reference: UE → AMF → vSMF → vUPF (N4); vSMF → hSMF; hSMF → UDM/UDR.  
**TC-05:** LBO-style (visited SMF/UPF only) **MEASURED**. **TC-15:** HR wiring **attempt** — hSMF path **not MEASURED** until 10.45.x.

| Step # | Message / procedure | Source → Destination | Protocol | PCAP + filter | Docker log + grep | TC-05 | TC-15 HR | Lab divergence note |
|--------|---------------------|----------------------|----------|---------------|-------------------|-------|----------|------------------------|
| 1 | PDU Session Establishment Request | UE → AMF | NAS-5GS (`nas-5gs.sm.message_type == 0xc1`) | `ran-net.pcap` · `nas-5gs.sm` | UE · `grep -i PDU`; `visited-amf.log` · `grep -i PDU` | **MEASURED** | PARTIAL | DNN `internet` in default UE YAML |
| 2 | Nsmf_PDUSession create SM context | AMF → vSMF | HTTP/2 `POST /nsmf-pdusession/v1/sm-contexts` | `visited-net.pcap` · `http2 && ip.addr == 10.10.2.11 && ip.addr == 10.10.2.12` | `visited-amf.log` · `grep -i smf`; `visited-smf.log` · `grep -iE 'PDU\|session\|sm-context'` | **MEASURED** | PARTIAL | TC-05 uses visited SMF only for session anchor |
| 3 | PFCP Session Establishment (vUPF) | vSMF → vUPF | PFCP (`pfcp`) | `visited-net.pcap` · `pfcp && (ip.addr == 10.10.2.12 \|\| ip.addr == 10.10.2.13)` | `visited-smf.log` · `grep -i pfcp`; `visited-upf.log` · `grep -i session` | **MEASURED** | PARTIAL | **LBO:** user plane stays on visited UPF (10.46 pool) |
| 4 | Nsmf_PDUSession create (HR) / vSMF → hSMF | vSMF → hSMF | HTTP/2 N16 `/nsmf-pdusession/...` **UNVERIFIED** | `ipx-net.pcap` · `http2 && ip.addr == 10.10.2.12` (vSMF has no ipx — may appear on visited-net only) | `visited-smf.log` · `grep -iE 'home\|hSMF\|roam'`; `home-smf.log` · `grep -iE 'PDU\|session\|roam'` | **N/A** | PARTIAL | **TC-05 skips hSMF** — DEF-0016; HR requires home-smf Up + routing |
| 5 | Nudm_SDM_Get / Nudm_UECM (session) | hSMF → UDM | HTTP/2 `nudm-*` | `ipx-net.pcap` · `http2 && ip.addr == 10.10.1.23` (home-smf home-net) | `home-smf.log` · `grep -i udm`; `home-udm.log` · `grep -i session` | **N/A** | PARTIAL | Visible on home-net pcap if HR succeeds |
| 6 | Nudr_DR (session subscription) | UDM → UDR | HTTP/2 `/nudr-dr/v2/...` | `home-net.pcap` · `http2 && ip.addr == 10.10.1.12` | `home-udr.log` · `grep -i pdu` | **N/A** | PARTIAL | — |

---

## Flow 4 — PDU Session Establishment (2/2) Home Routed

Reference: hSMF → PCF → hUPF (N4); vSMF N4 mod; AMF → UE PDU Accept.  
**TC-05:** ends at visited UPF + PDU Accept (**MEASURED** LBO). **TC-15:** full HR chain **unproven**.

| Step # | Message / procedure | Source → Destination | Protocol | PCAP + filter | Docker log + grep | TC-05 | TC-15 HR | Lab divergence note |
|--------|---------------------|----------------------|----------|---------------|-------------------|-------|----------|------------------------|
| 1 | Npcf_SMPolicyControl create | SMF → PCF | HTTP/2 `POST /npcf-smpolicycontrol/v1/sm-policies` | `visited-net.pcap` or `ipx-net.pcap` · `http2 && ip.addr == 10.10.3.25` | `home-pcf.log` · `grep -i sm-policy`; SMF log · `grep -i pcf` | **PARTIAL** | PARTIAL | TC-05 may use visited-local PCF path — confirm in pcap |
| 2 | PFCP Session Establishment (hUPF) | hSMF → hUPF | PFCP | `home-net.pcap` · `pfcp && (ip.addr == 10.10.1.23 \|\| ip.addr == 10.10.1.24)` | `home-smf.log` · `grep -i pfcp`; `home-upf.log` · `grep -i session` | **N/A** | PARTIAL | Requires HR; pool **10.45.0.0/16** |
| 3 | PFCP Session Modification (vUPF / N3) | vSMF → vUPF | PFCP | `visited-net.pcap` · `pfcp` | `visited-smf.log` · `grep -iE 'modify\|update'` | **MEASURED** | PARTIAL | LBO: single UPF programming |
| 4 | N4 / N9 path coordination (HR) | vSMF ↔ hSMF | PFCP + GTP-U **UNVERIFIED** N9 in Open5GS | `visited-net.pcap` + `home-net.pcap` · `pfcp \|\| gtp` | `visited-smf.log` · `grep -iE 'N9\|upf'`; `home-smf.log` · `grep -i upf` | **N/A** | PARTIAL | **Not MEASURED** — N9/home-UPF path open (DEF-0016) |
| 5 | Namf_Communication N1N2 transfer (PDU Accept) | AMF → UE | NGAP + NAS-5GS (`0xc2` PDU Session Establishment Accept) | `ran-net.pcap` · `nas-5gs.sm.message_type == 0xc2` | `visited-amf.log` · `grep -i 'PDU Session Establishment Accept'`; UE · `PDU session establishment successful` | **MEASURED** | PARTIAL | TC-05: Accept + `uesimtun0` **10.46.0.5** |
| 6 | User-plane check | UE → UPF GW | ICMP / IPv4 | `visited-net.pcap` · `icmp && ip.addr == 10.46.0.5` (LBO) or `10.45.x` (HR) | `ping -I uesimtun0 10.46.0.1` (script TC-11) | **MEASURED** (GW) | **N/A** until 10.45.x | DN ping 8.8.8.8 **fails** (no NAT, DEF-0015) |

---

## Architecture honesty checklist (for `pcaps/TC-XX/<ts>/NOTES.md`)

Copy into each capture’s `NOTES.md` after review:

- [ ] **Camp model:** B1 same-PLMN **001/01** — **not** true VPLMN **999/70** ([DEF-0014](../defect-log.md))
- [ ] **SEPP/N32:** **ABSENT** — dual-home SBI / proxy stand-in only ([limitations](../limitations.md))
- [ ] **User plane:** ☐ LBO **10.46** (MEASURED default) ☐ HR **10.45** (TC-15 only) ☐ unknown
- [ ] **SUCI:** `suci-0-001-01-0000-0-0-0000000001` (not `999-70`)
- [ ] **Auth+reg:** home AUSF/UDM/UDR 2xx on ipx-net
- [ ] **PDU:** session established; note SMF/UPF ownership (visited vs home)
- [ ] **Result:** PASS / FAIL / PARTIAL
- [ ] **MEASURED files:** list pcap + log paths reviewed

---

## Mermaid (reference vs lab)

```mermaid
sequenceDiagram
  participant UE
  participant gNB as gNB (ran-net)
  participant AMF as visited-AMF (ipx 10.10.3.31)
  participant AUSF as home-AUSF (ipx 10.10.3.21)
  participant UDM as home-UDM (ipx 10.10.3.22)
  participant vSMF as visited-SMF
  participant vUPF as visited-UPF
  participant hSMF as home-SMF (HR only)
  participant hUPF as home-UPF (HR only)

  Note over UE,AMF: Flow 1–2 TC-05 MEASURED (B1 camp)
  UE->>gNB: Registration + 5G-AKA (NAS)
  gNB->>AMF: NGAP
  AMF->>AUSF: Nausf (HTTP/2 ipx-net, no SEPP)
  AUSF->>UDM: Nudm auth data
  AMF->>UDM: Nudm UECM/SDM (registration)

  Note over UE,hUPF: Flow 3–4 TC-05 = LBO 10.46; TC-15 targets HR 10.45 (unproven)
  UE->>AMF: PDU Session Request
  AMF->>vSMF: Nsmf create
  vSMF->>vUPF: PFCP (MEASURED LBO)
  vSMF-->>hSMF: HR N16 (TC-15 PARTIAL only)
  hSMF-->>hUPF: PFCP (TC-15 PARTIAL only)
  AMF->>UE: PDU Accept
```

---

## Status summary

| Flow | TC-05 (golden / LBO) | TC-15 (HR attempt) |
|------|----------------------|---------------------|
| 1 Authentication | **MEASURED** | PARTIAL (same attach; HR mode does not change AKA) |
| 2 Registration | **MEASURED** (SDM subscribe: confirm in pcap if needed) | PARTIAL |
| 3 PDU (1/2) | **MEASURED** visited SMF/UPF only; hSMF **N/A** | PARTIAL — hSMF/UDM steps not MEASURED |
| 4 PDU (2/2) | **MEASURED** PDU Accept + 10.46 GW; hUPF/N9 **N/A** | **N/A** until **10.45.x** on `uesimtun0` |

**Interview sound bite:** “We **MEASURED** 5G-AKA, registration, and an LBO PDU on the golden path (TC-05). The slide’s **home-routed** PDU legs map to TC-15 wiring but are **not yet MEASURED**; B1 is same-PLMN camp, not production VPLMN selection, and we have **no SEPP**.”
