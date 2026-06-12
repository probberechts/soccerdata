"""Unittests for class soccerdata.WhoScored."""

from unittest.mock import MagicMock

import pandas as pd

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
