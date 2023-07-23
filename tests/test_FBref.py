"""Unittests for class soccerdata.FBref."""
import pandas as pd
import pytest

import soccerdata as sd
from soccerdata.fbref import FBref, _concat


@pytest.mark.parametrize(
    "stat_type",
    [
        "standard",
        "keeper",
        "keeper_adv",
        "shooting",
        "passing",
        "passing_types",
        "goal_shot_creation",
        "defense",
        "possession",
        "playing_time",
        "misc",
    ],
)
def test_read_team_season_stats(fbref_ligue1: FBref, stat_type: str) -> None:
    assert isinstance(fbref_ligue1.read_team_season_stats(stat_type), pd.DataFrame)


@pytest.mark.parametrize(
    "stat_type",
    [
        "schedule",
        "shooting",
        "keeper",
        "passing",
        "passing_types",
        "goal_shot_creation",
        "defense",
        "possession",
        "misc",
    ],
)
def test_read_team_match_stats(fbref_ligue1: FBref, stat_type: str) -> None:
    assert isinstance(fbref_ligue1.read_team_match_stats(stat_type), pd.DataFrame)


@pytest.mark.parametrize(
    "stat_type",
    [
        "standard",
        "shooting",
        "passing",
        "passing_types",
        "goal_shot_creation",
        "defense",
        "possession",
        "playing_time",
        "misc",
        "keeper",
        "keeper_adv",
    ],
)
def test_read_player_season_stats(fbref_ligue1: FBref, stat_type: str) -> None:
    assert isinstance(fbref_ligue1.read_player_season_stats(stat_type), pd.DataFrame)


def test_read_schedule(fbref_ligue1: FBref) -> None:
    assert isinstance(fbref_ligue1.read_schedule(), pd.DataFrame)


@pytest.mark.parametrize(
    "stat_type",
    [
        "summary",
        "keepers",
        "passing",
        "passing_types",
        "defense",
        "possession",
        "misc",
    ],
)
def test_read_player_match_stats(fbref_ligue1: FBref, stat_type: str) -> None:
    assert isinstance(
        fbref_ligue1.read_player_match_stats(stat_type, match_id="796787da"), pd.DataFrame
    )


def test_read_events(fbref_ligue1: FBref) -> None:
    assert isinstance(fbref_ligue1.read_events(match_id="796787da"), pd.DataFrame)


def test_read_shot_events(fbref_ligue1: FBref) -> None:
    assert isinstance(fbref_ligue1.read_shot_events(match_id="796787da"), pd.DataFrame)


def test_read_lineup(fbref_ligue1: FBref) -> None:
    assert isinstance(fbref_ligue1.read_lineup(match_id="796787da"), pd.DataFrame)


def test_combine_big5() -> None:
    fbref_bigfive = sd.FBref(["Big 5 European Leagues Combined"], 2021)
    assert len(fbref_bigfive.read_leagues()) == 1
    assert len(fbref_bigfive.read_seasons()) == 1


@pytest.mark.parametrize(
    "stat_type",
    [
        "standard",
        "keeper",
        "keeper_adv",
        "shooting",
        "passing",
        "passing_types",
        "goal_shot_creation",
        "defense",
        "possession",
        "playing_time",
        "misc",
    ],
)
def test_combine_big5_team_season_stats(fbref_ligue1: FBref, stat_type: str) -> None:
    fbref_bigfive = sd.FBref(["Big 5 European Leagues Combined"], 2021)
    ligue1 = fbref_ligue1.read_team_season_stats(stat_type).loc["FRA-Ligue 1"].reset_index()
    bigfive = fbref_bigfive.read_team_season_stats(stat_type).loc["FRA-Ligue 1"].reset_index()
    cols = _concat([ligue1, bigfive], key=["season"]).columns
    ligue1.columns = cols
    bigfive.columns = cols
    pd.testing.assert_frame_equal(
        ligue1,
        bigfive,
    )


@pytest.mark.parametrize(
    "stat_type",
    [
        "standard",
        "shooting",
        "passing",
        "passing_types",
        "goal_shot_creation",
        "defense",
        "possession",
        "playing_time",
        "misc",
        "keeper",
        "keeper_adv",
    ],
)
def test_combine_big5_player_season_stats(fbref_ligue1: FBref, stat_type: str) -> None:
    fbref_bigfive = sd.FBref(["Big 5 European Leagues Combined"], 2021)
    ligue1 = fbref_ligue1.read_player_season_stats(stat_type).loc["FRA-Ligue 1"].reset_index()
    bigfive = fbref_bigfive.read_player_season_stats(stat_type).loc["FRA-Ligue 1"].reset_index()
    cols = _concat([ligue1, bigfive], key=["season"]).columns
    ligue1.columns = cols
    bigfive.columns = cols
    pd.testing.assert_frame_equal(
        ligue1,
        bigfive,
    )
