"""Parse offline pcaps into Prometheus metrics and a Grafana ladder JSON.

Uses pyshark when installed, else tshark subprocess, else fixture/degraded mode
for Windows offline tests (DEFERRED-TO-UBUNTU for live capture parsing).

Endpoints (default :8010):
  GET /metrics   — Prometheus text
  GET /ladder    — latest ladder JSON
  GET /ladder/latest — alias
  GET /static/roaming-callflow.html — ladder UI (StaticFiles mount)
  GET /health
  POST /reload   — re-parse PCAP_DIR (JSON body optional: {"pcap_dir": "..."}
                   or {"clear": true} to zero metrics without re-parse)
  POST /clear    — drop capture ladder; gauges → 0; health observed=0, pcap_dir=null
"""
from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, Info, generate_latest

try:
    from .flow_catalog import (
        CATALOG_STEPS_TOTAL,
        FLOW_STEPS,
        FlowStep,
        catalog_step_counts,
        expected_label,
        expected_step_counts,
        total_expected_steps,
    )
except ImportError:
    from flow_catalog import (
        CATALOG_STEPS_TOTAL,
        FLOW_STEPS,
        FlowStep,
        catalog_step_counts,
        expected_label,
        expected_step_counts,
        total_expected_steps,
    )

LOGGER = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PCAP_ROOT = ROOT / "pcaps"
FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "tc05_minimal_ladder.json"
PUBLIC_ASSETS = Path(
    os.environ.get(
        "PUBLIC_ASSETS",
        str(Path(__file__).resolve().parents[1] / "grafana" / "public-assets"),
    )
)
CALLFLOW_HTML = Path(os.environ.get("CALLFLOW_HTML", str(PUBLIC_ASSETS / "roaming-callflow.html")))
HARNESS_REPORTS = Path(
    os.environ.get("HARNESS_REPORTS", str(ROOT / "harness" / "reports"))
)

# Gauge (not Counter): result label changes on reload; stale Counter series duplicated Grafana rows.
# On every reload, ALL child series are cleared (not left at 0) so PromQL count() cannot see ghosts.
STEP_STATUS = Gauge(
    "roaming_flow_step_total",
    "Current roaming flow step result (1=active for this capture only)",
    ["phase", "step", "procedure", "result", "domain"],
)
STEP_TS = Gauge(
    "roaming_flow_step_timestamp",
    "First observed epoch timestamp for a flow step",
    ["phase", "step"],
)
COVERAGE_RATIO = Gauge(
    "roaming_flow_coverage_ratio",
    "Observed steps / TC-expected steps (0-1); denominator excludes N/A catalog steps",
    ["tc_id"],
)
CATALOG_STEPS = Gauge(
    "roaming_flow_catalog_steps_total",
    "Full catalog step count per phase (28 steps: auth=9 reg=7 pdu=12)",
    ["phase"],
)
EXPECTED_STEPS = Gauge(
    "roaming_flow_expected_steps_total",
    "TC-aware expected steps (excludes N/A); phase=all is coverage denominator",
    ["phase", "tc_id"],
)
PHASE_COVERAGE = Gauge(
    "roaming_flow_phase_coverage_ratio",
    "Observed / TC-expected steps per phase (0-1)",
    ["phase", "tc_id"],
)
DOMAIN_OBSERVED = Gauge(
    "roaming_flow_domain_observed_total",
    "Observed ladder steps per lab domain (ran/visited/home/ipx) for current capture",
    ["domain", "tc_id"],
)
HARNESS_PASSED = Gauge("harness_reports_passed_total", "Sum of passed from harness/reports/*.json")
HARNESS_EXECUTED = Gauge("harness_reports_executed_total", "Sum of executed from harness/reports/*.json")
HARNESS_PASS_RATE = Gauge("harness_pass_rate", "C8 pass rate = passed/executed from harness reports")
HARNESS_FILES = Gauge("harness_reports_files_total", "Count of JSON report files in harness/reports")
PARSER_INFO = Gauge(
    "flow_exporter_parser_info",
    "Flow exporter parser backend active (1=current)",
    ["backend"],
)
BUILD_INFO = Info("flow_exporter_build", "Flow exporter build metadata")

# Procedure completion from ladder step presence (binary). Not multi-trial GSMA KPIs.
# Oracles: registration=reg-7/auth-1; auth=auth-8|9 over auth-3|6; pdu=pdu-11/pdu-1.
PROCEDURE_SUCCESS_RATE = Gauge(
    "roaming_procedure_success_rate",
    "MEASURED ladder completion ratio (0-1) for last capture; always published after reload (0 when neither attempt nor accept)",
    ["procedure", "tc_id"],
)
PROCEDURE_ATTEMPTS = Gauge(
    "roaming_procedure_attempts_total",
    "Binary attempt presence (0|1) from catalog step observation — Gauge to avoid stale Counter labels",
    ["procedure", "tc_id"],
)
PROCEDURE_SUCCESSES = Gauge(
    "roaming_procedure_successes_total",
    "Binary success presence (0|1) from catalog step observation — Gauge to avoid stale Counter labels",
    ["procedure", "tc_id"],
)
PROCEDURE_KPI_READY = Gauge(
    "roaming_procedure_kpi_ready",
    "1 when success_rate published (attempt and/or accept known); 0 when PENDING for this capture",
    ["procedure", "tc_id"],
)

