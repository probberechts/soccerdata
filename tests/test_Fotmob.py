"""Unittests for class soccerdata.Fotmob."""

import pandas as pd
import pytest

# import soccerdata as sd
from soccerdata.fotmob import Fotmob

# Unittests -------------------------------------------------------------------


def test_read_league_table(fotmob_laliga: Fotmob) -> None:
    assert isinstance(fotmob_laliga.read_league_table(), pd.DataFrame)


def test_read_schedule(fotmob_laliga: Fotmob) -> None:
    assert isinstance(fotmob_laliga.read_schedule(), pd.DataFrame)


@pytest.mark.parametrize(
    "stat_type",
    ['Top stats', 'Shots', 'Expected goals (xG)', 'Passes', 'Defence', 'Duels', 'Discipline'],
)
def test_read_match_stats(fotmob_laliga: Fotmob, stat_type: str) -> None:
    assert isinstance(fotmob_laliga.read_match_stats(stat_type, match_id="3424405"), pd.DataFrame)
