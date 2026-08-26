"""Phase 14 NTN suite markers."""
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.tier2
@pytest.mark.lab_ireg("LAB-IREG-NTN-001")
def test_b4_profiles_exist():
    p = ROOT / "ran" / "oai" / "netem" / "profiles-b4.yaml"
    text = p.read_text(encoding="utf-8")
    assert "delay_ms: 271" in text and "delay_ms: 13" in text


@pytest.mark.tier2
@pytest.mark.deferred
@pytest.mark.live
@pytest.mark.lab_ireg("LAB-IREG-NTN-002")
def test_oai_leo_attach_deferred():
    pytest.skip("DEFERRED-TO-UBUNTU OAI @ 38dc378")
