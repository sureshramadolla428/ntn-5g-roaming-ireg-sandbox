"""Offline tests for dashboard/exporters/pcap_flow_exporter.py (Windows-safe)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

EXPORTERS = Path(__file__).resolve().parents[2] / "dashboard" / "exporters"
sys.path.insert(0, str(EXPORTERS))

import flow_catalog  # noqa: E402
import pcap_flow_exporter as exporter  # noqa: E402

pytestmark = pytest.mark.tier1


def test_flow_catalog_has_auth_reg_pdu_phases() -> None:
    phases = {s.phase for s in flow_catalog.FLOW_STEPS}
    assert phases == {"auth", "reg", "pdu"}
    assert len(flow_catalog.FLOW_STEPS) == 28


def test_expected_step_counts_tc05_excludes_na() -> None:
    """TC-05 denominator: auth=9 reg=7 pdu=7 (excludes 5 HR-only N/A pdu steps) → 23."""
    counts = flow_catalog.expected_step_counts("TC-05")
    assert counts == {"auth": 9, "reg": 7, "pdu": 7}
    assert flow_catalog.total_expected_steps("TC-05") == 23
    assert flow_catalog.catalog_step_counts() == {"auth": 9, "reg": 7, "pdu": 12}


def test_status_for_observation_honesty() -> None:
    assert exporter._status_for_observation(True, "MEASURED") == "observed"
    assert exporter._status_for_observation(False, "MEASURED") == "missing"
    assert exporter._status_for_observation(False, "PARTIAL") == "partial_expected"
    assert exporter._status_for_observation(False, "N/A") == "partial_expected"


def test_resolve_latest_capture_empty(tmp_path: Path) -> None:
    root = tmp_path / "pcaps"
    (root / "TC-05").mkdir(parents=True)
    assert exporter.resolve_latest_capture(root, "TC-05") is None


def test_resolve_latest_capture_picks_newest(tmp_path: Path) -> None:
    base = tmp_path / "pcaps" / "TC-05"
    (base / "20250101T100000").mkdir(parents=True)
    latest = base / "20250102T120000"
    latest.mkdir()
    assert exporter.resolve_latest_capture(tmp_path / "pcaps", "TC-05") == latest


def test_resolve_latest_capture_ignores_junk_trees(tmp_path: Path) -> None:
    """pcaps/TC-05/mnt|home nested copies must not win over timestamp captures."""
    base = tmp_path / "pcaps" / "TC-05"
    good = base / "20250824T120000"
    good.mkdir(parents=True)
    (good / "ipx-net.pcap").write_bytes(b"\x00")
    (base / "mnt").mkdir()
    (base / "home").mkdir()
    (base / "mnt" / "hgfs").mkdir(parents=True)
    assert exporter.resolve_latest_capture(tmp_path / "pcaps", "TC-05") == good


def test_reload_clears_metrics_when_switching_fixtures(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Switching capture ladders must drop old gauges, not leave zeros or ghosts."""
    monkeypatch.setenv("TC_ID", "TC-05")
    rich = exporter.load_fixture_ladder("TC-05")
    exporter.STATE.tc_id = "TC-05"
    exporter.STATE.capture_dir = tmp_path / "a"
    exporter._publish_metrics(rich)
    assert exporter.DOMAIN_OBSERVED.labels(domain="ran", tc_id="TC-05")._value.get() > 0  # type: ignore[attr-defined]
    assert exporter.PROCEDURE_SUCCESS_RATE.labels(
        procedure="registration", tc_id="TC-05"
    )._value.get() == 1.0  # type: ignore[attr-defined]
    assert exporter.PROCEDURE_KPI_READY.labels(
        procedure="registration", tc_id="TC-05"
    )._value.get() == 1.0  # type: ignore[attr-defined]

    empty = exporter._build_ladder({}, "TC-05")
    exporter.STATE.capture_dir = tmp_path / "b"
    exporter._publish_metrics(empty)
    # Always-emit: rate stays published at 0; ready=0; domain counts zeroed via clear+republish.
    assert (
        exporter.PROCEDURE_SUCCESS_RATE.labels(
            procedure="registration", tc_id="TC-05"
        )._value.get()  # type: ignore[attr-defined]
        == 0.0
    )
    assert exporter.PROCEDURE_KPI_READY.labels(
        procedure="registration", tc_id="TC-05"
    )._value.get() == 0.0  # type: ignore[attr-defined]
    assert exporter.DOMAIN_OBSERVED.labels(domain="ran", tc_id="TC-05")._value.get() == 0.0  # type: ignore[attr-defined]
    assert exporter.COVERAGE_RATIO.labels(tc_id="TC-05")._value.get() == 0.0  # type: ignore[attr-defined]


