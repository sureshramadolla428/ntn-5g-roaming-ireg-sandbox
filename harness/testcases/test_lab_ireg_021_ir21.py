"""LAB-IREG-021: IR.21 profile validate vs network-plan"""
from __future__ import annotations

import pytest

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-021"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_021_ir21():
    """IR.21 profile validate vs network-plan

    Anti-flake metadata: flaky_candidate; N-run job in ci (D4.4).
    Multi-point capture: visited-edge, ipx-ingress, home-edge.
    """
    import sys
    from pathlib import Path
    import yaml
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / 'ir21'))
    from parser import load_yaml_profile, validate_profile
    plan = yaml.safe_load((root / 'network-plan.yaml').read_text(encoding='utf-8'))
    assert validate_profile(load_yaml_profile(root / 'ir21' / 'profiles' / 'visited.yaml'), plan) == []
