# KPI traceability — Grafana dashboards

**GSMA IR.21 / IR.88 / IR.77 numeric KPI targets are not included** — they are not present in the accessible reference set for this lab. Only publicly verifiable 3GPP TS procedure definitions (numerators/denominators) or LAB-DEFINED metrics appear below.

**Legend — Verification status**

| Status | Meaning |
|--------|---------|
| VERIFIED FORMULA | Spec-traceable procedure definition; lab may still lack live counters |
| LAB MEASURED (ladder) | Rate from pcap/flow-exporter step presence for last capture (binary) |
| LAB-DEFINED | Metric shape or threshold defined by lab; not a GSMA/3GPP published target |
| UNVERIFIED/MOCK | Placeholder or component absent in lab |
| PENDING | Planned from master prompt; exporter/panel not wired |
| DEFERRED | Blocked on infrastructure (4G MME, Ubuntu live capture, V15 scrape) |

**Honesty note:** procedure success rates are **binary ladder completion** from the last
capture (attempt/success step observed), **not** multi-trial GSMA population KPIs.
Supporting gauges: `roaming_procedure_attempts_total`, `roaming_procedure_successes_total`
(also Gauges, not Counters). Rate series omitted when the attempt step is absent → Grafana
`PENDING — not wired`.

---

## 00 — Roaming Overview (`ntn-roaming-overview`)

| Panel | Formula / PromQL | 3GPP/GSMA source | Status |
|-------|------------------|------------------|--------|
| HOME (HPLMN) observed steps | `sum(roaming_flow_step_total{result="observed",phase=~"auth\|reg"})` | LAB-DEFINED domain heuristic | LAB-DEFINED |
| VISITED (VPLMN) observed steps | `sum(...{phase="pdu",result="observed"})` | LAB-DEFINED | LAB-DEFINED |
| IPX (SBI relay) observed steps | count by step on ipx-related steps | LAB-DEFINED; not DRA/S6a | LAB-DEFINED |
| RAN (NAS/NGAP) observed steps | count by step on ran-related steps | LAB-DEFINED | LAB-DEFINED — expect 0 offline |
| Flow steps observed | `sum(roaming_flow_step_total{result="observed"})` | LAB-DEFINED | LAB-DEFINED |
| Steps partial_expected | `sum(...{result="partial_expected"})` | LAB-DEFINED (LBO vs HR honesty) | LAB-DEFINED |
| Steps missing | `sum(...{result="missing"})` | LAB-DEFINED | LAB-DEFINED |
| Expected denominator | `roaming_flow_expected_steps_total{phase="all"}` | flow_catalog TC-aware (excludes N/A) | LAB-DEFINED |
| Catalog total | `sum(roaming_flow_catalog_steps_total)` | 28 steps (auth=9 reg=7 pdu=12) | LAB-DEFINED |
| Parser backend up | `up{job="flow-exporter"}` | Prometheus convention | LAB-DEFINED |
| C8 pass rate | `harness_pass_rate` = passed/executed | Appendix C8 (lab KPI appendix) | VERIFIED FORMULA |
| Harness passed / executed / files | Gauges from `harness/reports/*.json` | Appendix C8 | VERIFIED FORMULA |
| Observed / expected coverage | `roaming_flow_coverage_ratio{tc_id}` | observed / TC-expected (23 for TC-05) | LAB-DEFINED |
| Auth / Reg / PDU phase coverage % | `100 * roaming_flow_phase_coverage_ratio{phase}` | observed / TC-expected per phase | LAB-DEFINED |
| Registration Success Rate | `roaming_procedure_success_rate{procedure="registration"}` = observed(reg-7)/observed(auth-1) | TS 24.501 §5.5.1 narrative; binary ladder presence | LAB MEASURED (ladder) |
| Auth Success Rate | `roaming_procedure_success_rate{procedure="auth"}` = auth-8\|9 / auth-3\|6 | TS 33.501 §6.1.3 narrative; binary ladder presence | LAB MEASURED (ladder) |
| PDU Session Establishment Success Rate | `roaming_procedure_success_rate{procedure="pdu"}` = observed(pdu-11)/observed(pdu-1) | TS 24.501 §6.4.1 narrative; binary ladder presence | LAB MEASURED (ladder) |
| Steps by phase & result | `sum by (phase, result) (roaming_flow_step_total)` | LAB-DEFINED | LAB-DEFINED |
| Home NFs Up (master prompt) | `up{job=~"open5gs-home.*"}` | N/A | PENDING — V15 DEFERRED |
| Registration success vs reject | Accept count / Request count × 100 | TS 24.501 §5.5.1 (5G); TS 24.301 §5.5.1 (4G) | PENDING |
| SMS / NIDD success | mock/harness only | TS 29.338 / TS 29.122 | PENDING |

