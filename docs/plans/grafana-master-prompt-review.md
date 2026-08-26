# Grafana/Prometheus master prompt — review & adaptation

**Date:** 2026-08-24  
**Scope:** User-pasted “CURSOR MASTER PROMPT — Grafana/Prometheus Dashboard Build for NTN Roaming Lab”  
**Verdict:** **PARTIAL YES** — goals align with Phase 11 and lab hard rules, but the prompt must **not** be pasted raw. It conflicts with the existing `dashboard/` stack and assumes infrastructure the lab does not have.

---

## Executive verdict

| Question | Answer |
|----------|--------|
| Does the prompt make sense conceptually? | **Yes** — domain colors, 4G/5G separation, KPI traceability, fault-domain attribution, and “no invented GSMA targets” match `accuracy.mdc` and `execution.mdc`. |
| Can it be executed as written? | **No** — wrong paths (`monitoring/` vs `dashboard/`), wrong hostnames/PLMNs, duplicate exporters, and live 4G/NF metrics the lab cannot populate today. |
| Recommended approach | **Extend `dashboard/`** — regenerate dashboards from `gen_dashboards.py`, add traceability docs, defer Open5GS scrape until V15 is verified on Ubuntu. |

---

## What aligns with lab hard rules

1. **No invented spec values** — Step 11 KPI traceability and “LAB-DEFINED” labels match Appendix C8/D4 and `accuracy.mdc`.
2. **Honest UNVERIFIED/PENDING labels** — Open5GS scrape comment, SEPP grey-out, live pcap tailer deferral are correct instincts.
3. **Domain color semantics** — HOME green, VISITED blue, IPX orange, RAN purple match existing `COLORS` in `gen_dashboards.py` and `docs/runbooks/grafana-5g-flow.md`.
4. **Fault-domain attribution (Step 10)** — Consistent with `harness/trace-validation/fault_domain.py` and master prompt Phase 11 “MTTD by fault domain”.
5. **4G/5G separation** — Sensible long-term; 4G must be **DEFERRED** until visited MME/eNB exist (TC-01/02 blocked).
6. **GSMA IR numeric targets omitted** — Correct; IR.21/IR.88/IR.77 thresholds are not in the accessible reference set.

---

## Conflicts with existing `dashboard/` implementation

| Master prompt assumes | Lab reality | Impact |
|----------------------|-------------|--------|
| New tree `monitoring/` | **`dashboard/`** already has compose, Prometheus, Grafana, exporter | Duplicate stack, broken paths, two Prometheus on :9090 |
| `flow_exporter.py` + `pcap_tailer.py` on **8000/8001** | **`pcap_flow_exporter.py` on :8010** with `/metrics`, `/ladder/latest`, call-flow HTML | Port clash with SCEF mock **:8000** (`mocks/docker-compose.yml`) |
| Hostnames `amf-home`, `amf-visited`, … | **`home-ausf`, `visited-amf`, …** per `home-network/docker-compose.yml` | Scrape targets would fail |
| VPLMN PLMN **999-70** | **B1 same-PLMN 001/01** — not production 999/70 | Misleading dashboard labels |
| `ipx-dra-sepp` with SEPP | **SEPP/N32 absent (V14)** — `ipx-sbi-proxy` stand-in | SEPP panels must stay MOCK/UNVERIFIED |
| Node graph from `nodegraph_*` synthetic gauges | **`gen_dashboards.py` uses markdown + static SVG**; nodeGraph needs ARC metrics | Synthetic node graph ≠ MEASURED topology |
| “Do not modify existing NTN dashboard file” | Dashboards are **generated** from `gen_dashboards.py` → `dashboard/grafana/dashboards/*.json` | Style source is `COLORS` + runbook, not a frozen JSON |
| `docker-compose.monitoring.yml` on `ntn-lab-net` | **`dashboard/docker-compose.yml` on `ntn-monitoring-net`** (`10.10.7.0/24`) | Network name and IP plan differ from core stacks |
| Full 4G S6a/S1AP KPI panels with live data | **No visited MME/eNB** — 4G deferred | Fake “live” 4G dashboard would violate honesty rules |
| `01-4g-roaming-flow.json` with node graph + KPIs | Not built; **DEFERRED stub** added instead | See integrated work below |

