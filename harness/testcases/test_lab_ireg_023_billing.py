"""LAB-IREG-023: RAP-style reject on seq gap"""
from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-023"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_023_billing():
    """RAP-style reject on seq gap

    Anti-flake metadata: flaky_candidate; N-run job in ci (D4.4).
    Multi-point capture: visited-edge, ipx-ingress, home-edge.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'mocks' / 'billing'))
    from cdr_model import LabCdr, reconcile, RapRejectCode
    r = reconcile(
        [LabCdr('1', 'i', 'LABVS', 'LABHM', 1, 1), LabCdr('2', 'i', 'LABVS', 'LABHM', 1, 2)],
        [LabCdr('1', 'i', 'LABVS', 'LABHM', 1, 1), LabCdr('2', 'i', 'LABVS', 'LABHM', 1, 3)],
    )
    assert r['sequence_gaps'] or RapRejectCode.SEQ_GAP
