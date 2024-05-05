"""Unittests for class soccerdata.Sofascore."""

import pandas as pd

from soccerdata.sofascore import Sofascore


def test_read_leagues(sofascore_epl_1516: Sofascore) -> None:
    leagues = sofascore_epl_1516.read_leagues()
    assert isinstance(leagues, pd.DataFrame)
    assert len(leagues) == 1


def test_read_seasons(sofascore_epl_1516: Sofascore) -> None:
    seasons = sofascore_epl_1516.read_seasons()
    assert isinstance(seasons, pd.DataFrame)
    assert len(seasons) == 1


def test_read_seasons_empty() -> None:
    sofascore_instance = Sofascore("ENG-Premier League", "90-91")
    seasons = sofascore_instance.read_seasons()
    assert isinstance(seasons, pd.DataFrame)
    assert len(seasons) == 0


def test_read_schedule(sofascore_epl_1516: Sofascore) -> None:
    schedule = sofascore_epl_1516.read_schedule()
    assert isinstance(schedule, pd.DataFrame)
    assert len(schedule) == 380


def test_read_league_table(sofascore_epl_1516: Sofascore) -> None:
    league_table = sofascore_epl_1516.read_league_table()
    assert isinstance(league_table, pd.DataFrame)
    assert len(league_table) == 20
