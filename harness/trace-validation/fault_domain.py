"""Fault-domain attribution from multi-point evidence.

Domains: HOME | IPX | VISITED | INDETERMINATE
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class FaultDomain(str, Enum):
    HOME = "HOME"
    IPX = "IPX"
    VISITED = "VISITED"
    INDETERMINATE = "INDETERMINATE"


@dataclass
class Observation:
    request_at_visited_edge: Optional[bool] = None
    request_at_ipx_ingress: Optional[bool] = None
    request_at_home_edge: Optional[bool] = None
    answer_origin: Optional[str] = None  # HOME|IPX|VISITED
    answer_code: Optional[str] = None
    aia_success: Optional[bool] = None
    attach_success: Optional[bool] = None


def fault_domain(obs: Observation) -> FaultDomain:
    """Attribute fault domain per master-prompt evidence rules.

    Returns INDETERMINATE when evidence is insufficient (never guess).
    """
    # Explicit answer origins
    if obs.answer_code and "REALM_NOT_SERVED" in obs.answer_code.upper():
        if obs.answer_origin == "IPX":
            return FaultDomain.IPX
    if obs.answer_origin == "HOME" and obs.answer_code and obs.answer_code.startswith("5"):
        return FaultDomain.HOME

    # Presence matrix for requests
    if obs.request_at_visited_edge is True and obs.request_at_ipx_ingress is False:
        return FaultDomain.VISITED
    if obs.request_at_ipx_ingress is True and obs.request_at_home_edge is False:
        return FaultDomain.IPX

    if obs.aia_success is True and obs.attach_success is False:
        return FaultDomain.VISITED

    if (
        obs.request_at_visited_edge is True
        and obs.request_at_ipx_ingress is True
        and obs.request_at_home_edge is True
        and obs.answer_origin is None
    ):
        return FaultDomain.INDETERMINATE

    return FaultDomain.INDETERMINATE
