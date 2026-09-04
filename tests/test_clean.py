"""Tests for `repair` and the corruption patterns.

Expected values here are derivable from the source text, not guessed:
`Ch&#225;vez` is `Chávez`. METHOD 28 -- when a test fails, decide whether
the code or the test is wrong. `test_hash_number_not_an_entity` failed
twice on hand-written assertions.
"""

from __future__ import annotations

import re

import pytest

from agnews.clean import CORRUPT, PATTERNS, repair

# Only the new clean.py defines this. Step 4 runs the file against the OLD
# one, where a hard import would be a collection error -- every test
# erroring out, which is not the same signal as seven failing.
try:
    from agnews.clean import _UNREPAIRED_BY_DESIGN
except ImportError:
    _UNREPAIRED_BY_DESIGN = set()

TOKENIZER = re.compile(r"\b\w\w+\b")


def tokens(s: str) -> list[str]:
    """sklearn's default `token_pattern`, lowercased as the vectorizer does."""
    return TOKENIZER.findall(s.lower())


# --- the boundary, the reason for this session ----------------------

@pytest.mark.parametrize("dirty,clean", [
    ("Ch #225;vez", "Chávez"),
    ("Congr #232;s", "Congrès"),
    ("r #233;sum #233;", "résumé"),
    ("f #234;te", "fête"),
])
def test_letter_entity_rejoins_word(dirty: str, clean: str) -> None:
    """The `&` was replaced by a space; repair must consume it.

    Watch this fail against the 31 Aug function before fixing anything.
    A test you have never seen fail is a test you do not trust.
    """
    assert repair(dirty) == clean


def test_boundary_fix_is_token_neutral_for_hash39() -> None:
    """`#39;` is 76.8% of corrupted rows. If the boundary fix moved its
    tokens, the re-run would be measuring two changes, not one."""
    assert tokens(repair("Last season #39;s UEFA")) == ["last", "season", "uefa"]


def test_a_real_word_is_not_glued_to_the_previous_one() -> None:
    """Only the entity's own space is consumed, never a word's."""
    assert repair("the Ch #225;vez government") == "the Chávez government"


# --- entities ------------------------------------------------------

def test_bare_numeric_entity() -> None:
    assert repair("Street #39;s") == "Street's"


def test_bare_named_entity() -> None:
    assert repair("a gt; b") == "a> b"


def test_intact_entity_still_unescaped() -> None:
    """`&amp;` never lost its ampersand; it still needs unescaping."""
    assert repair("AT&amp;T") == "AT&T"


def test_intact_entity_is_not_double_escaped() -> None:
    """The lookbehind must stop `&#39;` becoming `&&#39;`."""
    assert repair("Street&#39;s") == "Street's"


def test_clean_text_untouched() -> None:
    s = "Yankees beat Red Sox 5-3 in extra innings."
    assert repair(s) == s


def test_idempotent() -> None:
    once = repair("Ch #225;vez said gt; #39;no #39;")
    assert repair(once) == once


def test_low_numbers_left_alone() -> None:
    """A jersey number is not an entity."""
    assert repair("wearing #7; tonight") == "wearing #7; tonight"


# --- the counted / repaired gap ------------------------------------

@pytest.mark.skipif(not _UNREPAIRED_BY_DESIGN, reason="old clean.py has no gap list")
@pytest.mark.parametrize("cp", sorted(_UNREPAIRED_BY_DESIGN) or ["skipped"])
def test_documented_gap_is_counted_but_not_repaired(cp: str) -> None:
    """Pins the divergence so it cannot widen silently.

    These codepoints match `CORRUPT` and survive `repair` untouched. If
    one starts being repaired, this fails and the appendix needs updating
    in the same commit.
    """
    s = f"x #{cp}; y"
    assert re.search(CORRUPT, s), f"#{cp}; is not counted as corruption"
    assert repair(s) == s, f"#{cp}; is now repaired; update _UNREPAIRED_BY_DESIGN"


def test_intact_pattern_matches_markup() -> None:
    assert re.search(PATTERNS["intact"], "&lt;strong&gt;")