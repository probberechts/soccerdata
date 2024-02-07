"""Unittests for class soccerdata.ESPN."""

import pandas as pd
import pytest

from soccerdata.espn import ESPN


def test_read_schedule(espn_seriea: ESPN) -> None:
    """It should return a dataframe with the schedule of the season."""
    assert isinstance(espn_seriea.read_schedule(), pd.DataFrame)


def test_read_matchsheet(espn_seriea: ESPN) -> None:
    """It should return a dataframe with the matchsheet data."""
    assert isinstance(espn_seriea.read_matchsheet(match_id=554204), pd.DataFrame)


def test_read_matchsheet_bad_id(espn_seriea: ESPN) -> None:
    """It should raise a ValueError if the selected game is not in the specified season."""
    with pytest.raises(
        ValueError, match="No games with the given IDs found for the selected seasons and leagues."
    ):
        assert isinstance(espn_seriea.read_matchsheet(match_id=123), pd.DataFrame)


def test_read_lineups(espn_seriea: ESPN) -> None:
    """It should return a dataframe with the lineups."""
    assert isinstance(espn_seriea.read_lineup(match_id=554204), pd.DataFrame)


def test_id_not_in_season(espn_seriea: ESPN) -> None:
    """It should raise a ValueError if the selected game is not in the specified season."""
    with pytest.raises(ValueError):
        assert isinstance(espn_seriea.read_lineup(match_id=123), pd.DataFrame)
