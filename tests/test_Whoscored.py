"""Unittests for class soccerdata.WhoScored."""

from unittest.mock import MagicMock

import pandas as pd
import pytest

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


def test_read_season_stages_localized_html(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test read_season_stages when 'Fixtures' anchor is missing on localized pages (issue #974)."""
    import io

    instance = WhoScored.__new__(WhoScored)
    monkeypatch.setattr(instance, "_is_complete", MagicMock(return_value=True))
    instance.data_dir = MagicMock()
    instance._leagues_dict = {"ITA-Serie A": "Serie A"}
    instance._season_ids = ["20-21"]

    df_mock = pd.DataFrame(
        [{"region_id": "108", "league_id": "5", "season_id": "7494"}],
        index=pd.MultiIndex.from_tuples([("ITA-Serie A", "20-21")], names=["league", "season"]),
    )
    monkeypatch.setattr(instance, "read_seasons", MagicMock(return_value=df_mock))

    localized_html = """
    <html lang="it">
      <head>
        <script>
          var config = {"stageId": 24500, "tournamentId": 5};
        </script>
      </head>
      <body>
        <a href="/matches/">Partite</a>
      </body>
    </html>
    """
    monkeypatch.setattr(instance, "get", MagicMock(return_value=io.StringIO(localized_html)))

    df = instance.read_season_stages(force_cache=True)
    assert not df.empty
    stage_id_val = df.loc[("ITA-Serie A", "20-21"), "stage_id"]
    if isinstance(stage_id_val, pd.Series):
        stage_id_val = stage_id_val.values[0]
    assert stage_id_val == "24500"
