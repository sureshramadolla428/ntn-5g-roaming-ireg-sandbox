"""LAB-IREG-027: Multi-point capture design present"""
from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-027"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_027_trace():
    """Multi-point capture design present

    Anti-flake metadata: flaky_candidate; N-run job in ci (D4.4).
    Multi-point capture: visited-edge, ipx-ingress, home-edge.
    """
    from pathlib import Path
    assert (Path(__file__).resolve().parents[2] / 'docs' / 'call-flows' / 'multi-point-capture.md').exists()
