"""Unittests for class soccerdata.WhoScored."""

import io
import json
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd

from soccerdata.whoscored import WhoScored

# Unittests -------------------------------------------------------------------


def test_whoscored_missing_players(whoscored):
    assert isinstance(whoscored.read_missing_players(1485184), pd.DataFrame)


def test_whoscored_events(whoscored):
    assert isinstance(whoscored.read_events(1485184), pd.DataFrame)


def test_whoscored_events_preserve_event_id():
    instance = WhoScored.__new__(WhoScored)
    instance.data_dir = Path(".")
    instance.read_schedule = MagicMock(
        return_value=pd.DataFrame(
            [
                {
                    "league": "ENG-Premier League",
                    "season": "2021",
                    "game": "A-B",
                    "game_id": 1485184,
                }
            ]
        )
    )
    payload = {
        "playerIdNameDictionary": {"7": "Player"},
        "home": {"teamId": 1, "name": "Home"},
        "away": {"teamId": 2, "name": "Away"},
        "events": [
            {
                "eventId": 42,
                "relatedEventId": 42,
                "playerId": 7,
                "teamId": 1,
                "qualifiers": [],
                "type": {"displayName": "Pass"},
                "period": {"displayName": "FirstHalf"},
            }
        ],
    }
    instance.get = MagicMock(return_value=io.BytesIO(json.dumps(payload).encode()))

    events = instance.read_events(match_id=1485184)

    assert isinstance(events, pd.DataFrame)
    assert events.iloc[0]["event_id"] == 42
    assert events.iloc[0]["related_event_id"] == 42


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
