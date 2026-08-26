"""Offline checks for generated Grafana 00-overview dashboard JSON."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OVERVIEW = ROOT / "dashboard" / "grafana" / "dashboards" / "00-overview.json"
FLOW = ROOT / "dashboard" / "grafana" / "dashboards" / "02-5g-roaming-flow.json"

TITLE_MARKER = "(v11 panel-fix)"


def _panel_titles(doc: dict) -> set[str]:
    titles: set[str] = set()
    for panel in doc.get("panels") or []:
        if panel.get("type") == "row":
            titles.add(panel.get("title", ""))
        titles.add(panel.get("title", ""))
    return titles


def _gauge_exprs(doc: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for panel in doc.get("panels") or []:
        if panel.get("type") == "gauge":
            targets = panel.get("targets") or []
            if targets:
                out[panel.get("title", "")] = targets[0].get("expr", "")
    return out


def _stat_exprs(doc: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for panel in doc.get("panels") or []:
        if panel.get("type") == "stat":
            targets = panel.get("targets") or []
            if targets:
                out[panel.get("title", "")] = targets[0].get("expr", "")
    return out


def _all_exprs(doc: dict) -> list[str]:
    exprs: list[str] = []
    for panel in doc.get("panels") or []:
        for target in panel.get("targets") or []:
            expr = target.get("expr") or ""
            if expr:
                exprs.append(expr)
    return exprs


def test_overview_has_debug_row_and_exporter_coverage_gauges() -> None:
    doc = json.loads(OVERVIEW.read_text(encoding="utf-8"))
    assert TITLE_MARKER in doc.get("title", "")
    titles = _panel_titles(doc)
    assert "Flow Completeness Debug View" in titles
    assert "3GPP procedure success rates (MEASURED ladder)" in titles
    assert "3GPP procedure success rates (UNVERIFIED)" not in titles
    assert "Observed / catalog coverage" not in titles

    # Header must not hardcode a wrong TC id (e.g. TC-06 while viewing TC-05).
    md = next(
        p["options"]["content"]
        for p in doc["panels"]
        if p.get("type") == "text" and "overview" in (p.get("title") or "").lower()
    )
    assert "TC-06 expected denominator" not in md
    assert "TC-06" not in md
    assert "Active capture (from exporter tc_id)" in md

    gauges = _gauge_exprs(doc)
    assert gauges["Observed / expected coverage"] == "roaming_flow_coverage_ratio"
    assert "roaming_flow_phase_coverage_ratio" in gauges["Auth phase coverage %"]
    assert "100 * roaming_procedure_success_rate" in gauges["Registration Success Rate"]
    assert "100 * roaming_procedure_success_rate" in gauges["Auth Success Rate"]
    assert "100 * roaming_procedure_success_rate" in gauges[
        "PDU Session Establishment Success Rate"
    ]
    assert "or vector(0)" not in gauges["Observed / expected coverage"]
    for expr in _all_exprs(doc):
        assert "or vector(0)" not in expr, expr
        assert "roaming_flow_registration_success_rate" not in expr
        assert "UNVERIFIED" not in expr

    stats = _stat_exprs(doc)
    for domain_title in ("HOME (HPLMN)", "VISITED (VPLMN)", "IPX (SBI relay)", "RAN (NAS/NGAP)"):
        expr = stats[domain_title]
        assert "roaming_flow_domain_observed_total" in expr
        assert 'result="observed"' in expr and "domain=" in expr
        # Prefer step count first so PromQL or does not hide truth behind a zero gauge.
        assert expr.strip().startswith("count(roaming_flow_step_total")
        panel = next(p for p in doc["panels"] if p.get("title") == domain_title)
        assert panel["fieldConfig"]["defaults"]["noValue"] == "—"

    coverage_panels = [
        p
        for p in doc.get("panels") or []
        if p.get("type") == "gauge" and "coverage" in (p.get("title") or "").lower()
    ]
    assert len(coverage_panels) == 4
    for panel in coverage_panels:
        no_val = panel["fieldConfig"]["defaults"]["noValue"]
        assert no_val == "PENDING — run refresh-flow-dashboard", panel.get("title")

    for title in (
        "Registration Success Rate",
        "Auth Success Rate",
        "PDU Session Establishment Success Rate",
    ):
        panel = next(p for p in doc["panels"] if p.get("title") == title)
        assert panel["type"] == "gauge"
        assert panel["fieldConfig"]["defaults"]["noValue"] == (
            "PENDING — run refresh-flow-dashboard"
        )
        assert "UNVERIFIED" not in (panel.get("description") or "")
        assert "multi-trial GSMA" in (panel.get("description") or "")


def test_flow_dashboard_v11_title_and_success_rates() -> None:
    doc = json.loads(FLOW.read_text(encoding="utf-8"))
    assert TITLE_MARKER in doc.get("title", "")
    assert "v6 markdown" not in doc.get("title", "")
    assert "v7 coverage" not in doc.get("title", "")
    assert "v9 capture-sync" not in doc.get("title", "")
    titles = _panel_titles(doc)
    assert "3GPP procedure success rates (MEASURED ladder)" in titles
    for expr in _all_exprs(doc):
        assert "or vector(0)" not in expr, expr
        assert "roaming_flow_auth_success_rate" not in expr
    gauges = _gauge_exprs(doc)
    assert "roaming_procedure_success_rate" in gauges["Registration Success Rate"]
