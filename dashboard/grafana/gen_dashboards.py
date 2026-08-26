#!/usr/bin/env python3
"""Generate Grafana dashboard JSON from flow_catalog (run: python gen_dashboards.py)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "dashboard" / "exporters"))

from flow_catalog import (  # noqa: E402
    CATALOG_STEPS_TOTAL,
    FLOW_STEPS,
    catalog_step_counts,
    expected_step_counts,
    steps_by_phase,
    total_expected_steps,
)

DS = {"type": "prometheus", "uid": "prometheus"}

COLORS = {
    "home": "#2E7D32",
    "visited": "#1565C0",
    "ipx": "#EF6C00",
    "ran": "#6A1B9A",
    "auth": "#FF9800",
    "reg": "#2E7D32",
    "pdu": "#1565C0",
    "observed": "#43A047",
    "partial": "#FBC02D",
    "missing": "#E53935",
}

PHASE_ROW_COLOR = {"auth": "#E65100", "reg": "#2E7D32", "pdu": "#1565C0"}

TITLE_MARKER = "v11 panel-fix"

# Honest panel copy: binary ladder presence ≠ multi-trial GSMA population KPI.
_HONESTY = (
    "MEASURED procedure completion from last capture ladder "
    "(1=Accept/success step seen / Request/attempt step seen). "
    "Not a multi-trial GSMA KPI. Binary presence ≠ population statistics."
)

PROCEDURE_SUCCESS_KPIS: list[tuple[str, str, str, int]] = [
    (
        "Registration Success Rate",
        '100 * roaming_procedure_success_rate{procedure="registration"}',
        (
            "3GPP TS 24.501 §5.5.1: Registration Accept (reg-7) / Registration Request (auth-1). "
            + _HONESTY
        ),
        44,
    ),
    (
        "Auth Success Rate",
        '100 * roaming_procedure_success_rate{procedure="auth"}',
        (
            "3GPP TS 33.501 §6.1.3: Nausf confirm (auth-8) or SMC (auth-9) / "
            "Nausf create (auth-3) or 5G-AKA challenge (auth-6). "
            + _HONESTY
        ),
        45,
    ),
    (
        "PDU Session Establishment Success Rate",
        '100 * roaming_procedure_success_rate{procedure="pdu"}',
        (
            "3GPP TS 24.501 §6.4.1: PDU Session Establishment Accept (pdu-11) / "
            "Request (pdu-1). "
            + _HONESTY
        ),
        46,
    ),
]


def _procedure_success_panels(y: int, *, id_offset: int = 0) -> tuple[list[dict], int]:
    """Row + three gauge panels for ladder-derived procedure completion rates."""
    panels: list[dict] = [_row("3GPP procedure success rates (MEASURED ladder)", y)]
    y += 1
    for idx, (title, expr, desc, base_pid) in enumerate(PROCEDURE_SUCCESS_KPIS):
        panels.append(
            _gauge(
                title,
                expr,
                idx * 8,
                y,
                8,
                5,
                base_pid + id_offset,
                100,
                description=desc,
                no_value="PENDING — run refresh-flow-dashboard",
                unit="none",
            )
        )
    y += 5
    return panels, y


def _row(title: str, y: int, color: str = "") -> dict:
    panel: dict = {
        "type": "row",
        "title": title,
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y},
        "id": hash(title) % 9000 + 100,
        "panels": [],
    }
    if color:
        panel["title"] = title
    return panel


def _stat(
    title: str,
    expr: str,
    x: int,
    y: int,
    w: int,
    h: int,
    color: str,
    pid: int,
    *,
    description: str = "",
    no_value: str = "0",
) -> dict:
    panel: dict = {
        "type": "stat",
        "title": title,
        "id": pid,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "datasource": DS,
        "targets": [{"expr": expr, "legendFormat": title, "refId": "A"}],
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "fixed", "fixedColor": color},
                "noValue": no_value,
                "thresholds": {"mode": "absolute", "steps": [{"color": color, "value": None}]},
            }
        },
        "options": {
            "colorMode": "background",
            "graphMode": "none",
            "textMode": "value_and_name",
            "reduceOptions": {"calcs": ["lastNotNull"]},
        },
    }
    if description:
        panel["description"] = description
    return panel


def _gauge(
    title: str,
    expr: str,
    x: int,
    y: int,
    w: int,
    h: int,
    pid: int,
    max_val: float = 100,
    *,
    description: str = "",
    no_value: str = "0",
    unit: str | None = None,
) -> dict:
    defaults: dict = {
        "min": 0,
        "max": max_val,
        "noValue": no_value,
        "thresholds": {
            "mode": "absolute",
            "steps": [
                {"color": COLORS["missing"], "value": None},
                {"color": COLORS["partial"], "value": 0.5 if max_val <= 1 else 50},
                {"color": COLORS["observed"], "value": 0.8 if max_val <= 1 else 80},
            ],
        },
    }
    if unit == "percentunit" or max_val <= 1:
        defaults["unit"] = "percentunit"
    elif unit:
        defaults["unit"] = unit
    panel: dict = {
        "type": "gauge",
        "title": title,
        "id": pid,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "datasource": DS,
        "targets": [{"expr": expr, "refId": "A"}],
        "fieldConfig": {"defaults": defaults},
        "options": {"reduceOptions": {"calcs": ["lastNotNull"]}, "showThresholdMarkers": True},
    }
    if description:
        panel["description"] = description
    return panel


def gen_overview() -> dict:
    y = 0
    catalog = catalog_step_counts()
    tc05_expected = expected_step_counts("TC-05")
    tc05_total = total_expected_steps("TC-05")
    panels: list[dict] = [
        {
            "type": "text",
            "title": "NTN Roaming Lab Overview",
            "id": 1,
            "gridPos": {"h": 5, "w": 24, "x": 0, "y": y},
            "options": {
                "mode": "markdown",
                "content": (
                    "## NTN Roaming Lab — monitoring overview\n\n"
                    "**Domain colors:** HOME `#2E7D32` · VISITED `#1565C0` · IPX `#EF6C00` · RAN `#6A1B9A`\n\n"
                    f"**Catalog:** {CATALOG_STEPS_TOTAL} steps (auth={catalog['auth']}, reg={catalog['reg']}, "
                    f"pdu={catalog['pdu']}). **Active capture (from exporter tc_id):** expected "
                    f"denominator via `roaming_flow_expected_steps_total{{phase=\"all\"}}` "
                    f"(TC-05 reference = {tc05_total}, excludes N/A HR-only pdu steps).\n\n"
                    "**B1 same-PLMN camp (001/01)** — not production VPLMN 999/70. **SEPP/N32 absent.** "
                    "Open **[02 — 5G Roaming Flow](/d/ntn-5g-roaming-flow)** for post-capture ladder.\n\n"
                    "Thresholds: green=observed · yellow=partial_expected · red=missing"
                ),
            },
        }
    ]
    y += 5

    # Domain stat row — prefer step{domain=} count (truth), else domain gauge.
    # noValue is "—" (not "0") so a missing scrape is not confused with zero observed.
    # Prefer count first: PromQL `or` ignores the RHS when LHS series exists (even if 0).
    _domain_expr = (
        'count(roaming_flow_step_total{{result="observed",domain="{d}"}}) '
        'or on() sum(roaming_flow_domain_observed_total{{domain="{d}"}})'
    )
    domain_stats = [
        (
            "HOME (HPLMN)",
            _domain_expr.format(d="home"),
            COLORS["home"],
            0,
            "Observed ladder steps with domain=home (UDM/AUSF/UDR/PCF path). "
            "Uses count(step_total{domain=}) else roaming_flow_domain_observed_total.",
        ),
        (
            "VISITED (VPLMN)",
            _domain_expr.format(d="visited"),
            COLORS["visited"],
            6,
            "Observed ladder steps with domain=visited (vSMF/vUPF path).",
        ),
        (
            "IPX (SBI relay)",
            _domain_expr.format(d="ipx"),
            COLORS["ipx"],
            12,
            "Observed ladder steps with domain=ipx — SBI relay, not SEPP/N32.",
        ),
        (
            "RAN (NAS/NGAP)",
            _domain_expr.format(d="ran"),
            COLORS["ran"],
            18,
            "Observed ladder steps with domain=ran (NAS/NGAP). "
            "True 0 means this capture has no ran-domain steps observed "
            "(often missing ran-net.pcap / DEFERRED-TO-UBUNTU), not a green KPI.",
        ),
    ]
    for title, expr, color, x, desc in domain_stats:
        panels.append(
            _stat(
                title,
                expr,
                x,
                y,
                6,
                4,
                color,
                10 + x,
                description=desc,
                no_value="—",
            )
        )
    y += 4

    panels.append(_row("Flow Completeness Debug View", y))
    y += 1
    debug_stats = [
        (
            "Flow steps observed",
            'sum(roaming_flow_step_total{result="observed"})',
            COLORS["observed"],
            0,
            5,
            f"Numerator for coverage ratio. Active capture denominator from exporter "
            f"tc_id via roaming_flow_expected_steps_total (TC-05 reference={tc05_total}).",
        ),
        (
            "Steps partial_expected",
            'sum(roaming_flow_step_total{result="partial_expected"})',
            COLORS["partial"],
            5,
            5,
            "PARTIAL/N/A catalog honesty — not counted as observed.",
        ),
        (
            "Steps missing",
            'sum(roaming_flow_step_total{result="missing"})',
            COLORS["missing"],
            10,
            5,
            f"MEASURED steps not seen in pcap. observed+partial+missing={CATALOG_STEPS_TOTAL} catalog steps.",
        ),
        (
            "Expected denominator",
            'roaming_flow_expected_steps_total{phase="all"}',
            COLORS["visited"],
            15,
            5,
            f"TC-aware expected steps (excludes N/A). TC-05={tc05_total}, catalog={CATALOG_STEPS_TOTAL}.",
        ),
        (
            "Catalog total",
            "sum(roaming_flow_catalog_steps_total)",
            COLORS["ipx"],
            20,
            4,
            f"Full catalog per flow_catalog.py: auth={catalog['auth']} reg={catalog['reg']} pdu={catalog['pdu']}.",
        ),
    ]
    for i, (title, expr, color, x, w, desc) in enumerate(debug_stats):
        panels.append(_stat(title, expr, x, y, w, 4, color, 20 + i, description=desc))
    y += 4

    panels.append(_row("Health & harness KPIs", y))
    y += 1
    panels.append(
        _stat(
            "Parser backend up",
            'up{job="flow-exporter"}',
            0,
            y,
            6,
            4,
            COLORS["visited"],
            28,
            description="Prometheus scrape target for pcap_flow_exporter :8010.",
        )
    )
    harness = [
        ("C8 pass rate", "harness_pass_rate", 6, 4),
        ("Harness passed", "harness_reports_passed_total", 12, 4),
        ("Harness executed", "harness_reports_executed_total", 16, 4),
        ("Report files", "harness_reports_files_total", 20, 4),
    ]
    for i, (title, expr, x, w) in enumerate(harness):
        panels.append(_stat(title, expr, x, y, w, 4, COLORS["home"], 30 + i))
    y += 4

    phase_cov_desc = (
        "observed / TC-expected × 100 from exporter. "
        f"TC-05 denominators: auth={tc05_expected['auth']}, reg={tc05_expected['reg']}, "
        f"pdu={tc05_expected['pdu']} (excludes N/A HR-only steps)."
    )
    panels.append(
        _gauge(
            "Observed / expected coverage",
            "roaming_flow_coverage_ratio",
            0,
            y,
            6,
            5,
            40,
            1.0,
            description=(
                f"observed / TC-expected ({tc05_total} for TC-05). "
                "Metric from pcap_flow_exporter; no fallback zero."
            ),
            no_value="PENDING — run refresh-flow-dashboard",
        )
    )
    pending_cov = "PENDING — run refresh-flow-dashboard"
    panels.append(
        _gauge(
            "Auth phase coverage %",
            '100 * roaming_flow_phase_coverage_ratio{phase="auth"}',
            6,
            y,
            6,
            5,
            41,
            100,
            description=phase_cov_desc,
            no_value=pending_cov,
            unit="none",
        )
    )
    panels.append(
        _gauge(
            "Reg phase coverage %",
            '100 * roaming_flow_phase_coverage_ratio{phase="reg"}',
            12,
            y,
            6,
            5,
            43,
            100,
            description=phase_cov_desc,
            no_value=pending_cov,
            unit="none",
        )
    )
    panels.append(
        _gauge(
            "PDU phase coverage %",
            '100 * roaming_flow_phase_coverage_ratio{phase="pdu"}',
            18,
            y,
            6,
            5,
            42,
            100,
            description=phase_cov_desc,
            no_value=pending_cov,
            unit="none",
        )
    )
    y += 5

    success_panels, y = _procedure_success_panels(y, id_offset=0)
    panels.extend(success_panels)

    panels.append({
        "type": "bargauge",
        "title": "Steps by phase & result",
        "id": 50,
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": y},
        "datasource": DS,
        "targets": [{"expr": "sum by (phase, result) (roaming_flow_step_total)", "legendFormat": "{{phase}} {{result}}", "refId": "A"}],
        "fieldConfig": {
            "defaults": {
                "noValue": "0",
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": COLORS["missing"], "value": None},
                        {"color": COLORS["partial"], "value": 1},
                        {"color": COLORS["observed"], "value": 3},
                    ],
                },
                "color": {"mode": "thresholds"},
            }
        },
        "options": {"displayMode": "gradient", "orientation": "horizontal", "reduceOptions": {"calcs": ["lastNotNull"]}},
    })

    return {
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "id": None,
        "links": [{"title": "5G Roaming Flow", "url": "/d/ntn-5g-roaming-flow", "type": "dashboard"}],
        "liveNow": False,
        "panels": panels,
        "refresh": "10s",
        "schemaVersion": 39,
        "style": "dark",
        "tags": ["5g", "roaming", "ntn-lab", "overview"],
        "templating": {"list": []},
        "time": {"from": "now-15m", "to": "now"},
        "timezone": "",
        "title": f"00 — Roaming Overview ({TITLE_MARKER})",
        "uid": "ntn-roaming-overview",
        "version": 11,
        "description": (
            "Colorful domain overview. HOME #2E7D32, VISITED #1565C0, IPX #EF6C00, RAN #6A1B9A. "
            "Harness C8 from harness/reports/*.json via flow-exporter. B1/no SEPP honesty. "
            "Procedure success rates from ladder step presence (not multi-trial GSMA KPIs)."
        ),
    }


def _phase_stats(phase: str, y: int, base_id: int) -> tuple[list[dict], int]:
    panels: list[dict] = []
    color = PHASE_ROW_COLOR[phase]
    panels.append(_row(f"Phase: {phase.upper()} — observed / partial / missing", y, color))
    y += 1
    stats = [
        ("observed", COLORS["observed"]),
        ("partial_expected", COLORS["partial"]),
        ("missing", COLORS["missing"]),
    ]
    for i, (result, c) in enumerate(stats):
        panels.append(_stat(
            f"{phase} {result}",
            f'sum(roaming_flow_step_total{{phase="{phase}",result="{result}"}})',
            i * 8, y, 8, 3, c, base_id + i,
        ))
    y += 3
    return panels, y


IFRAME_BASE = os.environ.get("GRAFANA_IFRAME_BASE", "http://127.0.0.1:8010")


def _topology_html() -> str:
    """Static colorful topology (nodeGraph requires ARC metrics — not available here)."""
    return f"""
