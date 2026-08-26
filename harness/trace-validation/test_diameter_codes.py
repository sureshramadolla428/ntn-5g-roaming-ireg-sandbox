"""Unit tests for Diameter code registry — verified vs UNVERIFIED gates."""
from __future__ import annotations

import pytest

from diameter_codes import (
    DIAMETER_REALM_NOT_SERVED,
    DIAMETER_SUCCESS,
    DIAMETER_UNABLE_TO_DELIVER,
    EXPERIMENTAL_ROAMING_NOT_ALLOWED,
    EXPERIMENTAL_USER_UNKNOWN,
    require_verified,
)


def test_rfc6733_codes_verified():
    assert DIAMETER_SUCCESS.verified and DIAMETER_SUCCESS.code == 2001
    assert DIAMETER_UNABLE_TO_DELIVER.code == 3002
    assert DIAMETER_REALM_NOT_SERVED.code == 3003


def test_experimental_remain_unverified():
    assert EXPERIMENTAL_USER_UNKNOWN.verified is False
    assert EXPERIMENTAL_ROAMING_NOT_ALLOWED.verified is False


def test_require_verified_blocks_guesses():
    with pytest.raises(AssertionError):
        require_verified(EXPERIMENTAL_USER_UNKNOWN)
    require_verified(DIAMETER_SUCCESS)
