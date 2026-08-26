import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cdr_model import LabCdr, reconcile


def test_reconcile_gap_and_mismatch():
    home = [LabCdr("1", "001010000000001", "LABVS", "LABHM", 100, 1), LabCdr("2", "001010000000001", "LABVS", "LABHM", 50, 2)]
    visited = [LabCdr("1", "001010000000001", "LABVS", "LABHM", 99, 1), LabCdr("3", "001010000000001", "LABVS", "LABHM", 10, 3)]
    r = reconcile(home, visited)
    assert "2" in r["missing_at_visited"]
    assert "3" in r["orphan_at_visited"]
    assert "1" in r["field_mismatched"]
    assert r["conformance"] == "NOT_TAP3_BER"
