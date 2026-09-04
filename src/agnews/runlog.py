"""Environment stamp for every result row (METHOD 25).

Lifted verbatim from the `git_sha` in floor.py, with one addition: a SHA
recorded from a dirty working tree does not identify the code that ran.
The flag makes that visible instead of silently wrong.

Nothing executes at import (METHOD 24).
"""

from __future__ import annotations

import subprocess

import sklearn


def _git(*args: str) -> str | None:
    try:
        return subprocess.check_output(["git", *args], text=True).strip()
    except Exception:
        return None


def git_sha() -> str:
    return _git("rev-parse", "--short", "HEAD") or "unknown"


def git_dirty() -> bool | None:
    """True if tracked files differ from HEAD. None if git is unavailable."""
    out = _git("status", "--porcelain")
    return None if out is None else bool(out)


def stamp() -> dict:
    """Attach to every result row. Flat, so it merges into a JSONL record."""
    return {
        "git_sha": git_sha(),
        "git_dirty": git_dirty(),
        "sklearn": sklearn.__version__,
    }