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


def test_shot_assist_player_id_matches_player_stats(monkeypatch: pytest.MonkeyPatch) -> None:
    # Recorded subset of https://understat.com/getMatchData/82 (2026-09-22).
    # This match also appears in docs/datasources/Understat.ipynb.
    roster_player = {
        "id": "548657",
        "player_id": "890",
        "player": "Gabriel Agbonlahor",
        "team_id": "71",
        "position": "FW",
        "positionOrder": "15",
        "time": "90",
        "goals": "0",
        "own_goals": "0",
        "shots": "2",
        "xG": "0.13016000390052795",
        "xGChain": "0.24382799863815308",
        "xGBuildup": "0",
        "assists": "0",
        "xA": "0.11366800218820572",
        "key_passes": "1",
        "yellow_card": "0",
        "red_card": "0",
    }
    shot = {
        "id": "487144",
        "player_id": "668",
        "player": "Idrissa Gueye",
        "player_assisted": "Gabriel Agbonlahor",
        "h_a": "a",
        "a_team": "Aston Villa",
        "date": "2015-08-08 18:00:00",
        "minute": "47",
        "xG": "0.11366800218820572",
        "X": "0.8830000305175781",
        "Y": "0.5609999847412109",
        "shotType": "LeftFoot",
        "situation": "OpenPlay",
        "result": "SavedShot",
    }
    match_data = {
        "match_info": {
            "h": "73",
            "a": "71",
            "team_h": "Bournemouth",
            "team_a": "Aston Villa",
        },
        "rostersData": {"h": {}, "a": {roster_player["id"]: roster_player}},
        "shotsData": {"h": [], "a": [shot]},
    }
    schedule = pd.DataFrame(
        [
            {
                "league": "ENG-Premier League",
                "season": "1516",
                "game": "2015-08-08 Bournemouth-Aston Villa",
                "league_id": 1,
                "season_id": 2015,
                "game_id": 82,
                "url": "https://understat.com/match/82",
            }
        ]
    ).set_index(["league", "season", "game"])
    monkeypatch.setattr(Understat, "_init_session", lambda *args: None)
    understat = Understat("ENG-Premier League", "15-16", no_store=True)
    monkeypatch.setattr(understat, "read_schedule", lambda **kwargs: schedule)
    monkeypatch.setattr(understat, "_read_match", lambda *args: match_data)

    assert roster_player["id"] != roster_player["player_id"]
    player = understat.read_player_match_stats(82).reset_index().iloc[0]
    assist = understat.read_shot_events(82).iloc[0]

    assert player["player_id"] == int(roster_player["player_id"])
    assert assist["assist_player"] == player["player"]
    assert assist["assist_player_id"] == player["player_id"]
