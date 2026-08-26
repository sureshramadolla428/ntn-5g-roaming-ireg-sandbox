import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kpi import pass_rate, wilson_interval, automation_coverage, flake_rate, defect_coverage


def test_pass_rate():
    assert pass_rate(8, 10) == 0.8


def test_wilson():
    lo, hi = wilson_interval(8, 10)
    assert 0 <= lo <= hi <= 1


def test_d4():
    assert automation_coverage(20, 25) == 80.0
    assert flake_rate(1, 100) == 1.0
    assert defect_coverage(5, 5) == 100.0
