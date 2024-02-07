"""Unittests for class soccerdata.SoFIFA."""

import pandas as pd

from soccerdata.sofifa import SoFIFA


def test_read_team_ratings(sofifa_bundesliga: SoFIFA) -> None:
    """It should return a dataframe with the team ratings."""
    assert isinstance(sofifa_bundesliga.read_team_ratings(), pd.DataFrame)


def test_read_player_ratings(sofifa_bundesliga: SoFIFA) -> None:
    """It should return a dataframe with the player ratings."""
    assert isinstance(sofifa_bundesliga.read_player_ratings(player=189596), pd.DataFrame)