---

## 02 — 5G Roaming Flow (`ntn-5g-roaming-flow`)

| Panel | Formula / source | 3GPP/GSMA source | Status |
|-------|------------------|------------------|--------|
| Network domains map | Static markdown | LAB-DEFINED layout | LAB-DEFINED |
| Call-flow ladder link | `/ladder/latest` JSON | Post-capture MEASURED | LAB-DEFINED |
| Signalling steps table | `roaming_flow_step_total > 0` instant | Catalog vs pcap | LAB-DEFINED |
| AUTH / REG / PDU observed | per-phase sum observed | LAB-DEFINED | LAB-DEFINED |
| Phase observed/partial/missing | per-phase result sums | LAB-DEFINED | LAB-DEFINED |
| Coverage ratio | `roaming_flow_coverage_ratio{tc_id}` | observed / TC-expected | LAB-DEFINED |
| Expected denominator | `roaming_flow_expected_steps_total{phase="all"}` | flow_catalog TC-aware | LAB-DEFINED |
| Parser backend / steps in metrics | exporter gauges | LAB-DEFINED | LAB-DEFINED |
| Signalling by procedure | stacked bar by procedure | LAB-DEFINED | LAB-DEFINED |
| Sequence diagram legend | markdown + HTML ladder | request/response/policy colors UNVERIFIED until Ubuntu | LAB-DEFINED |
| Fault domain attribution | Evidence rules (text panel) | TS 24.501 Annex A; TS 29.500 §5.2.7; TS 29.272 §7.3 — cause codes UNVERIFIED until traced | LAB-DEFINED + citations |
| Registration Success Rate | `roaming_procedure_success_rate{procedure="registration"}` = observed(reg-7)/observed(auth-1) | TS 24.501 §5.5.1 narrative; binary ladder presence | LAB MEASURED (ladder) |
| Auth Success Rate | `roaming_procedure_success_rate{procedure="auth"}` = auth-8\|9 / auth-3\|6 | TS 33.501 §6.1.3 narrative; binary ladder presence | LAB MEASURED (ladder) |
| PDU Session Establishment Success Rate | `roaming_procedure_success_rate{procedure="pdu"}` = observed(pdu-11)/observed(pdu-1) | TS 24.501 §6.4.1 narrative; binary ladder presence | LAB MEASURED (ladder) |
| PDU establishment latency HR vs LBO | T(res) − T(req) from trace | Measurement LAB-DEFINED; threshold LAB-DEFINED | PENDING |
| Registration reject cause breakdown | 5GMM cause histogram | TS 24.501 Annex A | PENDING |
| N32/SEPP indicator | grey placeholder | SEPP absent V14 | UNVERIFIED/MOCK |
| Node graph (live edges) | `nodegraph_*` metrics | N/A | DEFERRED — static SVG only |

---

## 01 — 4G Roaming Flow (`ntn-4g-roaming-flow`) — DEFERRED

| Panel | Formula | 3GPP source | Status |
|-------|---------|-------------|--------|
| Entire dashboard | N/A — no visited MME/eNB | TS 24.301 / TS 29.272 | DEFERRED |
| Attach success rate | Attach Accept / Attach Request × 100 | TS 24.301 §5.5.1 | DEFERRED |
| S6a auth / UL success | Diameter AIR/AIA, ULR/ULA | TS 29.272 §7.2–7.3 | DEFERRED |
| PDN connectivity success | Activate default bearer accept / PDN req | TS 24.301 §6.5.1 | DEFERRED |
| SGd SMS delivery | SMS report / attempts | TS 29.338; TS 23.040 | DEFERRED |
| Roaming reject EMM causes | Annex A breakdown | TS 24.301 Annex A | DEFERRED |

---

## Master prompt components not duplicated

| Component | Reason |
|-----------|--------|
| `monitoring/exporters/pcap_tailer.py` | Live tail DEFERRED-TO-UBUNTU; use post-capture reload |
| Dual flow exporters :8000/:8001 | Conflicts with SCEF :8000; single `:8010` exporter |
| Open5GS scrape `amf-home:9090` | Wrong hostnames; V15 UNVERIFIED; not published in compose |
| GSMA IR readiness traffic light | Thresholds config-only in C8; not IR-sourced |
