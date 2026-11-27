"""Unittests for class soccerdata.FootballCharts."""

import io
import json

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from soccerdata.footballcharts import ARCHIVE_COLUMNS, FOOTBALLCHARTS_API, FootballCharts


def test_read_leagues(footballcharts_epl_2324: FootballCharts) -> None:
    leagues = footballcharts_epl_2324.read_leagues()
    assert isinstance(leagues, pd.DataFrame)
    assert len(leagues) == 1
    assert leagues.loc["ENG-Premier League", "league_id"] == "premier"


def test_read_seasons(footballcharts_epl_2324: FootballCharts) -> None:
    seasons = footballcharts_epl_2324.read_seasons()
    assert isinstance(seasons, pd.DataFrame)
    assert len(seasons) == 1
    assert seasons.iloc[0]["season_id"] == "2023-2024"
    assert seasons.iloc[0]["source"] == "archive"


def test_read_seasons_empty() -> None:
    seasons = FootballCharts("ENG-Premier League", "90-91").read_seasons()
    assert isinstance(seasons, pd.DataFrame)
    assert len(seasons) == 0


def test_read_schedule(footballcharts_epl_2324: FootballCharts) -> None:
    schedule = footballcharts_epl_2324.read_schedule()
    assert isinstance(schedule, pd.DataFrame)
    assert len(schedule) == 380
    assert (
        schedule[["home_score", "away_score", "ht_home_score", "ht_away_score"]]
        .notna()
        .all()
        .all()
    )
    # every goal of the archived seasons has a minute
    goals = schedule["home_score"] + schedule["away_score"]
    assert (schedule["goal_minutes"].apply(len) == goals).all()
    game = schedule.loc[("ENG-Premier League", "2324", "2023-08-11 Burnley-Manchester City")]
    assert game["date"] == pd.Timestamp("2023-08-11")
    assert (game["home_score"], game["away_score"]) == (0, 3)
    assert (game["ht_home_score"], game["ht_away_score"]) == (0, 2)
    assert game["first_goal_minute"] == 4
    assert game["goal_minutes"] == [4, 36, 75]


def test_read_schedule_from_api(mocker: MockerFixture) -> None:
    """The seasons that are not archived yet are read from the API."""
    responses = {
        "leagues/premier/results/?season=2026-2027": {
            "current_season": "2026-2027",
            "matches": [
                {
                    "date": "2026-08-21",
                    "time": "20:00:00",
                    "homeTeam": "Arsenal",
                    "awayTeam": "Coventry",
                    "score": "3:0",
                    "ht_result": "2:0",
                    "first_goal_time": 45,
                    "first_goal_time_extra": 2,
                },
                {
                    "date": "2026-08-22",
                    "time": None,
                    "homeTeam": "Leeds",
                    "awayTeam": "Everton",
                    "score": "0:0",
                    "ht_result": "0:0",
                    "first_goal_time": None,
                    "first_goal_time_extra": None,
                },
            ],
        },
        "leagues/premier/fixtures/": {
            "matches": [
                {
                    "match_date": "2026-10-10",
                    "time": "11:30",
                    "home_team": "Arsenal",
                    "away_team": "Leeds",
                },
            ],
        },
    }

    def get(url: str, *args: object, **kwargs: object) -> io.BytesIO:
        return io.BytesIO(json.dumps(responses[url.removeprefix(FOOTBALLCHARTS_API)]).encode())

    index = {
        "leagues": [
            {"league": "premier", "country": "England", "url": None, "seasons": ["2026-2027"]}
        ]
    }
    mocker.patch.object(FootballCharts, "_read_league_index", return_value=index)
    mocker.patch.object(
        FootballCharts, "_read_archive", return_value=pd.DataFrame(columns=ARCHIVE_COLUMNS)
    )
    mocker.patch.object(FootballCharts, "get", side_effect=get)

    fc = FootballCharts("ENG-Premier League", "2627", no_store=True)
    assert fc.read_seasons().iloc[0]["source"] == "api"
    schedule = fc.read_schedule().droplevel(["league", "season"])
    assert len(schedule) == 3
    played = schedule.loc["2026-08-21 Arsenal-Coventry"]
    assert played["first_goal_minute"] == 47
    assert pd.isna(played["goal_minutes"])
    goalless = schedule.loc["2026-08-22 Leeds-Everton"]
    assert pd.isna(goalless["first_goal_minute"])
    assert goalless["goal_minutes"] == []
    upcoming = schedule.loc["2026-10-10 Arsenal-Leeds"]
    assert pd.isna(upcoming["home_score"])
    assert pd.isna(upcoming["away_score"])


def test_read_league_table(footballcharts_epl_2324: FootballCharts) -> None:
    league_table = footballcharts_epl_2324.read_league_table()
    assert isinstance(league_table, pd.DataFrame)
    assert len(league_table) == 20
    assert (league_table["MP"] == 38).all()
    champion = league_table.iloc[0]
    assert champion["team"] == "Manchester City"
    assert champion["Pts"] == 91


@pytest.mark.parametrize(
    ("minute", "expected"),
    [("4", 4), ("45+2", 47), ("94", 94)],
)
def test_minute(minute: str, expected: int) -> None:
    from soccerdata.footballcharts import _minute

    assert _minute(minute) == expected
