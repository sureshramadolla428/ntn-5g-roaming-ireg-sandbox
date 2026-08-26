"""LAB-IREG-000: topology / routing policy offline checks + live probe gate."""
from __future__ import annotations

import os
import platform
import socket
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
PLAN = yaml.safe_load((ROOT / "network-plan.yaml").read_text(encoding="utf-8"))

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-000"),
    pytest.mark.tier1,
]


def test_plan_declares_direct_path_blocked():
    assert PLAN["routing_policy"]["home_visited_direct"] == "blocked"
    assert PLAN["routing_policy"]["inter_plmn_via"] == "ipx-net"


def test_plan_plmns_and_imsi_range():
    assert PLAN["lab"]["home_plmn"] == {"mcc": "001", "mnc": "01"}
    assert PLAN["lab"]["visited_plmn"] == {"mcc": "999", "mnc": "70"}
    assert PLAN["subscribers"]["imsi_range"] == ["001010000000001", "001010000000020"]


def test_sepp_reserved_not_used_as_sbi_path():
    """V14: SEPP absent — interconnect is sbi_proxy, never named SEPP."""
    assert "UNUSED" in PLAN["hosts"]["home"]["sepp_reserved"]["note"]
    assert PLAN["hosts"]["ipx"]["sbi_proxy"]["alias"] == "sbi-proxy.ipx.lab"
    divergence = (ROOT / "ipx" / "docs" / "n32-divergence-table.md").read_text(encoding="utf-8")
    assert "Must never be called SEPP" in divergence


def test_home_nf_configs_present():
    for nf in ("nrf", "scp", "ausf", "udm", "udr", "pcf", "hss", "smf", "upf"):
        assert (ROOT / "home-network" / "configs" / nf / f"{nf}.yaml").is_file()


@pytest.mark.skipif(
    platform.system() == "Windows" or os.environ.get("NTN_LIVE_NET") != "1",
    reason="Live iptables/docker probe DEFERRED-TO-UBUNTU (set NTN_LIVE_NET=1)",
)
def test_live_direct_probe_fails():
    """Negative test: TCP connect across home↔visited must fail when policy applied."""
    target = PLAN["hosts"]["visited"]["amf"]["ip"]
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex((target, 38412))
        assert result != 0, "Direct home→visited connect unexpectedly succeeded"
    finally:
        sock.close()
