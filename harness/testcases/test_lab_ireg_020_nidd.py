"""LAB-IREG-020: NIDD oversize reject boundary"""
from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-020"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_020_nidd():
    """NIDD oversize reject boundary

    Anti-flake metadata: flaky_candidate; N-run job in ci (D4.4).
    Multi-point capture: visited-edge, ipx-ingress, home-edge.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'mocks' / 'scef'))
    from app import app, NIDD_MAX_PAYLOAD_UNVERIFIED
    from fastapi.testclient import TestClient
    c = TestClient(app)
    over = 'aa' * (NIDD_MAX_PAYLOAD_UNVERIFIED + 1)
    r = c.post('/t8-nidd/v1/unverified/scs-as-sessions', json={'ue_id': 'x', 'payload_hex': over})
    assert r.status_code == 413
