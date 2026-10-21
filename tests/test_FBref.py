"""Unittests for class soccerdata.FBref."""

import io
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

import soccerdata as sd
from soccerdata._common import SeasonNotFoundError
from soccerdata.fbref import FBref, _concat


def test_available_leagues() -> None:
    assert sd.FBref.available_leagues() == [
        "Big 5 European Leagues Combined",
        "ENG-Premier League",
        "ESP-La Liga",
        "FRA-Ligue 1",
        "GER-Bundesliga",
        "INT-European Championship",
        "INT-Women's World Cup",
        "INT-World Cup",
        "ITA-Serie A",
    ]


@pytest.mark.parametrize(
    "stat_type",
    [
        "standard",
        "keeper",
        "shooting",
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
        "misc",
    ],
)
def test_read_team_match_stats(fbref_ligue1: FBref, stat_type: str) -> None:
    assert isinstance(fbref_ligue1.read_team_match_stats(stat_type), pd.DataFrame)


def test_read_team_match_stats_alt_names(fbref_ligue1: FBref) -> None:
    # Test with FBref team name
    assert isinstance(
        fbref_ligue1.read_team_match_stats(stat_type="schedule", team="Marseille"),
        pd.DataFrame,
    )
    # Test with standardized team name
    assert isinstance(
        fbref_ligue1.read_team_match_stats(stat_type="schedule", team="Olympique de Marseille"),
        pd.DataFrame,
    )


@pytest.mark.parametrize(
    "stat_type",
    [
        "standard",
        "shooting",
        "playing_time",
        "misc",
        "keeper",
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
    ],
)
def test_read_player_match_stats(fbref_ligue1: FBref, stat_type: str) -> None:
    assert isinstance(
        fbref_ligue1.read_player_match_stats(stat_type, match_id="796787da"), pd.DataFrame
    )


def test_read_events(fbref_ligue1: FBref) -> None:
    assert isinstance(fbref_ligue1.read_events(match_id="796787da"), pd.DataFrame)


def test_read_events_yellow_for_manager() -> None:
    """When a yellow card given to the manager, there is no <a> tag."""
    fbref_laliga = sd.FBref("ESP-La Liga", "23-24")
    events = fbref_laliga.read_events(match_id="e8867e6b")
    yellow_cards = events[events["event_type"] == "yellow_card"]
    assert "Pepe Bordalás" in yellow_cards["player1"].tolist()


def test_missing_events() -> None:
    fbref = sd.FBref("FRA-Ligue 1", "19-20")
    events = fbref.read_events(match_id="1d845950")
    assert len(events) == 0


def test_read_lineup(fbref_ligue1: FBref) -> None:
    assert isinstance(fbref_ligue1.read_lineup(match_id="796787da"), pd.DataFrame)


def test_concat() -> None:
    df1 = pd.DataFrame(
        columns=pd.MultiIndex.from_tuples(
            [("Unnamed: a", "player"), ("Performance", "Goals"), ("Performance", "Assists")]
        )
    )
    df2 = pd.DataFrame(
        columns=pd.MultiIndex.from_tuples(
            [("Unnamed: a", "player"), ("Unnamed: b", "Goals"), ("Performance", "Assists")]
        )
    )
    df3 = pd.DataFrame(
        columns=pd.MultiIndex.from_tuples(
            [("Unnamed: a", "player"), ("Goals", "Unnamed: b"), ("Performance", "Assists")]
        )
    )
    res = _concat([df1, df2, df3], key=["player"])
    assert res.columns.equals(
        pd.MultiIndex.from_tuples(
            [("player", ""), ("Performance", "Goals"), ("Performance", "Assists")]
        )
    )
    res = _concat([df3, df1, df2], key=["player"])
    assert res.columns.equals(
        pd.MultiIndex.from_tuples(
            [("player", ""), ("Performance", "Goals"), ("Performance", "Assists")]
        )
    )


def test_concat_with_forfeited_game() -> None:
    fbref_seriea = sd.FBref(["ITA-Serie A"], 2021)
    df_1 = fbref_seriea.read_player_match_stats(match_id=["e0a20cfe", "34e95e35"])
    df_2 = fbref_seriea.read_player_match_stats(match_id=["e0a20cfe", "a3e10e13"])
    assert isinstance(df_1, pd.DataFrame)
    assert isinstance(df_2, pd.DataFrame)
    # Regardless of the order in which the matches are read, the result should be the same.
    assert df_1.columns.equals(df_2.columns)


def test_combine_big5() -> None:
    fbref_bigfive = sd.FBref(["Big 5 European Leagues Combined"], 2021)
    assert len(fbref_bigfive.read_leagues(split_up_big5=False)) == 1
    assert len(fbref_bigfive.read_seasons(split_up_big5=False)) == 1
    assert len(fbref_bigfive.read_leagues(split_up_big5=True)) == 5
    assert len(fbref_bigfive.read_seasons(split_up_big5=True)) == 5
    # by default, split_up_big5 should be False
    assert len(fbref_bigfive.read_leagues()) == 1
    assert len(fbref_bigfive.read_seasons()) == 1


@pytest.mark.parametrize(
    "stat_type",
    [
        "standard",
        "keeper",
        "shooting",
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
        "playing_time",
        "misc",
        "keeper",
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


FBREF_SEASONS_HTML = """
<table id="seasons"><thead><tr>
<th data-stat="year_id">Season</th><th>Competition Name</th><th>Squads</th>
</tr></thead><tbody>
<tr><th data-stat="year_id"><a href="/en/comps/9/2024-2025/2024-2025-Premier-League-Stats">2024-2025</a></th><td>Premier League</td><td>20</td></tr>
<tr><th data-stat="year_id"><a href="/en/comps/9/2023-2024/2023-2024-Premier-League-Stats">2023-2024</a></th><td>Premier League</td><td>20</td></tr>
</tbody></table>
"""


@pytest.fixture
def fbref_cached_seasons(tmp_path, monkeypatch):
    """Return an FBref reader whose cached seasons page ends with 2024-2025."""

    def _reader(seasons):
        monkeypatch.setattr(FBref, "_init_webdriver", lambda self: None)
        reader = FBref("ENG-Premier League", seasons, data_dir=tmp_path)
        leagues = pd.DataFrame(
            {"url": ["/en/comps/9/history/Premier-League-Seasons"]},
            index=pd.Index(["ENG-Premier League"], name="league"),
        )
        monkeypatch.setattr(reader, "read_leagues", lambda split_up_big5=False: leagues)
        monkeypatch.setattr(
            reader, "get", lambda url, filepath, **kwargs: io.BytesIO(FBREF_SEASONS_HTML.encode())
        )
        return reader

    return _reader


def test_read_seasons_cached(fbref_cached_seasons: Callable[[str], FBref]) -> None:
    seasons = fbref_cached_seasons("2024-2025").read_seasons()
    assert list(seasons.index) == [("ENG-Premier League", "2425")]


def test_read_seasons_not_in_cache(
    fbref_cached_seasons: Callable[[str], FBref], tmp_path: Path
) -> None:
    reader = fbref_cached_seasons("2025-2026")
    with pytest.raises(SeasonNotFoundError, match="2526 \\(ENG-Premier League\\)") as excinfo:
        reader.read_seasons()
    assert "no_cache=True" in str(excinfo.value)
    assert str(tmp_path / "seasons_ENG-Premier League.html") in str(excinfo.value)
    # still a KeyError, as before
    assert isinstance(excinfo.value, KeyError)