<div style="font-family:Segoe UI,sans-serif;padding:12px;background:#1a1d23;border-radius:8px">
  <svg viewBox="0 0 900 220" width="100%" height="220">
    <defs>
      <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
        <path d="M0,0 L6,3 L0,6 Z" fill="#90A4AE"/>
      </marker>
    </defs>
    <rect x="10" y="10" width="880" height="50" fill="{COLORS["visited"]}" opacity="0.25" rx="6"/>
    <text x="20" y="35" fill="{COLORS["visited"]}" font-weight="700">VPLMN</text>
    <rect x="10" y="70" width="880" height="50" fill="{COLORS["home"]}" opacity="0.25" rx="6"/>
    <text x="20" y="95" fill="{COLORS["home"]}" font-weight="700">HPLMN</text>
    <circle cx="120" cy="160" r="28" fill="{COLORS["ran"]}"/><text x="120" y="165" fill="#fff" text-anchor="middle" font-size="12">UE</text>
    <circle cx="280" cy="160" r="28" fill="{COLORS["visited"]}"/><text x="280" y="165" fill="#fff" text-anchor="middle" font-size="11">vAMF</text>
    <circle cx="440" cy="35" r="26" fill="{COLORS["visited"]}"/><text x="440" y="40" fill="#fff" text-anchor="middle" font-size="10">vSMF</text>
    <circle cx="580" cy="35" r="26" fill="{COLORS["visited"]}"/><text x="580" y="40" fill="#fff" text-anchor="middle" font-size="10">vUPF</text>
    <circle cx="440" cy="95" r="26" fill="{COLORS["home"]}"/><text x="440" y="100" fill="#fff" text-anchor="middle" font-size="10">AUSF</text>
    <circle cx="580" cy="95" r="26" fill="{COLORS["home"]}"/><text x="580" y="100" fill="#fff" text-anchor="middle" font-size="10">UDM</text>
    <circle cx="720" cy="95" r="26" fill="{COLORS["home"]}"/><text x="720" y="100" fill="#fff" text-anchor="middle" font-size="10">hSMF</text>
    <line x1="148" y1="160" x2="252" y2="160" stroke="#90A4AE" marker-end="url(#arr)"/>
    <line x1="308" y1="145" x2="420" y2="55" stroke="{COLORS["ipx"]}" marker-end="url(#arr)"/>
    <line x1="308" y1="150" x2="414" y2="95" stroke="{COLORS["ipx"]}" marker-end="url(#arr)"/>
    <line x1="466" y1="35" x2="554" y2="35" stroke="{COLORS["visited"]}" marker-end="url(#arr)"/>
    <line x1="466" y1="95" x2="554" y2="95" stroke="{COLORS["home"]}" marker-end="url(#arr)"/>
    <line x1="466" y1="55" x2="694" y2="85" stroke="{COLORS["ipx"]}" stroke-dasharray="6,4" marker-end="url(#arr)"/>
  </svg>
  <p style="color:#B0BEC5;font-size:12px;margin:8px 0 0">Solid = LBO MEASURED · Dashed = HR PARTIAL (TC-15). IPX SBI orange — not SEPP/N32.</p>