def test_reload_endpoint_accepts_pcap_dir_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    cap = tmp_path / "20250824T150000"
    cap.mkdir()
    monkeypatch.setenv("TC_ID", "TC-05")
    monkeypatch.setenv("PCAP_DIR", "")
    monkeypatch.setenv("PCAP_ROOT", str(tmp_path.parent))
    # Empty dir → fixture backend when no pcaps
    client = TestClient(exporter.app)
    resp = client.post("/reload", json={"pcap_dir": str(cap)})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "reloaded"
    assert "observed" in body
    assert body["capture_dir"] == str(cap)
    metrics = client.get("/metrics").content.decode()
    assert "roaming_procedure_kpi_ready" in metrics
    assert "roaming_flow_domain_observed_total" in metrics


def test_publish_procedure_rates_after_reload() -> None:
    """After clear+publish, attempts/successes always present; rate only when ready."""
    steps = exporter.load_fixture_ladder("TC-05")
    exporter.STATE.tc_id = "TC-05"
    exporter._publish_metrics(steps)
    for procedure in ("registration", "auth", "pdu"):
        assert exporter.PROCEDURE_ATTEMPTS.labels(
            procedure=procedure, tc_id="TC-05"
        )._value.get() == 1.0  # type: ignore[attr-defined]
        assert exporter.PROCEDURE_KPI_READY.labels(
            procedure=procedure, tc_id="TC-05"
        )._value.get() == 1.0  # type: ignore[attr-defined]
        assert exporter.PROCEDURE_SUCCESS_RATE.labels(
            procedure=procedure, tc_id="TC-05"
        )._value.get() == 1.0  # type: ignore[attr-defined]


def test_load_fixture_ladder() -> None:
    steps = exporter.load_fixture_ladder("TC-05")
    assert steps
    assert any(s.id == "auth-3" and s.status == "observed" for s in steps)
    assert any(s.id == "pdu-4" and s.status == "partial_expected" for s in steps)


def test_build_ladder_empty_observations() -> None:
    ladder = exporter._build_ladder({}, "TC-05")
    assert len(ladder) == len(flow_catalog.FLOW_STEPS)
    missing = [s for s in ladder if s.status == "missing"]
    assert missing


def test_match_http2_row() -> None:
    step = flow_catalog.FLOW_STEPS[2]  # auth-3 nausf
    assert flow_catalog.match_http2_row(
        step, "ipx-net.pcap", 0.0, "10.10.3.31", "10.10.3.21", "POST",
        "/nausf-auth/v1/ue-authentications",
    )
    assert not flow_catalog.match_http2_row(
        step, "ipx-net.pcap", 0.0, "x", "y", "GET", "/other",
    )


