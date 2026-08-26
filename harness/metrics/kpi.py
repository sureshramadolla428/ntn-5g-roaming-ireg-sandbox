"""KPI formulas citing C8 / C9 / D3 / D4."""
from __future__ import annotations

import math
from typing import Iterable, Sequence


def pass_rate(passed: int, executed: int) -> float:
    """C8-related pass rate = passed/executed."""
    if executed == 0:
        return 0.0
    return passed / executed


def wilson_interval(passed: int, executed: int, z: float = 1.96) -> tuple[float, float]:
    """D4.7 Wilson score interval on pass rate."""
    if executed == 0:
        return (0.0, 0.0)
    p = passed / executed
    denom = 1 + z**2 / executed
    centre = p + z**2 / (2 * executed)
    margin = z * math.sqrt(p * (1 - p) / executed + z**2 / (4 * executed**2))
    return ((centre - margin) / denom, (centre + margin) / denom)


def automation_coverage(automated: int, total: int) -> float:
    """D4.2 Automation Coverage %."""
    if total == 0:
        return 0.0
    return 100.0 * automated / total


def flake_rate(inconsistent: int, executed: int) -> float:
    """D4.4 Flake Rate %."""
    if executed == 0:
        return 0.0
    return 100.0 * inconsistent / executed


def defect_coverage(closed_with_regression: int, closed: int) -> float:
    """D4.6 Defect Coverage %."""
    if closed == 0:
        return 100.0
    return 100.0 * closed_with_regression / closed


def signalling_success(successes: int, attempts: int) -> float:
    """D3 signalling success ratio."""
    if attempts == 0:
        return 0.0
    return successes / attempts