---

## UNVERIFIED or would require inventing APIs

| Item | Status | Evidence |
|------|--------|----------|
| Open5GS `/metrics` on NF **:9090** | **UNVERIFIED (V15)** | `metrics.server.port: 9090` appears in e.g. `home-network/configs/smf/open5gs-smf.yaml`, but **not scraped** — `dashboard/prometheus/prometheus.yml` defers; ports not published in NF compose |
| Open5GS NF “Up” stat panels from Prometheus | **PENDING** | Requires cross-network scrape from `ntn-monitoring-net` → `10.10.1.x` / `10.10.2.x` after V15 Ubuntu curl proof |
| `ipx-dra` / `ipx-sbi-proxy` on **:9091** | **UNVERIFIED** | No Prometheus exporter in `ipx/docker-compose.yml` |
| UERANSIM gNB/UE on **:9092** | **UNVERIFIED** | UERANSIM does not expose Prometheus in lab configs |
| `roaming_messages_total` from live `pcap_tailer.py` | **PENDING** | Live capture DEFERRED-TO-UBUNTU; post-capture path uses `pcap_flow_exporter` reload |
| GSMA IR.21/IR.88/IR.77 numeric KPI targets | **Not included** | Per prompt Step 11 — no public formula in lab reference set |
| Registration/Attach **latency pass/fail thresholds** | **LAB-DEFINED** | Formula = trace Δt; thresholds not 3GPP/GSMA-sourced |
| N32/SEPP indicator | **UNVERIFIED/MOCK** | V14 VERIFIED-ABSENT |
| Diameter timer windows for IPX attribution | **UNVERIFIED** | TS 29.272 timer defaults not hardcoded in lab |

---

## Recommended adaptation (extend `dashboard/`, not parallel `monitoring/`)

```
~/ntn-roaming-lab/
  dashboard/                          # KEEP — single monitoring stack
    docker-compose.yml
    prometheus/prometheus.yml         # add NF jobs only after V15 proof
    exporters/pcap_flow_exporter.py   # single exporter :8010 (4G+5G via tc_id/RAT later)
    grafana/gen_dashboards.py         # source of truth for JSON + colors
    grafana/dashboards/*.json         # generated; do not hand-edit
    kpi-traceability.md               # NEW — panel ↔ formula map
  scripts/extract_grafana_theme.sh    # NEW — extract hex from generated JSON
  docs/plans/grafana-master-prompt-review.md  # this file
```

**Do not create** `monitoring/` parallel tree unless deliberately migrating with a single compose entrypoint.

---

## Step mapping: master prompt → existing file or work item

