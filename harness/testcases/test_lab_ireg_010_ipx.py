"""LAB-IREG-010: SBI proxy stand-in labelled (not SEPP)."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-010"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_010_sbi_proxy_not_sepp():
    compose = (ROOT / "ipx" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "ipx-sbi-proxy" in compose
    assert "Not a SEPP" in compose or "NOT called SEPP" in compose or "do NOT call it SEPP" in compose
    table = (ROOT / "ipx" / "docs" / "n32-divergence-table.md").read_text(encoding="utf-8")
    assert "SBI proxy stand-in" in table
