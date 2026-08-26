import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fault_domain import Observation, FaultDomain, fault_domain


def test_visited_egress():
    assert fault_domain(Observation(request_at_visited_edge=True, request_at_ipx_ingress=False)) == FaultDomain.VISITED


def test_ipx_blackhole():
    assert fault_domain(Observation(request_at_ipx_ingress=True, request_at_home_edge=False)) == FaultDomain.IPX


def test_home_experimental_class():
    assert fault_domain(Observation(answer_origin="HOME", answer_code="5001")) == FaultDomain.HOME


def test_ipx_realm_not_served():
    assert (
        fault_domain(Observation(answer_origin="IPX", answer_code="DIAMETER_REALM_NOT_SERVED"))
        == FaultDomain.IPX
    )


def test_amf_down_pattern():
    assert fault_domain(Observation(aia_success=True, attach_success=False)) == FaultDomain.VISITED


def test_indeterminate():
    assert (
        fault_domain(
            Observation(
                request_at_visited_edge=True,
                request_at_ipx_ingress=True,
                request_at_home_edge=True,
                answer_origin=None,
            )
        )
        == FaultDomain.INDETERMINATE
    )
