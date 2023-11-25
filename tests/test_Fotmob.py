"""Unittests for class soccerdata.FBref."""

import pandas as pd
import pytest

import soccerdata as sd
from soccerdata.fotmob import Fotmob

# Unittests -------------------------------------------------------------------

def test_read_league_table(fotmob_laliga: Fotmob) -> None:
    assert isinstance(fotmob_laliga.read_league_table(), pd.DataFrame)


def test_read_schedule(fotmob_laliga):
    assert isinstance(fotmob_laliga.read_schedule(), pd.DataFrame)


@pytest.mark.parametrize(
    "stat_type",
    [
        'Top stats',
        'Shots',
        'Expected goals (xG)',
        'Passes',
        'Defense',
        'Duels',
        'Discipline'
    ],
)
def test_read_game_match_stats(fotmob_laliga, stat_type):
    assert isinstance(
        fotmob_laliga.read_game_match_stats(stat_type, match_id="3918309"), pd.DataFrame
    )

