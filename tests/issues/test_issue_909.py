"""Tests for issue #909: Locale-independent month parsing."""

import locale
from datetime import datetime, timezone

import pytest
import time_machine

from soccerdata._common import BaseRequestsReader, SeasonCode


@pytest.fixture
def non_english_time_locale():
    """Switch LC_TIME to a non-English locale for the test, then always restore it.

    Skips the test if no supported non-English locale is installed on this machine,
    rather than failing for an unrelated reason.
    """
    original = locale.setlocale(locale.LC_TIME)
    candidates = (
        "es_ES.UTF-8",
        "es_ES",
        "nl_NL.UTF-8",
        "nl_NL.utf8",
        "nl_NL",
        "de_DE.UTF-8",
        "de_DE.utf8",
        "de_DE",
        "fr_FR.UTF-8",
        "fr_FR.utf8",
        "fr_FR",
        "it_IT.UTF-8",
        "it_IT.utf8",
        "it_IT",
        "Spanish_Spain.1252",
        "German_Germany.1252",
        "French_France.1252",
        "Dutch_Netherlands.1252",
    )
    for candidate in candidates:
        try:
            locale.setlocale(locale.LC_TIME, candidate)
            break
        except locale.Error:
            continue
    else:
        pytest.skip("No non-English LC_TIME locale available on this machine")
    try:
        yield
    finally:
        locale.setlocale(locale.LC_TIME, original)


def test_season_code_from_league_is_locale_independent(non_english_time_locale):
    assert SeasonCode.from_league("ENG-Premier League") == SeasonCode.MULTI_YEAR


def test_is_complete_is_locale_independent(non_english_time_locale):
    reader = BaseRequestsReader(no_store=True)
    with time_machine.travel(datetime(2021, 7, 1, 1, 24, tzinfo=timezone.utc)):
        assert reader._is_complete("ENG-Premier League", "1920")
        assert not reader._is_complete("ENG-Premier League", "2122")