</div>
"""


def _domain_banner_html() -> str:
    c = COLORS
    return (
        f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;padding:4px;">'
        f'<div style="background:{c["visited"]};color:#fff;padding:22px 8px;text-align:center;'
        f'border-radius:10px;font-size:17px;font-weight:700;box-shadow:0 3px 10px rgba(0,0,0,.4);">'
        f'VISITED<br><span style="font-size:12px;font-weight:500">vAMF · vSMF · vUPF</span></div>'
        f'<div style="background:{c["home"]};color:#fff;padding:22px 8px;text-align:center;'
        f'border-radius:10px;font-size:17px;font-weight:700;box-shadow:0 3px 10px rgba(0,0,0,.4);">'
        f'HOME<br><span style="font-size:12px;font-weight:500">AUSF · UDM · UDR · PCF</span></div>'
        f'<div style="background:{c["ipx"]};color:#fff;padding:22px 8px;text-align:center;'
        f'border-radius:10px;font-size:17px;font-weight:700;box-shadow:0 3px 10px rgba(0,0,0,.4);">'
        f'IPX<br><span style="font-size:12px;font-weight:500">SBI relay · no N32</span></div>'
        f'<div style="background:{c["ran"]};color:#fff;padding:22px 8px;text-align:center;'
        f'border-radius:10px;font-size:17px;font-weight:700;box-shadow:0 3px 10px rgba(0,0,0,.4);">'
        f'RAN<br><span style="font-size:12px;font-weight:500">NAS · NGAP · ran-net</span></div>'
        f"</div>"
    )


def _fault_domain_markdown() -> str:
    """Fault-domain attribution guide (master prompt Step 10; harness/trace-validation/fault_domain.py)."""
    return (
        "## Fault domain attribution\n\n"
        "Use multi-point capture evidence before assigning blame. "
        "Implementation: `harness/trace-validation/fault_domain.py`.\n\n"
        "| Domain | When to attribute |\n"
        "|--------|-------------------|\n"
        "| **HOME** | Cause or failure response originates from HSS/UDM/AUSF/UDR "
        "(e.g. 5xx SBI from home NF, Diameter answer from HSS) |\n"
        "| **VISITED** | Local AMF/MME rejects before home is reached; attach succeeds "
        "through auth but fails in visited PDU path |\n"
        "| **IPX** | No response within Diameter/HTTP2 timer window, or transport "
        "failure at DRA/SBI proxy hop — **not SEPP/N32 (absent V14)** |\n"
        "| **RAN/UE** | Failure before NAS reaches core (RRC/NGAP/S1AP establishment) |\n"
        "| **NTN impairment** | Same cause codes as above but time-correlated with active "
        "netem profile on ran-net — UNVERIFIED timer correlation until measured |\n\n"
        "**Cause code references (definitions only — lab must trace MEASURED codes):**\n"
        "- 5GMM causes: 3GPP TS 24.501 Annex A — UNVERIFIED against live pcaps until TC run\n"
        "- EMM causes: 3GPP TS 24.301 Annex A — DEFERRED (no LTE MME)\n"
        "- Diameter Experimental-Result: TS 29.272 §7.3 — see verification-register V1/V2\n"
        "- HTTP problem details: TS 29.500 §5.2.7 — UNVERIFIED until SBI error pcaps parsed\n\n"
        "> **INDETERMINATE** when evidence is insufficient — never guess."
    )


def _markdown_panel(pid: int, title: str, y: int, h: int, content: str, w: int = 24, x: int = 0) -> dict:
    """Markdown text panel — Grafana renders this reliably (unlike raw HTML/iframes)."""
    return {
        "type": "text",
        "title": title,
        "id": pid,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "options": {"mode": "markdown", "content": content},
    }


def _html_panel(pid: int, title: str, y: int, h: int, content: str, w: int = 24, x: int = 0) -> dict:
    """Deprecated: Grafana often shows HTML as raw text — prefer _markdown_panel."""
    return _markdown_panel(pid, title, y, h, content, w, x)


def _signalling_table_panel(y: int, h: int = 14, w: int = 24, x: int = 0, pid: int = 230) -> dict:
    return {
        "type": "table",
        "title": "Signalling steps (Auth → Reg → PDU)",
        "id": pid,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "datasource": DS,
        "targets": [{"expr": "roaming_flow_step_total > 0", "format": "table", "instant": True, "refId": "A"}],
        "transformations": [
            {"id": "labelsToFields", "options": {"mode": "columns"}},
            {
                "id": "organize",
                "options": {
                    "excludeByName": {"Time": True, "Value": True, "__name__": True, "instance": True, "job": True},
                    "renameByName": {"phase": "Phase", "step": "Step", "procedure": "Signalling message", "result": "Status"},
                    "indexByName": {"Phase": 0, "Step": 1, "Signalling message": 2, "Status": 3},
                },
            },
            {"id": "sortBy", "options": {"fields": {}, "sort": [{"field": "Step"}]}},
        ],
        "fieldConfig": {
            "defaults": {"custom": {"align": "auto", "filterable": True}},
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "Status"},
                    "properties": [
                        {"id": "custom.cellOptions", "value": {"type": "color-background", "mode": "basic"}},
                        {
                            "id": "mappings",
                            "value": [
                                {"type": "value", "options": {"observed": {"text": "OBSERVED", "color": COLORS["observed"]}}},
                                {"type": "value", "options": {"partial_expected": {"text": "PARTIAL", "color": COLORS["partial"]}}},
                                {"type": "value", "options": {"missing": {"text": "MISSING", "color": COLORS["missing"]}}},
                            ],
                        },
                    ],
                },
            ],
        },
    }


def _big_stat(title: str, expr: str, x: int, y: int, w: int, color: str, pid: int) -> dict:
    p = _stat(title, expr, x, y, w, 5, color, pid)
    p["fieldConfig"]["defaults"]["thresholds"] = {
        "mode": "absolute",
        "steps": [{"color": color, "value": None}],
    }
    p["options"]["text"] = {"titleSize": 14, "valueSize": 36}
    p["options"]["colorMode"] = "background"
    return p


def gen_flow_dashboard() -> dict:
    y = 0
    panels: list[dict] = []
    ladder_url = f"{IFRAME_BASE}/static/roaming-callflow.html?api={IFRAME_BASE}/ladder/latest"

    panels.append(_markdown_panel(
        1, "Network domains", y, 4,
        (
            "### 5G SA Roaming — domain map\n\n"
            "| | **VISITED (VPLMN)** | **HOME (HPLMN)** | **IPX** | **RAN** |\n"
            "|:---:|:---:|:---:|:---:|:---:|\n"
            "| NF | vAMF · vSMF · vUPF | AUSF · UDM · UDR · PCF | SBI proxy | gNB · UE |\n"
            "| Color | `#1565C0` blue | `#2E7D32` green | `#EF6C00` orange | `#6A1B9A` purple |\n"
        ),
    ))
    y += 4

    panels.append(_markdown_panel(
        2, "Signalling call-flow (open beside Grafana)", y, 6,
        (
            "## Live sequence diagram\n\n"
            f"**[Open call-flow ladder in new tab ↗]({ladder_url})**\n\n"
            "- Auto-refreshes every 10s from `flow-exporter /ladder/latest`\n"
            "- **Step status (arrow border):** green = **observed** · yellow = **partial_expected** · red = **missing**\n"
            "- **Message role colors (when wired on Ubuntu):** 🔴 red = **request** · "
            "🟢 green = **success response** · 🟠 orange = **intermediate/policy** (PCF/NRF hops)\n"
            "- **B1 same-PLMN 001/01** · **No SEPP/N32** · TC-05 LBO MEASURED\n\n"
            "> Grafana cannot embed iframes safely — use the link above for the full Auth → Reg → PDU ladder.\n"
        ),
    ))
    y += 6

    panels.append(_signalling_table_panel(y, h=14))
    y += 14

    panels.append(_markdown_panel(3, "Fault domain attribution", y, 10, _fault_domain_markdown()))
    y += 10

    panels.append(_row("Phase totals", y))
    y += 1
    panels.extend([
        _big_stat("AUTH observed", 'sum(roaming_flow_step_total{phase="auth",result="observed"})', 0, y, 8, COLORS["auth"], 101),
        _big_stat("REG observed", 'sum(roaming_flow_step_total{phase="reg",result="observed"})', 8, y, 8, COLORS["reg"], 102),
        _big_stat("PDU observed", 'sum(roaming_flow_step_total{phase="pdu",result="observed"})', 16, y, 8, COLORS["pdu"], 103),
    ])
    y += 5

    for phase in ("auth", "reg", "pdu"):
        phase_panels, y = _phase_stats(phase, y, {"auth": 110, "reg": 120, "pdu": 130}[phase])
        panels.extend(phase_panels)

    panels.append(_row("Coverage", y))
    y += 1
    tc05_total = total_expected_steps("TC-05")
    panels.extend([
        _gauge(
            "Coverage ratio",
            "roaming_flow_coverage_ratio",
            0,
            y,
            6,
            5,
            200,
            1.0,
            description=f"observed / TC-expected ({tc05_total} for TC-05). Exporter metric — no fallback zero.",
            no_value="PENDING — run refresh-flow-dashboard",
        ),
        _stat(
            "Parser backend",
            "count(flow_exporter_parser_info == 1)",
            6,
            y,
            6,
            5,
            COLORS["ipx"],
            915,
            no_value="PENDING",
        ),
        _stat(
            "Expected denominator",
            'roaming_flow_expected_steps_total{phase="all"}',
            12,
            y,
            6,
            5,
            COLORS["visited"],
            916,
            description=f"TC-aware expected steps; catalog total={CATALOG_STEPS_TOTAL}.",
        ),
        _stat(
            "Steps in metrics",
            "count(roaming_flow_step_total)",
            18,
            y,
            6,
            5,
            COLORS["home"],
            917,
            description=f"Should equal catalog total {CATALOG_STEPS_TOTAL} (one result label per step; cleared on reload).",
        ),
    ])
    y += 5

    success_panels, y = _procedure_success_panels(y, id_offset=180)
    panels.extend(success_panels)

    panels.append({
        "type": "barchart",
        "title": "Signalling by procedure",
        "id": 210,
        "gridPos": {"h": 8, "w": 24, "x": 0, "y": y},
        "datasource": DS,
        "targets": [{"expr": "sum by (procedure, result) (roaming_flow_step_total)", "legendFormat": "{{procedure}}", "refId": "A"}],
        "fieldConfig": {
            "defaults": {"noValue": "0", "custom": {"stacking": {"mode": "normal"}}},
            "overrides": [
                {"matcher": {"id": "byName", "options": "observed"}, "properties": [{"id": "color", "value": {"fixedColor": COLORS["observed"], "mode": "fixed"}}]},
                {"matcher": {"id": "byName", "options": "partial_expected"}, "properties": [{"id": "color", "value": {"fixedColor": COLORS["partial"], "mode": "fixed"}}]},
                {"matcher": {"id": "byName", "options": "missing"}, "properties": [{"id": "color", "value": {"fixedColor": COLORS["missing"], "mode": "fixed"}}]},
            ],
        },
    })
    y += 8

    return {
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 1,
        "id": None,
        "links": [
            {"title": "▶ OPEN CALL-FLOW LADDER", "url": ladder_url, "type": "link", "icon": "external link", "targetBlank": True},
            {"title": "Overview", "url": "/d/ntn-roaming-overview", "type": "dashboard"},
        ],
        "liveNow": False,
        "panels": panels,
        "refresh": "10s",
        "schemaVersion": 39,
        "style": "dark",
        "tags": ["5g", "roaming", "ntn-lab"],
        "templating": {"list": []},
        "time": {"from": "now-15m", "to": "now"},
        "timezone": "",
        "title": f"02 — 5G Roaming Flow ({TITLE_MARKER})",
        "uid": "ntn-5g-roaming-flow",
        "version": 16,
        "description": (
            "Post-capture ladder from pcap_flow_exporter. VPLMN #1565C0, HPLMN #2E7D32, IPX #EF6C00, RAN #6A1B9A. "
            "Phase rows: Auth #FF9800, Reg #2E7D32, PDU #1565C0. Thresholds: green=observed, yellow=partial, red=missing. "
            "Procedure success rates from ladder step presence (not multi-trial GSMA KPIs)."
        ),
    }


def gen_4g_deferred_dashboard() -> dict:
    """DEFERRED stub — no visited MME/eNB; TC-01/02 blocked."""
    return {
        "annotations": {"list": []},
        "editable": True,
        "fiscalYearStartMonth": 0,
        "graphTooltip": 0,
        "id": None,
        "links": [{"title": "5G Roaming Flow (live path)", "url": "/d/ntn-5g-roaming-flow", "type": "dashboard"}],
        "liveNow": False,
        "panels": [
            _markdown_panel(
                1,
                "DEFERRED — no LTE MME in lab",
                0,
                12,
                (
                    "## 01 — 4G Roaming Flow — **DEFERRED**\n\n"
                    "This lab has **no visited MME or eNB**. TC-01/TC-02 (LTE attach/S6a) are **blocked**.\n\n"
                    "Do **not** interpret empty or stub panels as passing 4G IREG coverage.\n\n"
                    "**When LTE is added**, panels should cite:\n"
                    "- Attach success: TS 24.301 §5.5.1\n"
                    "- S6a AIR/AIA, ULR/ULA: TS 29.272 §7.2–7.3\n"
                    "- PDN connectivity: TS 24.301 §6.5.1\n"
                    "- SGd SMS: TS 29.338 / TS 23.040\n\n"
                    "See `dashboard/kpi-traceability.md` and `docs/plans/grafana-master-prompt-review.md`.\n\n"
                    "Use **[02 — 5G Roaming Flow](/d/ntn-5g-roaming-flow)** for the active B1 same-PLMN path."
                ),
            ),
        ],
        "refresh": "",
        "schemaVersion": 39,
        "style": "dark",
        "tags": ["4g", "deferred", "ntn-lab"],
        "templating": {"list": []},
        "time": {"from": "now-6h", "to": "now"},
        "timezone": "",
        "title": "01 — 4G Roaming Flow (DEFERRED — no LTE MME)",
        "uid": "ntn-4g-roaming-flow",
        "version": 1,
        "description": (
            "DEFERRED stub only. No fake node graphs or live KPI claims. "
            "4G blocked until visited MME/eNB exist. KPI traceability in dashboard/kpi-traceability.md."
        ),
    }


def main() -> None:
    out_dir = Path(__file__).resolve().parent / "dashboards"
    out_dir.mkdir(parents=True, exist_ok=True)
    dashboards = [
        ("00-overview.json", gen_overview()),
        ("01-4g-roaming-flow.json", gen_4g_deferred_dashboard()),
        ("02-5g-roaming-flow.json", gen_flow_dashboard()),
    ]
    for name, doc in dashboards:
        path = out_dir / name
        path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