# Timestamp capture dirs from capture-ireg-tc.sh: YYYYMMDDTHHMMSS
_CAPTURE_DIR_RE = re.compile(r"^\d{8}T\d{6}$")
# Accidental nested trees under pcaps/TC-05/ (mnt, home, …) must never win "latest".
_JUNK_CAPTURE_NAMES = frozenset({"mnt", "home", "hgfs", "Users", "reference", "__pycache__"})


@dataclass(frozen=True)
class ProcedureKpi:
    """Binary ladder-derived procedure completion for one TC capture."""

    procedure: str
    attempts: float
    successes: float
    rate: float | None  # None → publish rate 0.0 + kpi_ready=0 (Grafana shows 0, not No data)
    attempt_step: str
    success_step: str
    formula_note: str


@dataclass
class LadderStep:
    """Runtime observation for one catalog step."""

    id: str
    phase: str
    procedure: str
    src: str
    dst: str
    status: str
    ts: float | None
    domain: str
    expected: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "phase": self.phase,
            "procedure": self.procedure,
            "src": self.src,
            "dst": self.dst,
            "status": self.status,
            "ts": self.ts,
            "domain": self.domain,
            "expected": self.expected,
        }


@dataclass
class ParseState:
    """Mutable parse output shared by HTTP handlers."""

    capture_dir: Path | None = None
    tc_id: str = "TC-05"
    parser_backend: str = "none"
    steps: list[LadderStep] = field(default_factory=list)
    honesty: dict[str, str] = field(default_factory=dict)

    def ladder_payload(self) -> dict[str, Any]:
        return {
            "capture_dir": str(self.capture_dir) if self.capture_dir else None,
            "tc_id": self.tc_id,
            "parser": self.parser_backend,
            "honesty": self.honesty,
            "steps": [s.as_dict() for s in self.steps],
        }


STATE = ParseState(
    parser_backend="loading",
    honesty={
        "camp": "B1 same-PLMN 001/01 — not true VPLMN 999/70",
        "sepp": "ABSENT — dual-home SBI, not SEPP/N32",
        "user_plane": "TC-05 LBO 10.46 MEASURED; HR 10.45 steps PARTIAL until TC-15",
        "colors": "VPLMN #1565C0, HPLMN #2E7D32",
    }
)
_RELOAD_LOCK = threading.Lock()
_PARSE_READY = threading.Event()


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name, "").strip()
    return Path(raw) if raw else default


def _is_junk_capture_path(path: Path) -> bool:
    """True for mnt/home/hgfs nests under a TC-* capture root.

    Host absolute paths like ``/home/user/.../pcaps/TC-05/<ts>`` are allowed —
    only components *after* a ``TC-*`` directory are checked for junk names.
    """
    if path.name in _JUNK_CAPTURE_NAMES:
        return True
    parts = path.parts
    for i, part in enumerate(parts):
        # Only treat junk segments that appear *after* a TC-NN directory.
        if part.startswith("TC-") and i + 1 < len(parts):
            return any(p in _JUNK_CAPTURE_NAMES for p in parts[i + 1 :])
    return False


def _is_capture_dir(path: Path) -> bool:
    """True for capture-ireg-tc timestamp dirs (or any dir with .pcap), never junk trees."""
    if not path.is_dir() or path.name in _JUNK_CAPTURE_NAMES or _is_junk_capture_path(path):
        return False
    if _CAPTURE_DIR_RE.match(path.name):
        return True
    # Fallback: real capture with pcaps but non-standard name (still exclude junk).
    return any(path.glob("*.pcap"))


