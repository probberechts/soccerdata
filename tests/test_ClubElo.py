"""Unittests for class soccerdata.ClubElo."""

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from soccerdata import ClubElo


def test_read_by_date(elo: ClubElo) -> None:
    """It should return a dataframe with the ELO ratings for all clubs at the specified date."""
    assert isinstance(elo.read_by_date(), pd.DataFrame)
    assert isinstance(elo.read_by_date("2017-04-01"), pd.DataFrame)
    assert isinstance(elo.read_by_date(datetime(2017, 4, 1, tzinfo=timezone.utc)), pd.DataFrame)


def test_read_by_date_bad_params(elo: ClubElo) -> None:
    """It should raise an error if the parameters are invalid."""
    with pytest.raises(ValueError, match="time data '2017' does not match format '%Y-%m-%d'"):
        elo.read_by_date("2017")
    with pytest.raises(
        TypeError, match="'date' must be a datetime object or string like 'YYYY-MM-DD'"
    ):
        elo.read_by_date(1 / 4)  # type: ignore


def test_read_team_history(elo: ClubElo) -> None:
    """It should return a dataframe with the ELO history for the specified club."""
    assert isinstance(elo.read_team_history("Feyenoord"), pd.DataFrame)
    assert isinstance(elo.read_team_history("Feyenoord", 2), pd.DataFrame)
    assert isinstance(elo.read_team_history("Feyenoord", timedelta(days=2)), pd.DataFrame)


def test_read_team_history_max_age(elo: ClubElo) -> None:
    """It should not use cached data if it is older than max_age."""
    max_age = timedelta(milliseconds=1)
    assert isinstance(elo.read_team_history("Feyenoord", max_age), pd.DataFrame)
    update_time = (
        (Path(__file__).parent / "appdata" / "data" / "ClubElo" / "Feyenoord.csv").stat().st_mtime
    )
    current_time = time.time()
    assert current_time - update_time < 5


def test_read_team_history_replacement(elo: ClubElo) -> None:
    """It should use the replacement names from teamname_replacements.json."""
    assert isinstance(elo.read_team_history("Manchester City"), pd.DataFrame)


def test_read_team_history_bad_team(elo: ClubElo) -> None:
    """It should raise an error if the team is not found."""
    with pytest.raises(ValueError, match="No data found for team FC Knudde"):
        elo.read_team_history("FC Knudde")


def test_read_team_history_bad_params(elo: ClubElo) -> None:
    """It should raise an error if the parameters are invalid."""
    with pytest.raises(TypeError, match="'max_age' must be of type int or datetime.timedelta"):
        elo.read_team_history("Feyenoord", max_age=datetime.now(tz=timezone.utc))  # type: ignore
