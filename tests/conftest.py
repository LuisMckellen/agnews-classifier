"""Shared pytest configuration.

`pytest -k letter_entity` reported `8 deselected / 0 selected` and exited
green. Zero selected is not zero failed, but it looks identical at a
glance -- the same shape of error as an identity check recorded as
"holds to one row". A run that ran nothing is not a pass.
"""

from __future__ import annotations

import pytest


def pytest_collection_modifyitems(session, config, items) -> None:
    if not items:
        raise pytest.UsageError(
            "no tests selected. A green run that executed nothing is not a "
            "pass -- check the -k expression or the test name you expected "
            "to exist."
        )