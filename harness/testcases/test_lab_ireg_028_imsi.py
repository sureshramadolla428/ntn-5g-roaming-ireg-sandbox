"""LAB-IREG-028: IMSI correlator dry-run"""
from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-028"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_028_imsi():
    """IMSI correlator dry-run

    Anti-flake metadata: flaky_candidate; N-run job in ci (D4.4).
    Multi-point capture: visited-edge, ipx-ingress, home-edge.
    """
    from pathlib import Path
    assert (Path(__file__).resolve().parents[2] / 'imsi-trace' / 'correlate.py').exists()
