from src.clean import repair
import pytest

def test_bare_numeric_entity():
    assert repair("Sony #39;s deal") == "Sony 's deal"


def test_bare_named_entity():
    assert repair("gt; Eye On Stocks") == "> Eye On Stocks"


def test_intact_entity_still_unescaped():
    assert repair("AT&amp;T") == "AT&T"
    assert repair("5 &lt; 10") == "5 < 10"


def test_clean_text_untouched():
    s = "Stocks rose 3% on Tuesday."
    assert repair(s) == s


def test_idempotent():
    once = repair("gt; #39;s")
    assert repair(once) == once


def test_low_numbers_not_treated_as_entities():
    assert repair("Ranked #12; strong") == "Ranked #12; strong"

def test_observed_entities_repaired():
    assert repair("Sony #39;s") == "Sony 's"
    assert repair("#145;quoted#146;") == "\u2018quoted\u2019"

def test_low_numbers_left_alone():
    assert repair("Ranked #12; strong") == "Ranked #12; strong"