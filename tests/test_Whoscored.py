"""Unittests for class soccerdata.WhoScored."""

import io
from unittest.mock import MagicMock

import pandas as pd
import pytest

from soccerdata._common import SeasonNotFoundError
from soccerdata.whoscored import WhoScored

# Unittests -------------------------------------------------------------------


def test_whoscored_missing_players(whoscored):
    assert isinstance(whoscored.read_missing_players(1485184), pd.DataFrame)


def test_whoscored_events(whoscored):
    assert isinstance(whoscored.read_events(1485184), pd.DataFrame)


def test_validate_page_unwraps_json_in_pre():
    instance = WhoScored.__new__(WhoScored)
    driver = MagicMock()
    driver.page_source = '<html><body><pre>{"tournaments": []}</pre></body></html>'
    instance._driver = driver
    assert instance._validate_page("http://example") == '{"tournaments": []}'


def test_validate_page_passes_through_html():
    instance = WhoScored.__new__(WhoScored)
    driver = MagicMock()
    driver.page_source = "<html><body><h1>hi</h1></body></html>"
    instance._driver = driver
    assert instance._validate_page("http://example") == driver.page_source


WHOSCORED_SEASONS_HTML = """
<select id="seasons">
<option value="/regions/252/tournaments/2/seasons/10316/england-premier-league-2024-2025">2024/2025</option>
<option value="/regions/252/tournaments/2/seasons/9618/england-premier-league-2023-2024">2023/2024</option>
</select>
"""


@pytest.fixture
def whoscored_cached_seasons(tmp_path, monkeypatch):
    """Return a WhoScored reader whose cached seasons page ends with 2024-2025."""

    def _reader(seasons):
        monkeypatch.setattr(WhoScored, "_init_webdriver", lambda self: None)
        reader = WhoScored("ENG-Premier League", seasons, data_dir=tmp_path)
        leagues = pd.DataFrame(
            {"region_id": [252], "league_id": [2]},
            index=pd.Index(["ENG-Premier League"], name="league"),
        )
        monkeypatch.setattr(reader, "read_leagues", lambda: leagues)
        monkeypatch.setattr(
            reader,
            "get",
            lambda url, filepath, **kwargs: io.BytesIO(WHOSCORED_SEASONS_HTML.encode()),
        )
        return reader

    return _reader


def test_read_seasons_cached(whoscored_cached_seasons):
    seasons = whoscored_cached_seasons("2024-2025").read_seasons()
    assert list(seasons.index) == [("ENG-Premier League", "2425")]
    assert seasons.loc[("ENG-Premier League", "2425"), "season_id"] == "10316"


def test_read_seasons_not_in_cache(whoscored_cached_seasons, tmp_path):
    reader = whoscored_cached_seasons(["2024-2025", "2025-2026"])
    with pytest.raises(SeasonNotFoundError, match="2526 \\(ENG-Premier League\\)") as excinfo:
        reader.read_seasons()
    assert "2425" not in str(excinfo.value)
    assert str(tmp_path / "seasons" / "ENG-Premier League.html") in str(excinfo.value)
