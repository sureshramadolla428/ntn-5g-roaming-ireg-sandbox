"""5G SA roaming flow step catalog mapped from docs/call-flows/5g-sa-roaming-reference.md.

Step names and HTTP/2 path fragments follow the lab reference doc; exact 3GPP paths
marked UNVERIFIED there remain UNVERIFIED here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class FlowStep:
    """One checkable step in the roaming ladder."""

    id: str
    phase: str
    procedure: str
    src: str
    dst: str
    domain: str
    pcap_files: tuple[str, ...]
    tc05_label: str
    tc15_label: str
    http2_path_contains: str | None = None
    http2_method: str | None = None
    tshark_display_filter: str | None = None


# VPLMN #1565C0 / HPLMN #2E7D32 — documented in Grafana dashboard description.
FLOW_STEPS: tuple[FlowStep, ...] = (
    # Flow 1 — Authentication
    FlowStep(
        "auth-1", "auth", "Registration Request (SUCI)", "UE", "visited-amf", "ran",
        ("ran-net.pcap",), "MEASURED", "PARTIAL",
        tshark_display_filter="nas-5gs.mm.message_type == 0x41",
    ),
    FlowStep(
        "auth-2", "auth", "Initial UE Message", "gNB", "visited-amf", "ran",
        ("ran-net.pcap",), "MEASURED", "PARTIAL",
        tshark_display_filter="ngap",
    ),
    FlowStep(
        "auth-3", "auth", "Nausf_UEAuthentication create", "visited-amf", "home-ausf", "ipx",
        ("ipx-net.pcap",), "MEASURED", "PARTIAL",
        http2_method="POST", http2_path_contains="/nausf-auth/v1/ue-authentications",
    ),
    FlowStep(
        "auth-4", "auth", "Nudm_UEAuthentication_Get", "home-ausf", "home-udm", "ipx",
        ("ipx-net.pcap",), "MEASURED", "PARTIAL",
        http2_path_contains="/nudm-ueau/v1/",
    ),
    FlowStep(
        "auth-5", "auth", "Nudr_DR (auth subscription)", "home-udm", "home-udr", "ipx",
        ("ipx-net.pcap",), "MEASURED", "PARTIAL",
        http2_path_contains="/nudr-dr/v2/",
    ),
    FlowStep(
        "auth-6", "auth", "5G-AKA challenge", "visited-amf", "UE", "ran",
        ("ran-net.pcap",), "MEASURED", "PARTIAL",
        tshark_display_filter="nas-5gs",
    ),
    FlowStep(
        "auth-7", "auth", "Authentication Response", "UE", "visited-amf", "ran",
        ("ran-net.pcap",), "MEASURED", "PARTIAL",
        tshark_display_filter="nas-5gs.mm.message_type == 0x57",
    ),
    FlowStep(
        "auth-8", "auth", "Nausf_UEAuthentication confirm", "visited-amf", "home-ausf", "ipx",
        ("ipx-net.pcap",), "MEASURED", "PARTIAL",
        http2_path_contains="5g-aka-confirmation",
    ),
    FlowStep(
        "auth-9", "auth", "Security Mode Command/Complete", "visited-amf", "UE", "ran",
        ("ran-net.pcap",), "MEASURED", "PARTIAL",
        tshark_display_filter="nas-5gs || ngap",
    ),
    # Flow 2 — Registration
    FlowStep(
        "reg-1", "reg", "NF discovery (NRF)", "visited-amf", "visited-nrf", "ipx",
        ("ipx-net.pcap", "visited-net.pcap"), "MEASURED", "PARTIAL",
        http2_path_contains="/nnrf-nfm/v1/nf-instances",
    ),
    FlowStep(
        "reg-2", "reg", "Nudm_UECM_Registration", "visited-amf", "home-udm", "ipx",
        ("ipx-net.pcap", "visited-net.pcap", "home-net.pcap"), "MEASURED", "PARTIAL",
        http2_path_contains="/nudm-uecm/v1/",
    ),
    FlowStep(
        "reg-3", "reg", "Nudm_SDM_Get", "visited-amf", "home-udm", "ipx",
        ("ipx-net.pcap", "visited-net.pcap", "home-net.pcap"), "MEASURED", "PARTIAL",
        http2_path_contains="/nudm-sdm/v1/",
        http2_method="GET",
    ),
    FlowStep(
        "reg-4", "reg", "Nudm_SDM_Subscribe", "visited-amf", "home-udm", "ipx",
        ("ipx-net.pcap", "visited-net.pcap", "home-net.pcap"), "PARTIAL", "PARTIAL",
        http2_path_contains="sdm-subscriptions",
        http2_method="POST",
    ),
    FlowStep(
        "reg-5", "reg", "Nudr_DR (UE context)", "home-udm", "home-udr", "ipx",
        ("ipx-net.pcap",), "MEASURED", "PARTIAL",
        http2_path_contains="/nudr-dr/v2/",
    ),
    FlowStep(
        "reg-6", "reg", "Npcf_AMPolicyControl", "visited-amf", "home-pcf", "ipx",
        ("ipx-net.pcap",), "PARTIAL", "PARTIAL",
        http2_path_contains="/npcf-am-policy-control/",
    ),
    FlowStep(
        "reg-7", "reg", "Registration Accept", "visited-amf", "UE", "ran",
        ("ran-net.pcap",), "MEASURED", "PARTIAL",
        tshark_display_filter="nas-5gs.mm.message_type == 0x42",
    ),
    # Flow 3 — PDU (1/2)
    FlowStep(
        "pdu-1", "pdu", "PDU Session Establishment Request", "UE", "visited-amf", "ran",
        ("ran-net.pcap",), "MEASURED", "PARTIAL",
        tshark_display_filter="nas-5gs.sm.message_type == 0xc1",
    ),
    FlowStep(
        "pdu-2", "pdu", "Nsmf_PDUSession create (vSMF)", "visited-amf", "visited-smf", "visited",
        ("visited-net.pcap",), "MEASURED", "PARTIAL",
        http2_method="POST", http2_path_contains="/nsmf-pdusession/v1/sm-contexts",
    ),
    FlowStep(
        "pdu-3", "pdu", "PFCP Session Establishment (vUPF)", "visited-smf", "visited-upf", "visited",
        ("visited-net.pcap",), "MEASURED", "PARTIAL",
        tshark_display_filter="pfcp",
    ),
    FlowStep(
        "pdu-4", "pdu", "Nsmf_PDUSession create (HR / vSMF→hSMF)", "visited-smf", "home-smf", "ipx",
        ("ipx-net.pcap", "visited-net.pcap"), "N/A", "PARTIAL",
        http2_path_contains="/nsmf-pdusession/",
    ),
    FlowStep(
        "pdu-5", "pdu", "Nudm session (hSMF→UDM)", "home-smf", "home-udm", "home",
        ("home-net.pcap", "ipx-net.pcap"), "N/A", "PARTIAL",
        http2_path_contains="/nudm-",
    ),
    FlowStep(
        "pdu-6", "pdu", "Nudr_DR (session)", "home-udm", "home-udr", "home",
        ("home-net.pcap",), "N/A", "PARTIAL",
        http2_path_contains="/nudr-dr/v2/",
    ),
    # Flow 4 — PDU (2/2)
    FlowStep(
        "pdu-7", "pdu", "Npcf_SMPolicyControl create", "visited-smf", "home-pcf", "ipx",
        ("ipx-net.pcap", "visited-net.pcap"), "PARTIAL", "PARTIAL",
        http2_path_contains="/npcf-smpolicycontrol/v1/sm-policies",
    ),
    FlowStep(
        "pdu-8", "pdu", "PFCP Session Establishment (hUPF)", "home-smf", "home-upf", "home",
        ("home-net.pcap",), "N/A", "PARTIAL",
        tshark_display_filter="pfcp",
    ),
    FlowStep(
        "pdu-9", "pdu", "PFCP Session Modification (vUPF)", "visited-smf", "visited-upf", "visited",
        ("visited-net.pcap",), "MEASURED", "PARTIAL",
        tshark_display_filter="pfcp",
    ),
    FlowStep(
        "pdu-10", "pdu", "N4/N9 HR coordination", "visited-smf", "home-smf", "visited",
        ("visited-net.pcap", "home-net.pcap"), "N/A", "PARTIAL",
        tshark_display_filter="pfcp || gtp",
    ),
    FlowStep(
        "pdu-11", "pdu", "PDU Session Establishment Accept", "visited-amf", "UE", "ran",
        ("ran-net.pcap",), "MEASURED", "PARTIAL",
        tshark_display_filter="nas-5gs.sm.message_type == 0xc2",
    ),
    FlowStep(
        "pdu-12", "pdu", "User-plane check (LBO 10.46 / HR 10.45)", "UE", "visited-upf", "visited",
        ("visited-net.pcap",), "MEASURED", "N/A",
        tshark_display_filter="icmp",
    ),
)


def steps_by_phase() -> dict[str, list[FlowStep]]:
    """Group catalog steps by phase."""
    out: dict[str, list[FlowStep]] = {"auth": [], "reg": [], "pdu": []}
    for step in FLOW_STEPS:
        out.setdefault(step.phase, []).append(step)
    return out


# Step counts per docs/call-flows/5g-sa-roaming-reference.md:
# Flow 1 auth=9, Flow 2 reg=7, Flow 3 PDU (1/2)=6, Flow 4 PDU (2/2)=6 → 28 catalog steps.
CATALOG_STEPS_TOTAL = len(FLOW_STEPS)


def is_expected_for_tc(step: FlowStep, tc_id: str) -> bool:
    """Return True when a catalog step is in scope for the active TC (not N/A)."""
    return expected_label(step, tc_id) != "N/A"


def catalog_step_counts() -> dict[str, int]:
    """Full catalog step counts by phase (includes N/A steps)."""
    grouped = steps_by_phase()
    return {phase: len(steps) for phase, steps in grouped.items()}


def expected_step_counts(tc_id: str) -> dict[str, int]:
    """TC-aware expected step counts by phase (excludes N/A for active TC)."""
    counts = {"auth": 0, "reg": 0, "pdu": 0}
    for step in FLOW_STEPS:
        if is_expected_for_tc(step, tc_id):
            counts[step.phase] += 1
    return counts


def total_expected_steps(tc_id: str) -> int:
    """Total steps expected for TC (denominator for coverage ratio)."""
    return sum(expected_step_counts(tc_id).values())


def expected_label(step: FlowStep, tc_id: str) -> str:
    """Return MEASURED / PARTIAL / N/A label for the active TC."""
    if tc_id == "TC-15":
        return step.tc15_label
    return step.tc05_label


MatchFn = Callable[[FlowStep, str, float, str, str, str | None, str | None], bool]


def match_http2_row(
    step: FlowStep,
    _pcap: str,
    _ts: float,
    _src: str,
    _dst: str,
    method: str | None,
    path: str | None,
) -> bool:
    """Return True when an HTTP/2 row matches the step."""
    if step.http2_path_contains is None:
        return False
    if not path or step.http2_path_contains not in path:
        return False
    if step.http2_method and method and step.http2_method.upper() != method.upper():
        return False
    return True
