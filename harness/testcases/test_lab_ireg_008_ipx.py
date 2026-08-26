"""LAB-IREG-008: IPX DRA templates present; freeDiameter runtime DEFERRED-TO-UBUNTU."""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

pytestmark = [
    pytest.mark.lab_ireg("LAB-IREG-008"),
    pytest.mark.tier1,
    pytest.mark.flaky_candidate,
]


def test_lab_ireg_008_dra_templates():
    fd = ROOT / "ipx" / "freediameter"
    assert (fd / "dra.conf.template").is_file()
    assert (fd / "rt.conf.template").is_file()
    assert (fd / "Dockerfile").is_file()
    text = (fd / "dra.conf.template").read_text(encoding="utf-8")
    assert "dra.ipx.lab" in text
    assert "NOT called SEPP" in text or "Not a SEPP" in text.lower() or "SEPP" in text
