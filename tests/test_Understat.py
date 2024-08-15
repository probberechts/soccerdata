"""Unittests for class soccerdata.Understat."""

import pandas as pd
import pytest

from soccerdata.understat import Understat


def test_read_leagues(understat_epl_1516: Understat) -> None:
    leagues = understat_epl_1516.read_leagues()
    assert isinstance(leagues, pd.DataFrame)
    assert len(leagues) == 1


def test_read_seasons(understat_epl_1516: Understat) -> None:
    seasons = understat_epl_1516.read_seasons()
    assert isinstance(seasons, pd.DataFrame)
    assert len(seasons) == 1


def test_read_seasons_empty(understat_epl_9091: Understat) -> None:
    seasons = understat_epl_9091.read_seasons()
    assert isinstance(seasons, pd.DataFrame)
    assert len(seasons) == 0


def test_read_schedule(understat_epl_1516: Understat) -> None:
    schedule = understat_epl_1516.read_schedule()
    assert isinstance(schedule, pd.DataFrame)
    assert len(schedule) == 380


def test_read_team_match_stats(understat_epl_1516: Understat) -> None:
    team_match_stats = understat_epl_1516.read_team_match_stats()
    assert isinstance(team_match_stats, pd.DataFrame)
    assert len(team_match_stats) == 380


def test_read_player_season_stats(understat_epl_1516: Understat) -> None:
    player_season_stats = understat_epl_1516.read_player_season_stats()
    assert isinstance(player_season_stats, pd.DataFrame)
    assert len(player_season_stats) == 550


def test_read_player_match_stats(understat_epl_1516: Understat) -> None:
    player_match_stats = understat_epl_1516.read_player_match_stats()
    assert isinstance(player_match_stats, pd.DataFrame)


def test_read_player_match_stats_new_columns(understat_epl_1516: Understat) -> None:
    player_match_stats = understat_epl_1516.read_player_match_stats()
    assert "assists" in player_match_stats.columns
    assert "key_passes" in player_match_stats.columns
    assert "yellow_cards" in player_match_stats.columns
    assert "red_cards" in player_match_stats.columns


def test_read_shots(understat_epl_1516: Understat) -> None:
    shots_all = understat_epl_1516.read_shot_events()
    assert isinstance(shots_all, pd.DataFrame)
    assert len(shots_all) == 9_819
    shots_utd_bou = understat_epl_1516.read_shot_events(460)
    assert isinstance(shots_utd_bou, pd.DataFrame)
    assert len(shots_utd_bou) == 20
    with pytest.raises(
        ValueError, match="No matches found with the given IDs in the selected seasons."
    ):
        understat_epl_1516.read_shot_events(42)
