"""Unittests for class soccerdata.FotMob."""

import pandas as pd
import pytest

# import soccerdata as sd
from soccerdata.fotmob import FotMob

# Unittests -------------------------------------------------------------------


def test_read_league_table(fotmob_laliga: FotMob) -> None:
    assert isinstance(fotmob_laliga.read_league_table(), pd.DataFrame)


def test_read_schedule(fotmob_laliga: FotMob) -> None:
    assert isinstance(fotmob_laliga.read_schedule(), pd.DataFrame)


@pytest.mark.parametrize(
    "stat_type",
    ["Top stats", "Shots", "Expected goals (xG)", "Passes", "Defence", "Duels", "Discipline"],
)
def test_read_team_match_stats(fotmob_laliga: FotMob, stat_type: str) -> None:
    assert isinstance(
        fotmob_laliga.read_team_match_stats(stat_type, team="Valencia"), pd.DataFrame
    )


def test_read_team_match_stats_alt_names(fotmob_laliga: FotMob) -> None:
    # Test with Fotmob team name
    assert isinstance(
        fotmob_laliga.read_team_match_stats(stat_type="Top stats", team="Valencia"), pd.DataFrame
    )
    # Test with standardized team name
    assert isinstance(
        fotmob_laliga.read_team_match_stats(stat_type="Top stats", team="Valencia CF"),
        pd.DataFrame,
    )