def test_exporter_http_endpoints(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PCAP_DIR", "")
    monkeypatch.setenv("TC_ID", "TC-05")
    exporter.reload_state()
    client = TestClient(exporter.app)
    health = client.get("/health")
    assert health.status_code == 200
    body = health.json()
    assert body["status"] == "ok"
    assert "parser" in body
    assert "ready" in body
    assert "pcap_dir" in body
    assert "tc_id" in body
    assert body["tc_id"] == "TC-05"
    assert "observed" in body
    assert "coverage" in body
    assert "domains" in body
    assert set(body["domains"]) >= {"ran", "visited", "home", "ipx"}

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert b"roaming_flow_step_total" in metrics.content
    assert b"roaming_flow_domain_observed_total" in metrics.content

    ladder = client.get("/ladder/latest")
    assert ladder.status_code == 200
    ladder_body = ladder.json()
    assert ladder_body["tc_id"] == "TC-05"
    assert isinstance(ladder_body["steps"], list)
    assert ladder_body["honesty"]["sepp"].startswith("ABSENT")

    reloaded = client.post("/reload")
    assert reloaded.status_code == 200
    assert reloaded.json()["status"] == "reloaded"


def test_health_ok_while_parser_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    """Liveness must not wait on pcap parse (compose healthcheck / depends_on)."""
    monkeypatch.setenv("PCAP_DIR", "")
    exporter.STATE.parser_backend = "loading"
    exporter._PARSE_READY.clear()
    client = TestClient(exporter.app, raise_server_exceptions=True)
    # Bypass startup race: hit health with loading state after client exists
    exporter.STATE.parser_backend = "loading"
    exporter._PARSE_READY.clear()
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["parser"] == "loading"
    assert health.json()["ready"] is False



def test_parse_capture_dir_uses_fixture_without_pcaps(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cap_dir = tmp_path / "empty_capture"
    cap_dir.mkdir()
    steps, backend = exporter.parse_capture_dir(cap_dir, "TC-05")
    assert backend in {"fixture", "fixture-degraded", "tshark", "pyshark", "none"}
    if backend.startswith("fixture"):
        assert any(s.status == "observed" for s in steps)


def test_fixture_json_valid() -> None:
    fixture = EXPORTERS / "fixtures" / "tc05_minimal_ladder.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))
    assert data["tc_id"] == "TC-05"
    assert len(data["steps"]) == len(flow_catalog.FLOW_STEPS)


def test_publish_harness_metrics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "run1.json").write_text(
        json.dumps({"passed": 8, "executed": 10}), encoding="utf-8"
    )
    monkeypatch.setattr(exporter, "HARNESS_REPORTS", reports)
    exporter._publish_harness_metrics()
    assert exporter.HARNESS_PASSED._value.get() == 8.0  # type: ignore[attr-defined]
    assert exporter.HARNESS_EXECUTED._value.get() == 10.0  # type: ignore[attr-defined]
    assert exporter.HARNESS_PASS_RATE._value.get() == 0.8  # type: ignore[attr-defined]
    assert exporter.HARNESS_FILES._value.get() == 1.0  # type: ignore[attr-defined]


def test_coverage_ratio_on_fixture_ladder() -> None:
    steps = exporter.load_fixture_ladder("TC-05")
    exporter.STATE.tc_id = "TC-05"
    exporter._publish_metrics(steps)
    ratio = exporter.COVERAGE_RATIO.labels(tc_id="TC-05")._value.get()  # type: ignore[attr-defined]
    observed = sum(1 for s in steps if s.status == "observed")
    expected = flow_catalog.total_expected_steps("TC-05")
    assert ratio == observed / expected
    assert exporter.EXPECTED_STEPS.labels(phase="all", tc_id="TC-05")._value.get() == float(expected)  # type: ignore[attr-defined]
    auth_cov = exporter.PHASE_COVERAGE.labels(phase="auth", tc_id="TC-05")._value.get()  # type: ignore[attr-defined]
    assert auth_cov == 1.0  # fixture has all 9 auth steps observed


def test_compute_procedure_kpis_fixture_all_success() -> None:
    """Fixture has auth-1/reg-7, auth-3/auth-8, pdu-1/pdu-11 all observed → rate 1.0."""
    steps = exporter.load_fixture_ladder("TC-05")
    kpis = {k.procedure: k for k in exporter.compute_procedure_kpis(steps)}
    assert kpis["registration"].rate == 1.0
    assert kpis["registration"].attempt_step == "auth-1"
    assert kpis["registration"].success_step == "reg-7"
    assert kpis["auth"].rate == 1.0
    assert kpis["auth"].attempt_step == "auth-3"
    assert kpis["auth"].success_step == "auth-8"
    assert kpis["pdu"].rate == 1.0
    assert kpis["pdu"].attempt_step == "pdu-1"
    assert kpis["pdu"].success_step == "pdu-11"


def test_compute_procedure_kpis_missing_attempt_is_none() -> None:
    """No attempt and no accept → rate None (Grafana PENDING); do not invent success."""
    ladder = exporter._build_ladder({}, "TC-05")
    kpis = {k.procedure: k for k in exporter.compute_procedure_kpis(ladder)}
    assert kpis["registration"].rate is None
    assert kpis["registration"].attempts == 0.0
    assert kpis["auth"].rate is None
    assert kpis["pdu"].rate is None


def test_compute_procedure_kpis_attempt_without_success() -> None:
    """Request seen, Accept missing → rate 0.0 (honest failure), not UNVERIFIED."""
    ladder = exporter._build_ladder({"auth-1": (True, 1.0), "pdu-1": (True, 2.0)}, "TC-05")
    kpis = {k.procedure: k for k in exporter.compute_procedure_kpis(ladder)}
    assert kpis["registration"].rate == 0.0
    assert kpis["registration"].attempts == 1.0
    assert kpis["registration"].successes == 0.0
    assert kpis["pdu"].rate == 0.0
    # auth-3 absent; auth-6 absent → no auth rate
    assert kpis["auth"].rate is None


def test_compute_procedure_kpis_accept_only_is_ready_100() -> None:
    """Accept without matched request → ready rate 1.0 (weak parse honesty)."""
    ladder = exporter._build_ladder(
        {"reg-7": (True, 1.0), "auth-8": (True, 2.0), "pdu-11": (True, 3.0)},
        "TC-05",
    )
    kpis = {k.procedure: k for k in exporter.compute_procedure_kpis(ladder)}
    assert kpis["registration"].rate == 1.0
    assert kpis["registration"].attempts == 0.0
    assert kpis["registration"].successes == 1.0
    assert kpis["auth"].rate == 1.0
    assert kpis["pdu"].rate == 1.0


def test_compute_procedure_kpis_auth_fallback_challenge_smc() -> None:
    """When Nausf create missing, use challenge/SMC pair."""
    ladder = exporter._build_ladder(
        {"auth-6": (True, 1.0), "auth-9": (True, 2.0)},
        "TC-05",
    )
    kpis = {k.procedure: k for k in exporter.compute_procedure_kpis(ladder)}
    assert kpis["auth"].rate == 1.0
    assert kpis["auth"].attempt_step == "auth-6"
    assert kpis["auth"].success_step == "auth-9"


def test_publish_procedure_success_rate_metrics() -> None:
    steps = exporter.load_fixture_ladder("TC-05")
    exporter.STATE.tc_id = "TC-05"
    exporter._publish_metrics(steps)
    for procedure in ("registration", "auth", "pdu"):
        rate = exporter.PROCEDURE_SUCCESS_RATE.labels(
            procedure=procedure, tc_id="TC-05"
        )._value.get()  # type: ignore[attr-defined]
        assert rate == 1.0
        assert exporter.PROCEDURE_ATTEMPTS.labels(
            procedure=procedure, tc_id="TC-05"
        )._value.get() == 1.0  # type: ignore[attr-defined]
        assert exporter.PROCEDURE_SUCCESSES.labels(
            procedure=procedure, tc_id="TC-05"
        )._value.get() == 1.0  # type: ignore[attr-defined]

    # Empty ladder still publishes rate=0 (always-emit) so Grafana is not blank
    empty = exporter._build_ladder({}, "TC-05")
    exporter._publish_metrics(empty)
    for procedure in ("registration", "auth", "pdu"):
        assert (
            exporter.PROCEDURE_SUCCESS_RATE.labels(
                procedure=procedure, tc_id="TC-05"
            )._value.get()  # type: ignore[attr-defined]
            == 0.0
        )
        assert (
            exporter.PROCEDURE_KPI_READY.labels(
                procedure=procedure, tc_id="TC-05"
            )._value.get()  # type: ignore[attr-defined]
            == 0.0
        )
        assert (
            exporter.PROCEDURE_ATTEMPTS.labels(
                procedure=procedure, tc_id="TC-05"
            )._value.get()  # type: ignore[attr-defined]
            == 0.0
        )


def test_exporter_metrics_include_procedure_kpis(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PCAP_DIR", "")
    monkeypatch.setenv("TC_ID", "TC-05")
    exporter.reload_state()
    client = TestClient(exporter.app)
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    text = metrics.content.decode()
    assert "roaming_procedure_success_rate" in text
    assert 'procedure="registration"' in text
    assert "roaming_procedure_attempts_total" in text
    assert "roaming_procedure_successes_total" in text


def test_callflow_html_route(monkeypatch: pytest.MonkeyPatch) -> None:
    html = EXPORTERS.parent / "grafana" / "public-assets" / "roaming-callflow.html"
    assets = html.parent
    monkeypatch.setattr(exporter, "PUBLIC_ASSETS", assets)
    monkeypatch.setattr(exporter, "CALLFLOW_HTML", html)
    client = TestClient(exporter.app)
    # Trigger startup mounts
    with client:
        resp = client.get("/static/roaming-callflow.html")
    assert resp.status_code == 200
    assert "5G SA Roaming" in resp.text


def test_publish_metrics_clears_stale_result_labels() -> None:
    """Reload must drop old result labels so Grafana table has one row per step."""
    ladder_a = exporter._build_ladder({"auth-1": (False, None)}, "TC-05")
    exporter._publish_metrics(ladder_a)
    auth1_missing = exporter.STEP_STATUS.labels(
        phase="auth",
        step="auth-1",
        procedure=ladder_a[0].procedure,
        result="missing",
        domain="ran",
    )._value.get()  # type: ignore[attr-defined]
    assert auth1_missing == 1.0

    ladder_b = exporter._build_ladder({"auth-1": (True, 1.0)}, "TC-05")
    exporter._publish_metrics(ladder_b)
    # Cleared entirely — missing series must not remain (even at 0).
    missing_key = (
        "auth",
        "auth-1",
        ladder_b[0].procedure,
        "missing",
        "ran",
    )
    assert missing_key not in exporter.STEP_STATUS._metrics  # type: ignore[attr-defined]
    assert exporter.STEP_STATUS.labels(
        phase="auth",
        step="auth-1",
        procedure=ladder_b[0].procedure,
        result="observed",
        domain="ran",
    )._value.get() == 1.0  # type: ignore[attr-defined]


def test_domain_observed_matches_step_domain_labels() -> None:
    """Domain gauge and step{domain=} must agree for fixture ladder."""
    steps = exporter.load_fixture_ladder("TC-05")
    exporter.STATE.tc_id = "TC-05"
    exporter._publish_metrics(steps)
    for domain in ("ran", "visited", "home", "ipx"):
        gauge_val = exporter.DOMAIN_OBSERVED.labels(
            domain=domain, tc_id="TC-05"
        )._value.get()  # type: ignore[attr-defined]
        expected = sum(
            1 for s in steps if s.status == "observed" and s.domain == domain
        )
        assert gauge_val == float(expected), domain
    # Fixture has no observed home steps (HR N/A) — home may be 0; ran/ipx/visited > 0.
    assert exporter.DOMAIN_OBSERVED.labels(domain="ran", tc_id="TC-05")._value.get() > 0  # type: ignore[attr-defined]
    assert exporter.DOMAIN_OBSERVED.labels(domain="ipx", tc_id="TC-05")._value.get() > 0  # type: ignore[attr-defined]


def test_reload_refuses_junk_pcap_dir() -> None:
    """POST /reload must 400 on mnt/home junk nests (never load share trees)."""
    client = TestClient(exporter.app)
    for junk in (
        "/pcaps/TC-05/mnt",
        "/pcaps/TC-05/home/sureshramadolla/ntn-roaming-lab",
        "/pcaps/TC-05/hgfs/MVNOs_and_MNOs",
    ):
        resp = client.post("/reload", json={"pcap_dir": junk})
        assert resp.status_code == 400, junk
        assert "junk" in resp.json().get("error", "").lower()


def test_clear_endpoint_zeros_observed_and_gauges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /clear → health observed=0, pcap_dir null; step series gone; ratios 0."""
    monkeypatch.setenv("TC_ID", "TC-05")
    monkeypatch.setenv("PCAP_DIR", "/pcaps/TC-05/20250824T120000")
    steps = exporter.load_fixture_ladder("TC-05")
    assert any(s.status == "observed" for s in steps)

    client = TestClient(exporter.app)
    # Re-seed after TestClient startup (background reload may race).
    exporter.STATE.tc_id = "TC-05"
    exporter.STATE.capture_dir = Path("/pcaps/TC-05/20250824T120000")
    exporter.STATE.parser_backend = "fixture"
    exporter.STATE.steps = steps
    exporter._PARSE_READY.set()
    exporter._publish_metrics(steps)
    assert exporter.COVERAGE_RATIO.labels(tc_id="TC-05")._value.get() > 0  # type: ignore[attr-defined]

    resp = client.post("/clear")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "cleared"
    assert body["observed"] == 0
    assert body["pcap_dir"] is None
    assert body["capture_dir"] is None

    health = client.get("/health").json()
    assert health["ready"] is True
    assert health["observed"] == 0
    assert health["pcap_dir"] is None
    assert health["parser"] == "cleared"
    assert health["coverage"] == 0.0
    assert health["domains"] == {"ran": 0, "visited": 0, "home": 0, "ipx": 0}

    # No step series (cleared) — or, if any remain, must be empty registry.
    assert len(exporter.STEP_STATUS._metrics) == 0  # type: ignore[attr-defined]
    assert exporter.COVERAGE_RATIO.labels(tc_id="TC-05")._value.get() == 0.0  # type: ignore[attr-defined]
    assert exporter.PHASE_COVERAGE.labels(phase="auth", tc_id="TC-05")._value.get() == 0.0  # type: ignore[attr-defined]
    for domain in ("ran", "visited", "home", "ipx"):
        assert exporter.DOMAIN_OBSERVED.labels(domain=domain, tc_id="TC-05")._value.get() == 0.0  # type: ignore[attr-defined]
    for procedure in ("registration", "auth", "pdu"):
        assert exporter.PROCEDURE_SUCCESS_RATE.labels(
            procedure=procedure, tc_id="TC-05"
        )._value.get() == 0.0  # type: ignore[attr-defined]
        assert exporter.PROCEDURE_KPI_READY.labels(
            procedure=procedure, tc_id="TC-05"
        )._value.get() == 0.0  # type: ignore[attr-defined]
    assert os.environ.get("PCAP_DIR", "") == ""


def test_reload_clear_true_same_as_clear(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /reload {\"clear\": true} clears gauges like POST /clear."""
    monkeypatch.setenv("TC_ID", "TC-05")
    exporter.STATE.tc_id = "TC-05"
    exporter.STATE.capture_dir = Path("/pcaps/TC-05/x")
    exporter._publish_metrics(exporter.load_fixture_ladder("TC-05"))
    client = TestClient(exporter.app)
    resp = client.post("/reload", json={"clear": True})
    assert resp.status_code == 200
    assert resp.json()["status"] == "cleared"
    assert resp.json()["observed"] == 0
    assert client.get("/health").json()["pcap_dir"] is None


def test_is_junk_capture_path_detects_nested_trees() -> None:
    from pathlib import Path

    assert exporter._is_junk_capture_path(Path("/pcaps/TC-05/mnt/foo"))
    assert exporter._is_junk_capture_path(Path("/pcaps/TC-05/home/x"))
    assert exporter._is_junk_capture_path(
        Path("/pcaps/TC-05/home/sureshramadolla/ntn-roaming-lab")
    )
    assert not exporter._is_junk_capture_path(Path("/pcaps/TC-05/20250824T120000"))
    # Host /home/user/... before pcaps/TC-* must NOT false-positive on segment "home".
    assert not exporter._is_junk_capture_path(
        Path("/home/sureshramadolla/ntn-roaming-lab/pcaps/TC-05/20260826T010742")
    )
    # Host paths containing "Users" must NOT be treated as junk without a TC-* nest.
    assert not exporter._is_junk_capture_path(
        Path("C:/Users/sures/AppData/Local/Temp/20250824T120000")
    )
    assert not exporter._is_junk_capture_path(
        Path("C:/Users/sures/OneDrive/Desktop/MVNOs_and_MNOs/ntn-roaming-lab/pcaps/TC-05/20260826T010742")
    )