| Step | Description | Status | Existing / new location |
|------|-------------|--------|-------------------------|
| 1 | Extract color theme | **DONE** | `scripts/extract_grafana_theme.sh` → `dashboard/grafana/ntn-colors-extracted.txt`; canonical palette in `gen_dashboards.py` `COLORS` |
| 2 | Directory structure | **PARTIAL** | Use `dashboard/` not `monitoring/` |
| 3 | Prometheus NF scrape | **DEFERRED** | `dashboard/prometheus/prometheus.yml` — flow-exporter only; V15 |
| 4 | Flow exporter node graph | **PARTIAL** | `pcap_flow_exporter.py` — Gauge step metrics, not `nodegraph_*`; static topology in gen script |
| 5 | PCAP tailer (live) | **DEFERRED** | Post-capture reload via `scripts/refresh-flow-dashboard.sh`; live tailer PENDING Ubuntu |
| 6 | Grafana provisioning | **DONE** | `dashboard/grafana/provisioning/` — folder **NTN Roaming** |
| 7 | 00-overview.json | **PARTIAL** | Domain stats + harness C8 + coverage — **missing** NF Up row, registration reject TS, SMS/NIDD (no metrics yet) |
| 8 | 01-4g-roaming-flow.json | **DEFERRED** | Stub `01-4g-roaming-flow.json` — text panel only, no fake KPIs |
| 9 | 02-5g-roaming-flow.json | **PARTIAL** | Ladder/table/phase stats **DONE**; master-prompt KPI rates (Reg Accept/Req %) **PENDING** pcap counters |
| 10 | Fault domain attribution | **DONE** | Markdown panel in `gen_dashboards.py`; logic in `fault_domain.py` |
| 11 | KPI traceability file | **DONE** | `dashboard/kpi-traceability.md` |
| 12 | Docker compose | **DONE** | `dashboard/docker-compose.yml` |
| 13 | Validation checklist | **DONE** | See § Validation checklist below |

---

## Validation checklist (Step 13)

### Panels backed by VERIFIED or spec-traceable formulas (denominator visible)

- Harness **C8 pass rate** = passed / executed — `MASTER_PROMPT_v2.md` Appendix C8; metric `harness_pass_rate`
- **Coverage ratio** = observed catalog steps / total — LAB-DEFINED numerator from pcap parse
- Master-prompt **Registration Success Rate** etc. — formulas cite TS 24.501/33.501 **but panels not wired until pcap counters exist** → traceability marks PENDING

### LAB-DEFINED (labeled)

- Domain observed-step counts (HOME/VISITED/IPX/RAN) — heuristic PromQL on `roaming_flow_step_total`
- Auth/PDU phase coverage %
- Latency thresholds (when added)

### UNVERIFIED / MOCK / static

- Open5GS NF Up stats — V15
- N32/SEPP — V14 absent
- Node graph with live edge weights — static SVG/markdown only
- 4G attach/S6a KPIs — no LTE core

### Live vs post-capture vs fixture

| Component | Data source |
|-----------|-------------|
| Grafana/Prometheus/flow-exporter stack | Live when Docker up |
| 5G step metrics + ladder | Post-capture `refresh-flow-dashboard.sh` or fixture (Windows pytest) |
| Harness KPIs on overview | Live when `harness/reports/*.json` present |
| Open5GS NF metrics | Not wired |
| 4G dashboard | DEFERRED stub only |

**Compliance disclaimer:** Dashboards visualize captured/simulated traces against cited formulas where available. They do **not** prove GSMA roaming compliance or IR readiness.

---

## Key conflicts before pasting prompt raw

1. **`monitoring/` vs `dashboard/`** — will duplicate and confuse provisioning.
2. **Port 8000** — already SCEF mock; flow exporter must stay **8010**.
3. **PLMN 999-70 and SEPP** — contradict B1 lab honesty and V14.
4. **Synthetic node graph as “real message counters”** — violates MEASURED vs REFERENCE rules unless fed from pcaps.
5. **“Do not modify existing dashboard JSON”** — repo uses **generated** JSON; edit `gen_dashboards.py` instead.

---

## Integrated in this pass

- `scripts/extract_grafana_theme.sh`
- `dashboard/grafana/ntn-colors-extracted.txt` (generated)
- `dashboard/kpi-traceability.md`
- Fault-domain markdown panel on 02-5g-roaming-flow
- `01-4g-roaming-flow.json` DEFERRED stub
- Regenerated `00-overview.json`, `02-5g-roaming-flow.json`

## Explicitly deferred

- `monitoring/` tree and second compose file
- Open5GS / UERANSIM / IPX Prometheus scrape jobs
- Live `pcap_tailer.py` and dual exporters 8000/8001
- Full master-prompt KPI rate panels (Reg/Auth/PDU %) until counter plumbing exists
- GSMA IR numeric targets
