"""Entity corruption: counting and repair.

Counting and repair are two different questions and this file keeps them
visibly separate rather than accidentally separate. The 31 Aug version had
`corruption_rate` counting with `CORRUPT` and `repair` repairing with a
hand-typed `_NUM` covering a *smaller* set, with nothing recording that
they differed. See `_UNREPAIRED_BY_DESIGN` below.

Nothing executes at import (METHOD 24).
"""

from __future__ import annotations

import html
import re

# --------------------------------------------------------------------
# Counting. Produced 38,679 rows = 32.23% (data-appendix, 2 Sep).
# DO NOT EDIT without recomputing every dependent figure in one pass
# (METHOD 20). These strings are load-bearing for a published number.
# --------------------------------------------------------------------
PATTERNS = {
    "bare_num": r"#\d{2,4};",                          # `#39;`  <- `&#39;`
    "bare_named": r"\b(?:lt|gt|quot|amp|nbsp|apos);",  # `gt;`   <- `&gt;`
    "intact": r"&(?:#\d+|\w+);",                       # `&amp;` never unescaped
}

CORRUPT = PATTERNS["bare_num"] + "|" + PATTERNS["bare_named"]

# Compiled forms. Scripts import these; nothing retypes a pattern.
# collision.py and audit.py each had their own `BARE_NAMED` without the
# `\b`, which matches `salt;` and `clamp;`. Three definitions of one thing.
RE_BARE_NUM = re.compile(PATTERNS["bare_num"])
RE_BARE_NAMED = re.compile(PATTERNS["bare_named"])
RE_INTACT = re.compile(PATTERNS["intact"])
RE_CORRUPT = re.compile(CORRUPT)

# Raw HTML markup. NOTE: this requires an intact `&lt;`, which contains
# `lt;`, so "markup rows are matched by intact and by bare_named" is true
# by construction and tests nothing. The 5,241 count is real; the
# containment was never evidence.
RE_MARKUP = re.compile(r"&lt;\s*/?[A-Za-z]")

# KNOWN AND UNRESOLVED: `bare_named` has no `(?<!&)`, and there is a word
# boundary between `&` and `lt`, so it matches intact `&lt;` as well as
# bare `lt;`. All 5,241 markup rows are therefore inside the 38,679.
# The appendix says both "CORRUPT = bare entities only" (wrong) and "these
# rows are already inside the 38,679" (right). Fix the sentence, not the
# regex -- changing the regex moves a published figure.

# --------------------------------------------------------------------
# Repair.
#
# ONE change from the 31 Aug function: the boundary space. The numeric
# range below is unchanged, deliberately, so the 2x2 re-run isolates a
# single edit. Widening it is a separate change on a separate day.
# --------------------------------------------------------------------

# The `&` was not deleted, it was replaced by a space: `Ch&#225;vez`
# arrived as `Ch #225;vez`. Consuming that space is what rejoins the word.
_BOUNDARY = r" ?(?<!&)"

_REPAIRABLE_NUM = r"3[0-9]|1[0-9]{2}|2[0-9]{2}"

_NUM = re.compile(rf"{_BOUNDARY}#(?:{_REPAIRABLE_NUM});")
_NAMED = re.compile(rf"{_BOUNDARY}\b(?:lt|gt|quot|amp|nbsp|apos);")

# Codepoints the census found that `CORRUPT` counts and `repair` leaves
# alone. Listed so the gap is a decision on the page, not a silent drift.
# Roughly 96 occurrences total -- below the 0.002 paired resolution, so it
# cannot move the 2x2, but the "repaired" arm is not fully repaired and
# the write-up must not claim it is.
_UNREPAIRED_BY_DESIGN = {
    "038", "0151", "91", "93",              # zero-padded and low codepoints
    "8211", "8212", "8217", "8220", "8221",  # smart quotes and dashes
    "8364", "8482",
}


def _restore_ampersand(m: re.Match) -> str:
    return "&" + m.group(0).lstrip(" ")


def repair(s: str) -> str:
    """Reinsert dropped ampersands, then unescape.

    Consumes the space the `&` was replaced by, so `Ch #225;vez` becomes
    `Chávez` and not `Ch ávez`. Token-neutral for `#39;`: `season #39;s`
    gave `season 's` and now gives `season's`, and `\\b\\w\\w+\\b` drops the
    orphan either way. The accented entities are the only place the fix
    changes the token stream, which is exactly what the re-run measures.
    """
    s = _NUM.sub(_restore_ampersand, s)
    s = _NAMED.sub(_restore_ampersand, s)
    return html.unescape(s)


def corruption_rate(series) -> float:
    """Share of rows matching `CORRUPT`. Share of ROWS, not of occurrences
    -- the two answer different questions and 76.8% vs 94.7% is what an
    unqualified percentage costs (METHOD 18)."""
    return series.str.contains(CORRUPT, regex=True).mean()