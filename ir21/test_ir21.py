import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import yaml
from parser import load_yaml_profile, validate_profile, validate_imsi


def test_profiles_against_plan():
    plan = yaml.safe_load((ROOT / "network-plan.yaml").read_text(encoding="utf-8"))
    for name in ("home.yaml", "visited.yaml"):
        p = load_yaml_profile(ROOT / "ir21" / "profiles" / name)
        assert validate_profile(p, plan) == []


def test_imsi():
    assert validate_imsi("001010000000001")
    assert not validate_imsi("999700000000001")