def resolve_latest_capture(pcap_root: Path, tc_id: str) -> Path | None:
    """Return newest timestamp directory under pcaps/<TC-ID>/ (ignore mnt/home junk)."""
    base = pcap_root / tc_id
    if not base.is_dir():
        return None
    candidates = sorted(
        (p for p in base.iterdir() if _is_capture_dir(p)),
        key=lambda p: p.name,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _clear_gauge(gauge: Gauge) -> None:
    """Drop all child series so Prometheus scrape no longer exposes stale labels."""
    gauge._metrics.clear()  # type: ignore[attr-defined]


def _reset_metrics() -> None:
    """Fully clear every capture-derived gauge before republishing current ladder."""
    for gauge in (
        STEP_STATUS,
        STEP_TS,
        COVERAGE_RATIO,
        CATALOG_STEPS,
        EXPECTED_STEPS,
        PHASE_COVERAGE,
        DOMAIN_OBSERVED,
        PROCEDURE_SUCCESS_RATE,
        PROCEDURE_ATTEMPTS,
        PROCEDURE_SUCCESSES,
        PROCEDURE_KPI_READY,
        PARSER_INFO,
    ):
        _clear_gauge(gauge)
    HARNESS_PASSED.set(0.0)
    HARNESS_EXECUTED.set(0.0)
    HARNESS_PASS_RATE.set(0.0)
    HARNESS_FILES.set(0.0)


def _publish_zero_flow_gauges(tc_id: str) -> None:
    """Emit zeroed coverage/domain/procedure gauges so Grafana shows 0, not No data.

    Step series are intentionally absent (cleared) — table panels filter > 0.
    """
    COVERAGE_RATIO.labels(tc_id=tc_id).set(0.0)
    for phase in ("auth", "reg", "pdu"):
        PHASE_COVERAGE.labels(phase=phase, tc_id=tc_id).set(0.0)
        CATALOG_STEPS.labels(phase=phase).set(0.0)
        EXPECTED_STEPS.labels(phase=phase, tc_id=tc_id).set(0.0)
    EXPECTED_STEPS.labels(phase="all", tc_id=tc_id).set(0.0)
    for domain in ("ran", "visited", "home", "ipx"):
        DOMAIN_OBSERVED.labels(domain=domain, tc_id=tc_id).set(0.0)
    for procedure in ("registration", "auth", "pdu"):
        PROCEDURE_ATTEMPTS.labels(procedure=procedure, tc_id=tc_id).set(0.0)
        PROCEDURE_SUCCESSES.labels(procedure=procedure, tc_id=tc_id).set(0.0)
        PROCEDURE_SUCCESS_RATE.labels(procedure=procedure, tc_id=tc_id).set(0.0)
        PROCEDURE_KPI_READY.labels(procedure=procedure, tc_id=tc_id).set(0.0)


def clear_metrics_state() -> ParseState:
    """Zero all capture-derived gauges; health ready with observed=0, pcap_dir=null.

    Reuses _reset_metrics (same clear path as /reload before republish). Does not
    re-parse pcaps. Clears PCAP_DIR env so a bare POST /reload does not revive
    the previous capture path.
    """
    with _RELOAD_LOCK:
        tc_id = os.environ.get("TC_ID", STATE.tc_id or "TC-05").strip() or "TC-05"
        os.environ["PCAP_DIR"] = ""
        STATE.tc_id = tc_id
        STATE.capture_dir = None
        STATE.steps = []
        STATE.parser_backend = "cleared"
        _reset_metrics()
        _publish_zero_flow_gauges(tc_id)
        for label in (
            "tshark",
            "pyshark",
            "fixture",
            "fixture-degraded",
            "fixture-no-dir",
            "empty",
            "none",
            "loading",
            "error",
            "cleared",
        ):
            PARSER_INFO.labels(backend=label).set(0)
        PARSER_INFO.labels(backend="cleared").set(1)
        BUILD_INFO.info(
            {
                "parser": "cleared",
                "tc_id": tc_id,
                "capture_dir": "",
            }
        )
        _PARSE_READY.set()
        LOGGER.info("flow metrics cleared tc=%s observed=0 pcap_dir=null", tc_id)
        return STATE


def _step_observed(by_id: dict[str, LadderStep], step_id: str) -> bool:
    item = by_id.get(step_id)
    return item is not None and item.status == "observed"


def _binary_procedure_rate(
    attempt_seen: bool, success_seen: bool
) -> tuple[float, float, float | None]:
    """Map attempt/accept observation to (attempts, successes, rate).

    Honest ladder rules:
      - both known → rate 1.0 if accept else 0.0
      - only accept → rate 1.0 (weak parse still shows success)
      - only attempt → rate 0.0
      - neither → rate None (publisher still emits 0.0 + kpi_ready=0 so panels are not blank)
    """
    attempts = 1.0 if attempt_seen else 0.0
    successes = 1.0 if success_seen else 0.0
    if attempt_seen or success_seen:
        return attempts, successes, 1.0 if success_seen else 0.0
    return attempts, successes, None


def compute_procedure_kpis(steps: list[LadderStep]) -> list[ProcedureKpi]:
    """Derive registration/auth/pdu completion from catalog step presence.

    Binary oracles (not multi-attempt population rates):
      registration — reg-7 / auth-1 (TS 24.501 §5.5.1 narrative)
      auth — prefer auth-8/auth-3; else auth-9/auth-6 (TS 33.501 §6.1.3 narrative)
      pdu — pdu-11 / pdu-1 (TS 24.501 §6.4.1 narrative)

    Rate is None only when neither attempt nor accept was observed.
    """
    by_id = {s.id: s for s in steps}
    out: list[ProcedureKpi] = []

    # Registration: Accept / Request
    reg_attempt = _step_observed(by_id, "auth-1")
    reg_success = _step_observed(by_id, "reg-7")
    reg_attempts, reg_successes, reg_rate = _binary_procedure_rate(reg_attempt, reg_success)
    out.append(
        ProcedureKpi(
            procedure="registration",
            attempts=reg_attempts,
            successes=reg_successes,
            rate=reg_rate,
            attempt_step="auth-1",
            success_step="reg-7",
            formula_note="reg-7 / auth-1 (TS 24.501 §5.5.1)",
        )
    )

    # Auth: confirm|SMC / create|challenge — prefer SBI pair when create observed
    auth_success = _step_observed(by_id, "auth-8") or _step_observed(by_id, "auth-9")
    if _step_observed(by_id, "auth-3"):
        auth_attempt_step = "auth-3"
        auth_attempt = True
    elif _step_observed(by_id, "auth-6"):
        auth_attempt_step = "auth-6"
        auth_attempt = True
    else:
        auth_attempt_step = "auth-3"
        auth_attempt = False
    if _step_observed(by_id, "auth-8"):
        auth_success_step = "auth-8"
    elif _step_observed(by_id, "auth-9"):
        auth_success_step = "auth-9"
    else:
        auth_success_step = "auth-8"
    auth_attempts, auth_successes, auth_rate = _binary_procedure_rate(
        auth_attempt, auth_success
    )
    out.append(
        ProcedureKpi(
            procedure="auth",
            attempts=auth_attempts,
            successes=auth_successes,
            rate=auth_rate,
            attempt_step=auth_attempt_step,
            success_step=auth_success_step,
            formula_note="auth-8|auth-9 / auth-3|auth-6 (TS 33.501 §6.1.3)",
        )
    )

    # PDU: Accept / Request
    pdu_attempt = _step_observed(by_id, "pdu-1")
    pdu_success = _step_observed(by_id, "pdu-11")
    pdu_attempts, pdu_successes, pdu_rate = _binary_procedure_rate(pdu_attempt, pdu_success)
    out.append(
        ProcedureKpi(
            procedure="pdu",
            attempts=pdu_attempts,
            successes=pdu_successes,
            rate=pdu_rate,
            attempt_step="pdu-1",
            success_step="pdu-11",
            formula_note="pdu-11 / pdu-1 (TS 24.501 §6.4.1)",
        )
    )
    return out


def _publish_procedure_kpis(steps: list[LadderStep], tc_id: str) -> None:
    """Always emit attempts/successes/rate/ready gauges so Grafana never shows No data."""
    for kpi in compute_procedure_kpis(steps):
        PROCEDURE_ATTEMPTS.labels(procedure=kpi.procedure, tc_id=tc_id).set(kpi.attempts)
        PROCEDURE_SUCCESSES.labels(procedure=kpi.procedure, tc_id=tc_id).set(kpi.successes)
        ready = 1.0 if kpi.rate is not None else 0.0
        PROCEDURE_KPI_READY.labels(procedure=kpi.procedure, tc_id=tc_id).set(ready)
        # Always publish rate (0 when neither attempt nor accept) so instant queries work.
        PROCEDURE_SUCCESS_RATE.labels(procedure=kpi.procedure, tc_id=tc_id).set(
            kpi.rate if kpi.rate is not None else 0.0
        )
        LOGGER.info(
            "procedure kpi tc=%s procedure=%s attempts=%.0f successes=%.0f rate=%s ready=%.0f "
            "(%s → %s) %s",
            tc_id,
            kpi.procedure,
            kpi.attempts,
            kpi.successes,
            "n/a→0" if kpi.rate is None else f"{kpi.rate:.0f}",
            ready,
            kpi.attempt_step,
            kpi.success_step,
            kpi.formula_note,
        )


def _publish_metrics(steps: list[LadderStep]) -> None:
    _reset_metrics()
    tc_id = STATE.tc_id
    observed_total = 0
    partial_total = 0
    missing_total = 0
    observed_by_phase = {"auth": 0, "reg": 0, "pdu": 0}
    observed_by_domain = {"ran": 0, "visited": 0, "home": 0, "ipx": 0}
    for item in steps:
        domain = (item.domain or "").lower() or "unknown"
        STEP_STATUS.labels(
            phase=item.phase,
            step=item.id,
            procedure=item.procedure,
            result=item.status,
            domain=domain,
        ).set(1)
        if item.status == "observed":
            observed_total += 1
            observed_by_phase[item.phase] = observed_by_phase.get(item.phase, 0) + 1
            if domain in observed_by_domain:
                observed_by_domain[domain] += 1
            else:
                LOGGER.warning(
                    "observed step %s has unknown domain=%r (not counted in domain gauges)",
                    item.id,
                    domain,
                )
        elif item.status == "partial_expected":
            partial_total += 1
        elif item.status == "missing":
            missing_total += 1
        if item.ts is not None:
            STEP_TS.labels(phase=item.phase, step=item.id).set(item.ts)

    expected_by_phase = expected_step_counts(tc_id)
    catalog_by_phase = catalog_step_counts()
    denominator = total_expected_steps(tc_id) or 1

    for phase, count in catalog_by_phase.items():
        CATALOG_STEPS.labels(phase=phase).set(count)
    for phase, count in expected_by_phase.items():
        EXPECTED_STEPS.labels(phase=phase, tc_id=tc_id).set(count)
    EXPECTED_STEPS.labels(phase="all", tc_id=tc_id).set(denominator)

    for phase in ("auth", "reg", "pdu"):
        phase_expected = expected_by_phase[phase] or 1
        PHASE_COVERAGE.labels(phase=phase, tc_id=tc_id).set(
            observed_by_phase[phase] / phase_expected
        )

    for domain, count in observed_by_domain.items():
        DOMAIN_OBSERVED.labels(domain=domain, tc_id=tc_id).set(float(count))

    COVERAGE_RATIO.labels(tc_id=tc_id).set(observed_total / denominator)
    _publish_procedure_kpis(steps, tc_id)

    status_sum = observed_total + partial_total + missing_total
    LOGGER.info(
        "reload pcap_dir=%s observed=%d tc=%s parser=%s "
        "catalog=%d expected_denominator=%d partial=%d missing=%d status_sum=%d "
        "phases auth=%d/%d reg=%d/%d pdu=%d/%d domains ran=%d visited=%d home=%d ipx=%d",
        STATE.capture_dir,
        observed_total,
        tc_id,
        STATE.parser_backend,
        CATALOG_STEPS_TOTAL,
        denominator,
        partial_total,
        missing_total,
        status_sum,
        observed_by_phase["auth"],
        expected_by_phase["auth"],
        observed_by_phase["reg"],
        expected_by_phase["reg"],
        observed_by_phase["pdu"],
        expected_by_phase["pdu"],
        observed_by_domain["ran"],
        observed_by_domain["visited"],
        observed_by_domain["home"],
        observed_by_domain["ipx"],
    )
    if status_sum != CATALOG_STEPS_TOTAL:
        LOGGER.warning(
            "flow step status sum %d != catalog total %d",
            status_sum,
            CATALOG_STEPS_TOTAL,
        )
    # Single active parser label for Grafana stat panel
    for label in (
        "tshark",
        "pyshark",
        "fixture",
        "fixture-degraded",
        "fixture-no-dir",
        "empty",
        "none",
        "loading",
        "error",
        "cleared",
    ):
        PARSER_INFO.labels(backend=label).set(0)
    PARSER_INFO.labels(backend=STATE.parser_backend).set(1)
    BUILD_INFO.info(
        {
            "parser": STATE.parser_backend,
            "tc_id": STATE.tc_id,
            "capture_dir": str(STATE.capture_dir or ""),
        }
    )


def _publish_harness_metrics() -> None:
    """Expose harness/reports/*.json as Prometheus gauges (C8 pass rate)."""
    passed = 0
    executed = 0
    file_count = 0
    if HARNESS_REPORTS.is_dir():
        for report in HARNESS_REPORTS.glob("*.json"):
            try:
                data = json.loads(report.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                LOGGER.warning("skip harness report %s: %s", report, exc)
                continue
            file_count += 1
            passed += int(data.get("passed", 0))
            executed += int(data.get("executed", 0))
    HARNESS_FILES.set(file_count)
    HARNESS_PASSED.set(passed)
    HARNESS_EXECUTED.set(executed)
    HARNESS_PASS_RATE.set(passed / executed if executed else 0.0)


def _status_for_observation(observed: bool, expected: str) -> str:
    if observed:
        return "observed"
    if expected in {"N/A", "PARTIAL"}:
        return "partial_expected"
    return "missing"


def _build_ladder(observations: dict[str, tuple[bool, float | None]], tc_id: str) -> list[LadderStep]:
    ladder: list[LadderStep] = []
    for step in FLOW_STEPS:
        seen, ts = observations.get(step.id, (False, None))
        exp = expected_label(step, tc_id)
        ladder.append(
            LadderStep(
                id=step.id,
                phase=step.phase,
                procedure=step.procedure,
                src=step.src,
                dst=step.dst,
                status=_status_for_observation(seen, exp),
                ts=ts,
                domain=step.domain,
                expected=exp,
            )
        )
    return ladder


def load_fixture_ladder(tc_id: str) -> list[LadderStep]:
    """Load canned ladder for offline tests when no parser is available."""
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    out: list[LadderStep] = []
    for row in data["steps"]:
        out.append(
            LadderStep(
                id=row["id"],
                phase=row["phase"],
                procedure=row["procedure"],
                src=row["src"],
                dst=row["dst"],
                status=row["status"],
                ts=row.get("ts"),
                domain=row["domain"],
                expected=row.get("expected", "MEASURED"),
            )
        )
    return out


def _tshark_available() -> bool:
    return shutil.which("tshark") is not None


def _pyshark_available() -> bool:
    try:
        import pyshark  # noqa: F401

        return _tshark_available()
    except ImportError:
        return False


def _run_tshark_fields(pcap: Path, display_filter: str) -> list[dict[str, str]]:
    cmd = [
        "tshark",
        "-r",
        str(pcap),
        "-Y",
        display_filter,
        "-T",
        "fields",
        "-E",
        "separator=\t",
        "-e",
        "frame.time_epoch",
        "-e",
        "ip.src",
        "-e",
        "ip.dst",
        "-e",
        "http2.headers.method",
        "-e",
        "http2.headers.path",
        "-e",
        "http2.header.value",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        LOGGER.warning("tshark failed on %s: %s", pcap, exc)
        return []
    rows: list[dict[str, str]] = []
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        while len(parts) < 6:
            parts.append("")
        path = parts[4] or parts[5] or ""
        # http2.header.value may carry :path when headers.path is empty
        if not path and parts[5]:
            path = parts[5]
        rows.append(
            {
                "ts": parts[0],
                "src": parts[1],
                "dst": parts[2],
                "method": parts[3],
                "path": path,
            }
        )
    return rows


def _run_tshark_count(pcap: Path, display_filter: str) -> tuple[bool, float | None]:
    """Return whether any frame matches display_filter, plus first match epoch.

    Do **not** pass tshark ``-c 1`` when reading capture files: for ``-r``,
    ``-c`` limits packets read from the file *before* filtering, so an early
    non-matching frame (e.g. ICMP ping on ran-net) makes NGAP/NAS steps miss
    even when later frames match (MEASURED on host: ``tshark -Y ngap | wc -l``).

    Implementation: run ``tshark -r … -Y FILTER -T fields -e frame.time_epoch``
    with **no** ``-c``, take the first stdout epoch line, then kill the process
    (cap via timeout). Never truncate the file read before the filter can match.
    """
    cmd = [
        "tshark",
        "-r",
        str(pcap),
        "-Y",
        display_filter,
        "-T",
        "fields",
        "-e",
        "frame.time_epoch",
    ]
    # Guard: never reintroduce packet-count truncation on file reads.
    assert "-c" not in cmd, "tshark -c must not be used with -r (truncates before -Y)"
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except OSError:
        return False, None
    first_line = ""
    try:
        assert proc.stdout is not None
        # First matching frame.time_epoch only — do not buffer the full dump.
        # Timeout: readline can block on a hung tshark; join a reader thread.
        box: list[str] = []

        def _reader() -> None:
            try:
                box.append(proc.stdout.readline())  # type: ignore[union-attr]
            except OSError:
                box.append("")

        reader = threading.Thread(target=_reader, daemon=True)
        reader.start()
        reader.join(timeout=120.0)
        if reader.is_alive():
            proc.kill()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
            return False, None
        if box and box[0]:
            first_line = box[0].strip()
        if proc.poll() is None:
            proc.kill()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        else:
            proc.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        if proc.poll() is None:
            try:
                proc.kill()
            except OSError:
                pass
        return False, None
    if not first_line:
        return False, None
    try:
        return True, float(first_line)
    except ValueError:
        return True, None


def _match_step_http2(step: FlowStep, method: str, path: str) -> bool:
    if not step.http2_path_contains:
        return False
    path_l = path.lower()
    needle = step.http2_path_contains.lower()
    if needle not in path_l:
        return False
    if step.http2_method and method.strip() and method.upper() != step.http2_method.upper():
        return False
    return True


# Log grep fallback when bridge pcaps miss HTTP/2 decode (common on docker br-*).
_LOG_PATTERNS: dict[str, tuple[str, ...]] = {
    "auth-3": ("nausf-auth", "ue-authentications"),
    "auth-4": ("nudm-ueau", "generate-auth-data"),
    "auth-8": ("5g-aka-confirmation", "ue-authentications"),
    "reg-2": ("nudm-uecm", "registrations/amf-3gpp-access"),
    "reg-3": ("nudm-sdm", "sm-data", "dataset-names"),
    "reg-5": ("nudr-dr", "subscription-data"),
    "pdu-2": ("nsmf-pdusession", "sm-contexts"),
    "pdu-3": ("pfcp", "session establishment"),
    "pdu-11": ("pdu session", "establishment accept"),
}

# Ordered broader tshark filters when primary message_type misses (opaque NAS).
# Prefer nr-ue.log for step identity; avoid bare "ngap" except auth-2 (any NGAP).
_TSHARK_FALLBACKS: dict[str, tuple[str, ...]] = {
    "auth-1": ("ngap.procedureCode == 15",),  # InitialUEMessage
    "auth-6": ("nas-5gs.mm.message_type == 0x56",),
    "auth-7": ("nas-5gs.mm.message_type == 0x57",),
    "auth-9": (
        "nas-5gs.mm.message_type == 0x5e",  # SMC complete
        "nas-5gs.mm.message_type == 0x5d",
    ),
    "reg-7": ("nas-5gs.mm.message_type == 0x42",),
    "pdu-1": ("nas-5gs.sm.message_type == 0xc1",),
    "pdu-11": ("nas-5gs.sm.message_type == 0xc2",),
}

# UERANSIM nr-ue.log needles (lowercase) — RAN steps when pcap decode is weak.
_NR_UE_PATTERNS: dict[str, tuple[str, ...]] = {
    "auth-1": ("sending initial registration",),
    "auth-2": ("rrc connection established", "ue switches to state [cm-connected]"),
    "auth-6": ("authentication request received",),
    # Response often not printed; SMC after challenge implies auth response OK.
    "auth-7": ("security mode command received",),
    "auth-9": ("security mode command received",),
    "reg-7": ("registration accept received", "mm-registered"),
    "pdu-1": ("sending pdu session establishment request",),
    "pdu-11": (
        "pdu session establishment accept received",
        "pdu session establishment is successful",
    ),
    "pdu-12": ("uesimtun0", "10.46.", "10.45."),
}


def parse_docker_logs(capture_dir: Path) -> dict[str, tuple[bool, float | None]]:
    """Supplement tshark with AMF/SMF/AUSF/UDM log greps from capture snapshot."""
    log_dir = capture_dir / "docker-logs"
    if not log_dir.is_dir():
        return {}
    blobs: dict[str, str] = {}
    for log in log_dir.glob("*.log"):
        try:
            blobs[log.name] = log.read_text(encoding="utf-8", errors="replace").lower()
        except OSError:
            continue
    combined = "\n".join(blobs.values())
    out: dict[str, tuple[bool, float | None]] = {}
    for step_id, needles in _LOG_PATTERNS.items():
        if any(n in combined for n in needles):
            out[step_id] = (True, None)
    return out


def parse_nr_ue_log(capture_dir: Path) -> dict[str, tuple[bool, float | None]]:
    """Supplement RAN steps from UERANSIM ``nr-ue.log`` when NAS/NGAP filters miss.

    Patterns are MEASURED against UERANSIM v3.x attach logs (e.g. 014834 LBO).
    auth-7 is inferred from SMC after challenge (response line often absent).
    """
    log_path = capture_dir / "nr-ue.log"
    if not log_path.is_file():
        return {}
    try:
        text = log_path.read_text(encoding="utf-8", errors="replace").lower()
    except OSError:
        return {}
    out: dict[str, tuple[bool, float | None]] = {}
    for step_id, needles in _NR_UE_PATTERNS.items():
        if any(n in text for n in needles):
            out[step_id] = (True, None)
    # auth-7 requires challenge evidence; do not invent response alone.
    if "auth-7" in out and "auth-6" not in out:
        del out["auth-7"]
    return out


def _merge_observations(
    primary: dict[str, tuple[bool, float | None]],
    extra: dict[str, tuple[bool, float | None]],
) -> dict[str, tuple[bool, float | None]]:
    merged = dict(primary)
    for step_id, (seen, ts) in extra.items():
        if seen and not merged.get(step_id, (False, None))[0]:
            merged[step_id] = (True, ts)
    return merged


def _filters_for_step(step: FlowStep) -> list[str]:
    """Primary display filter then ordered broader fallbacks (opaque NAS)."""
    filters: list[str] = []
    if step.tshark_display_filter:
        filters.append(step.tshark_display_filter)
    for fb in _TSHARK_FALLBACKS.get(step.id, ()):
        if fb not in filters:
            filters.append(fb)
    return filters


def parse_with_tshark(capture_dir: Path) -> dict[str, tuple[bool, float | None]]:
    observations: dict[str, tuple[bool, float | None]] = {s.id: (False, None) for s in FLOW_STEPS}

    for step in FLOW_STEPS:
        for rel in step.pcap_files:
            pcap = capture_dir / rel
            if not pcap.is_file():
                continue
            if step.http2_path_contains:
                filter_expr = "http2 || tcp.port == 7777"
                for row in _run_tshark_fields(pcap, filter_expr):
                    path = row.get("path") or ""
                    method = row.get("method") or ""
                    if _match_step_http2(step, method, path):
                        ts_raw = row.get("ts") or ""
                        ts_val = float(ts_raw) if ts_raw else None
                        prev_seen, prev_ts = observations[step.id]
                        observations[step.id] = (True, prev_ts or ts_val)
                        break
                if observations[step.id][0]:
                    break
            elif step.tshark_display_filter:
                for disp in _filters_for_step(step):
                    seen, ts_val = _run_tshark_count(pcap, disp)
                    if seen:
                        observations[step.id] = (True, ts_val)
                        break
                if observations[step.id][0]:
                    break
    return observations


def parse_with_pyshark(capture_dir: Path) -> dict[str, tuple[bool, float | None]]:
    import pyshark  # type: ignore

    observations: dict[str, tuple[bool, float | None]] = {s.id: (False, None) for s in FLOW_STEPS}
    for step in FLOW_STEPS:
        for rel in step.pcap_files:
            pcap = capture_dir / rel
            if not pcap.is_file():
                continue
            display = step.tshark_display_filter or "http2"
            try:
                cap = pyshark.FileCapture(str(pcap), display_filter=display, keep_packets=False)
            except Exception as exc:  # noqa: BLE001
                LOGGER.warning("pyshark open failed %s: %s", pcap, exc)
                continue
            for pkt in cap:
                try:
                    ts_val = float(pkt.sniff_timestamp)
                except (AttributeError, ValueError, TypeError):
                    ts_val = None
                if step.http2_path_contains:
                    http2 = getattr(pkt, "http2", None)
                    path = str(getattr(http2, "headers_path", "") or "")
                    method = str(getattr(http2, "headers_method", "") or "")
                    if path and _match_step_http2(step, method, path):
                        observations[step.id] = (True, ts_val)
                        cap.close()
                        break
                else:
                    observations[step.id] = (True, ts_val)
                    cap.close()
                    break
            else:
                cap.close()
            if observations[step.id][0]:
                break
    return observations


def parse_capture_dir(capture_dir: Path, tc_id: str) -> tuple[list[LadderStep], str]:
    """Parse pcaps in capture_dir; return ladder steps and backend label."""
    has_pcaps = any(capture_dir.glob("*.pcap"))
    if not has_pcaps and FIXTURE_PATH.is_file():
        return load_fixture_ladder(tc_id), "fixture"

    if _tshark_available():
        observations = parse_with_tshark(capture_dir)
        observations = _merge_observations(observations, parse_docker_logs(capture_dir))
        observations = _merge_observations(observations, parse_nr_ue_log(capture_dir))
        return _build_ladder(observations, tc_id), "tshark"
    if _pyshark_available():
        observations = parse_with_pyshark(capture_dir)
        observations = _merge_observations(observations, parse_nr_ue_log(capture_dir))
        return _build_ladder(observations, tc_id), "pyshark"

    if FIXTURE_PATH.is_file():
        return load_fixture_ladder(tc_id), "fixture-degraded"
    return _build_ladder({}, tc_id), "none"


def reload_state() -> ParseState:
    """Re-parse pcaps from env and refresh metrics.

    May take minutes when many/large pcaps require tshark; callers that must
    not block HTTP (startup, health) should run this in a background thread.
    """
    with _RELOAD_LOCK:
        tc_id = os.environ.get("TC_ID", "TC-05").strip() or "TC-05"
        pcap_root = _env_path("PCAP_ROOT", DEFAULT_PCAP_ROOT)
        pcap_dir_env = os.environ.get("PCAP_DIR", "").strip()
        if pcap_dir_env:
            capture_dir = Path(pcap_dir_env)
            if _is_junk_capture_path(capture_dir) or (
                capture_dir.is_dir() and not _is_capture_dir(capture_dir)
            ):
                LOGGER.error(
                    "refusing junk/non-capture PCAP_DIR=%s — resolving latest under %s/%s",
                    capture_dir,
                    pcap_root,
                    tc_id,
                )
                capture_dir = resolve_latest_capture(pcap_root, tc_id)
        else:
            capture_dir = resolve_latest_capture(pcap_root, tc_id)

        STATE.tc_id = tc_id
        STATE.capture_dir = capture_dir
        if capture_dir and capture_dir.is_dir():
            STATE.steps, STATE.parser_backend = parse_capture_dir(capture_dir, tc_id)
        elif FIXTURE_PATH.is_file():
            STATE.steps = load_fixture_ladder(tc_id)
            STATE.parser_backend = "fixture-no-dir"
        else:
            STATE.steps = _build_ladder({}, tc_id)
            STATE.parser_backend = "empty"

        _publish_metrics(STATE.steps)
        _publish_harness_metrics()
        _PARSE_READY.set()
        return STATE


def _reload_state_background() -> None:
    """Daemon worker so uvicorn can bind and serve /health during first parse."""
    try:
        reload_state()
        LOGGER.info(
            "flow exporter parse complete capture=%s parser=%s",
            STATE.capture_dir,
            STATE.parser_backend,
        )
    except Exception:  # noqa: BLE001 — keep HTTP up; surface via parser label
        LOGGER.exception("background pcap parse failed")
        STATE.parser_backend = "error"
        _PARSE_READY.set()


app = FastAPI(title="NTN Roaming Flow Exporter", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup() -> None:
    logging.basicConfig(level=logging.INFO)
    if PUBLIC_ASSETS.is_dir():
        app.mount("/static", StaticFiles(directory=str(PUBLIC_ASSETS)), name="static")
        LOGGER.info("static assets mounted from %s", PUBLIC_ASSETS)
    elif CALLFLOW_HTML.is_file():
        app.mount(
            "/static",
            StaticFiles(directory=str(CALLFLOW_HTML.parent)),
            name="static",
        )
        LOGGER.warning("PUBLIC_ASSETS missing; mounted parent of CALLFLOW_HTML")
    else:
        LOGGER.warning("call-flow static assets not found at %s", PUBLIC_ASSETS)
    # Do not block ASGI startup on tshark — compose healthchecks need /health ASAP.
    STATE.parser_backend = "loading"
    _PARSE_READY.clear()
    threading.Thread(target=_reload_state_background, name="pcap-reload", daemon=True).start()
    LOGGER.info("flow exporter listening; pcap parse running in background")


@app.get("/health")
def health() -> dict[str, Any]:
    """Liveness + capture identity so refresh scripts can verify the loaded ladder.

    Always returns quickly. When parse is still running, ready=false and counts are 0.
    """
    ready = _PARSE_READY.is_set()
    observed = sum(1 for s in STATE.steps if s.status == "observed") if ready else 0
    denominator = total_expected_steps(STATE.tc_id) or 1
    coverage = (observed / denominator) if ready else 0.0
    domains = {"ran": 0, "visited": 0, "home": 0, "ipx": 0}
    if ready:
        for s in STATE.steps:
            if s.status == "observed":
                d = (s.domain or "").lower()
                if d in domains:
                    domains[d] += 1
    kpis: dict[str, float | None] = {}
    if ready:
        for kpi in compute_procedure_kpis(STATE.steps):
            kpis[kpi.procedure] = kpi.rate
    return {
        "status": "ok",
        "parser": STATE.parser_backend,
        "ready": ready,
        "pcap_dir": str(STATE.capture_dir) if STATE.capture_dir else None,
        "tc_id": STATE.tc_id,
        "observed": observed,
        "coverage": round(coverage, 4),
        "expected_denominator": denominator if ready else total_expected_steps(STATE.tc_id),
        "domains": domains,
        "procedure_rates": kpis,
    }


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/ladder")
@app.get("/ladder/latest")
def ladder() -> JSONResponse:
    return JSONResponse(STATE.ladder_payload())


def _cleared_response() -> JSONResponse:
    """JSON body after POST /clear or POST /reload {\"clear\": true}."""
    return JSONResponse(
        {
            "status": "cleared",
            "observed": 0,
            "pcap_dir": None,
            **STATE.ladder_payload(),
        }
    )


@app.post("/clear")
def clear() -> JSONResponse:
    """Zero all flow gauges; health ready with observed=0 and pcap_dir=null."""
    clear_metrics_state()
    return _cleared_response()


@app.post("/reload")
def reload(body: dict[str, Any] | None = Body(default=None)) -> JSONResponse:
    """Re-parse capture. Accepts {"pcap_dir": "..."}, {"clear": true}, or empty body."""
    if isinstance(body, dict) and body.get("clear") is True:
        clear_metrics_state()
        return _cleared_response()
    pcap_dir: str | None = None
    if isinstance(body, dict):
        raw = body.get("pcap_dir")
        if isinstance(raw, str) and raw.strip():
            pcap_dir = raw.strip()
    elif isinstance(body, str) and body.strip():
        # Legacy: raw JSON string body
        pcap_dir = body.strip()
    if pcap_dir:
        junk_path = Path(pcap_dir)
        if _is_junk_capture_path(junk_path) or junk_path.name in _JUNK_CAPTURE_NAMES:
            LOGGER.error("POST /reload refused junk pcap_dir=%s", pcap_dir)
            return JSONResponse(
                {
                    "ok": False,
                    "error": f"refused junk pcap_dir={pcap_dir} (mnt/home/hgfs not allowed)",
                    "hint": "use /pcaps/TC-05/<YYYYMMDDTHHMMSS> or omit pcap_dir for latest",
                },
                status_code=400,
            )
        os.environ["PCAP_DIR"] = pcap_dir
        LOGGER.info("reload requested pcap_dir=%s", pcap_dir)
    reload_state()
    observed = sum(1 for s in STATE.steps if s.status == "observed")
    LOGGER.info(
        "reload done pcap_dir=%s observed=%d tc=%s parser=%s",
        STATE.capture_dir,
        observed,
        STATE.tc_id,
        STATE.parser_backend,
    )
    return JSONResponse(
        {
            "status": "reloaded",
            "observed": observed,
            **STATE.ladder_payload(),
        }
    )


def main() -> None:
    import uvicorn

    host = os.environ.get("FLOW_EXPORTER_HOST", "0.0.0.0")
    port = int(os.environ.get("FLOW_EXPORTER_PORT", "8010"))
    # Ensure imports work when launched as script from exporters/
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    # Run app object directly — avoids import-path failures in Docker CMD.
    uvicorn.run(app, host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
