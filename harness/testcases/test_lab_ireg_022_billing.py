"""LAB-IREG-022: CDR reconcile missing orphan"""
from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-022"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_022_billing():
    """CDR reconcile missing orphan

    Anti-flake metadata: flaky_candidate; N-run job in ci (D4.4).
    Multi-point capture: visited-edge, ipx-ingress, home-edge.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'mocks' / 'billing'))
    from cdr_model import LabCdr, reconcile
    r = reconcile([LabCdr('1', '001010000000001', 'LABVS', 'LABHM', 1, 1)], [])
    assert '1' in r['missing_at_visited']
