"""Unittests for soccerdata._common."""

import json
from datetime import datetime, timezone
from io import StringIO
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import time_machine

import soccerdata
from soccerdata._common import (
    BaseRequestsReader,
    SeasonCode,
    add_alt_team_names,
    add_standardized_team_name,
    make_game_id,
    standardize_colnames,
)

# _download_and_save


@pytest.fixture
def mock_tls_client():
    # Patch the session's get method
    # Change 'your_module' to the actual module name
    with patch("tls_requests.Client.get") as mock_get:

        def _return_csv(content="Rank,Club,Country\n1,Barcelona,ESP"):
            mock_resp = MagicMock()
            mock_resp.content = content.encode("utf-8")
            mock_resp.status_code = 200
            mock_resp.raise_for_status = lambda: None
            mock_get.return_value = mock_resp
            return mock_get

        def _return_js_var(var_name="statData", data={"key": "value"}):
            """
            Mimics: var name = JSON.parse('\x7b\x22key\x22\x3a\x22value\x22\x7d')
            The regex in the reader expects string-escaped content inside single quotes.
            """
            # 1. Convert dict to JSON string
            json_str = json.dumps(data)
            # 2. Escape double quotes so it survives being wrapped in single quotes
            # and works with the reader's .decode("unicode_escape")
            escaped_json = json_str.replace('"', '\\"')

            html = f"var {var_name} = JSON.parse('{escaped_json}')"

            mock_resp = MagicMock()
            mock_resp.content = html.encode("utf-8")
            mock_resp.status_code = 200
            mock_resp.raise_for_status = lambda: None
            mock_get.return_value = mock_resp
            return mock_get

        mock_get.return_csv = _return_csv
        mock_get.return_js_var = _return_js_var
        yield mock_get


# --- Tests ---


def test_download_and_save_not_cached(tmp_path, mock_tls_client):
    # Setup mock
    mock_tls_client.return_csv()

    reader = BaseRequestsReader()
    url = "http://api.clubelo.com/Barcelona"
    filepath = tmp_path / "Barcelona.csv"
    data = reader.get(url, filepath)

    assert isinstance(pd.read_csv(data), pd.DataFrame)
    assert filepath.exists()


def test_download_and_save_cached(tmp_path, mock_tls_client):
    # Setup mock
    mock_tls_client.return_csv()

    reader = BaseRequestsReader()
    url = "http://api.clubelo.com/Barcelona"
    filepath = tmp_path / "Barcelona.csv"

    # First call: triggers the mock/download
    reader.get(url, filepath)
    # Second call: should read from disk
    data = reader.get(url, filepath)

    assert isinstance(pd.read_csv(data), pd.DataFrame)
    # Verify the network was only hit once
    assert mock_tls_client.call_count == 1


def test_download_and_save_no_cache(tmp_path, mock_tls_client):
    # Setup mock with at least 2 rows of data
    mock_tls_client.return_csv("Col1,Col2\nVal1,Val2\nVal3,Val4")

    reader = BaseRequestsReader(no_cache=True)
    url = "http://api.clubelo.com/Barcelona"
    filepath = tmp_path / "Barcelona.csv"

    # Pre-populate with bogus data
    filepath.write_text("bogus")

    data = reader.get(url, filepath)
    # If no_cache=True, it should have overwritten "bogus" with our 2-row CSV
    assert len(pd.read_csv(data)) >= 2


def test_download_and_save_no_store_no_filepath(mock_tls_client):
    # Setup mock
    mock_tls_client.return_csv()

    reader = BaseRequestsReader(no_store=True)
    url = "http://api.clubelo.com/Barcelona"
    data = reader.get(url, filepath=None)

    assert isinstance(pd.read_csv(data), pd.DataFrame)


def test_download_and_save_no_cache_filepath(tmp_path, mock_tls_client):
    # Setup mock
    mock_tls_client.return_csv()

    reader = BaseRequestsReader(no_store=True)
    url = "http://api.clubelo.com/Barcelona"
    filepath = tmp_path / "Barcelona.csv"

    data = reader.get(url, filepath)

    assert isinstance(pd.read_csv(data), pd.DataFrame)
    # no_store=True means the file should be deleted or never written
    assert not filepath.exists()


def test_download_and_save_variable_no_store_no_filepath(mock_tls_client):
    # Setup mock using the JS variable helper
    mock_tls_client.return_js_var(var_name="statData", data={"player": "Messi", "goals": 10})

    reader = BaseRequestsReader(no_store=True)
    url = "https://understat.com/"
    data = reader.get(url, filepath=None, var="statData")

    stats = json.load(data)
    assert isinstance(stats, dict)
    # the result is wrapped in {var_name: data}
    assert stats["statData"]["player"] == "Messi"


# def test_download_and_save_requests_tor(tmp_path):
#     url = "https://check.torproject.org/api/ip"
#     reader = BaseRequestsReader(proxy=None)
#     ip_without_proxy = reader.get(url, tmp_path / "myip.txt")
#     ip_without_proxy = json.load(ip_without_proxy)
#     proxy_reader = BaseRequestsReader(proxy="tor")
#     ip_with_proxy = proxy_reader.get(url, tmp_path / "myproxyip.txt")
#     ip_with_proxy = json.load(ip_with_proxy)
#     assert ip_without_proxy["IP"] != ip_with_proxy["IP"]
#     assert ip_with_proxy["IsTor"]
#
#
# def test_download_and_save_selenium_tor(tmp_path):
#     url = "https://check.torproject.org/api/ip"
#     reader = BaseSeleniumReader(proxy=None).get(url, tmp_path / "myip.txt")
#     ip_without_proxy = html.parse(reader).xpath("//pre")[0].text
#     ip_without_proxy = json.loads(ip_without_proxy)
#     proxy_reader = BaseSeleniumReader(proxy="tor").get(url, tmp_path / "myproxyip.txt")
#     ip_with_proxy = html.parse(proxy_reader).xpath("//pre")[0].text
#     ip_with_proxy = json.loads(ip_with_proxy)
#     assert ip_without_proxy["IP"] != ip_with_proxy["IP"]
#     assert ip_with_proxy["IsTor"]
#

# make_game_id


def test_make_game_id():
    s = pd.Series(
        {
            "date": datetime(1993, 7, 30, tzinfo=timezone.utc),
            "home_team": "Barcelona",
            "away_team": "Real Madrid",
        }
    )
    game_id = make_game_id(s)
    assert game_id == "1993-07-30 Barcelona-Real Madrid"


# add_alt_team_names


def test_add_alt_team_names():
    # "Valencia" is replaced by "Valencia CF"
    assert add_alt_team_names("Valencia CF") == {"Valencia", "Valencia CF"}
    # "Arsenal" is not replaced
    assert add_alt_team_names("Arsenal") == {"Arsenal"}


def test_add_standardize_team_name():
    # "Valencia" is replaced by "Valencia CF"
    assert add_standardized_team_name("Valencia") == {"Valencia", "Valencia CF"}
    # "Real Madrid" is not replaced
    assert add_standardized_team_name("Arsenal") == {"Arsenal"}


# standardize_colnames


def test_standardize_colnames():
    df = pd.DataFrame(
        columns=[
            "First Test",
            "SecondTest",
            "thirdTest",
            "Fourthtest",
            "Fifth-test",
            "TestSix",
        ]
    )
    df = standardize_colnames(
        df, cols=["First Test", "SecondTest", "thirdTest", "Fourthtest", "Fifth-test"]
    )
    assert df.columns.tolist() == [
        "first_test",
        "second_test",
        "third_test",
        "fourthtest",
        "fifth_test",
        "TestSix",
    ]


# is_complete


def test_is_complete():
    reader = BaseRequestsReader(no_store=True)
    with time_machine.travel(datetime(2020, 12, 25, 1, 24, tzinfo=timezone.utc)):
        assert reader._is_complete("ENG-Premier League", "1920")
        assert not reader._is_complete("ENG-Premier League", "2021")
    with time_machine.travel(datetime(2021, 2, 25, 1, 24, tzinfo=timezone.utc)):
        assert reader._is_complete("ENG-Premier League", "1920")
        assert not reader._is_complete("ENG-Premier League", "2021")
    with time_machine.travel(datetime(2021, 7, 1, 1, 24, tzinfo=timezone.utc)):
        assert reader._is_complete("ENG-Premier League", "1920")
        assert reader._is_complete("ENG-Premier League", "2021")
        assert not reader._is_complete("ENG-Premier League", "2122")


def test_is_complete_default_value(mocker):
    mocker.patch.object(soccerdata._common, "LEAGUE_DICT", {"FAKE-Dummy League": {}})
    reader = BaseRequestsReader(no_store=True)
    with time_machine.travel(datetime(2020, 12, 25, 1, 24, tzinfo=timezone.utc)):
        assert reader._is_complete("FAKE-Dummy League", "1920")


def test_is_complete_undefined_league(mocker):  # noqa: ARG001
    reader = BaseRequestsReader(no_store=True)
    with pytest.raises(
        ValueError,
        match="Invalid league 'FAKE-Dummy League'",
    ):
        reader._is_complete("FAKE-Dummy League", "1920")


# Season codes
def test_season_pattern1a():
    assert SeasonCode.MULTI_YEAR.parse("9495") == "9495"
    assert SeasonCode.SINGLE_YEAR.parse("9495") == "1994"


def test_season_pattern1a_warn():
    with pytest.warns(UserWarning) as record:
        assert SeasonCode.MULTI_YEAR.parse("2021") == "2021"

    # check that only one warning was raised
    assert len(record) == 1
    # check that the message matches
    msg = 'Season id "2021" is ambiguous: interpreting as "20-21"'
    assert record[0].message.args[0] == msg  # type: ignore


def test_season_pattern1b():
    my_season = check_post = "1998"
    assert SeasonCode.MULTI_YEAR.parse(my_season) == "9899"
    assert SeasonCode.SINGLE_YEAR.parse(my_season) == "1998"
    assert my_season == check_post


def test_season_pattern1c():
    assert SeasonCode.MULTI_YEAR.parse("1999") == "9900"
    assert SeasonCode.SINGLE_YEAR.parse("1999") == "1999"


def test_season_pattern2():
    assert SeasonCode.MULTI_YEAR.parse("11") == "1112"
    assert SeasonCode.SINGLE_YEAR.parse("11") == "2011"
    assert SeasonCode.MULTI_YEAR.parse("99") == "9900"
    assert SeasonCode.SINGLE_YEAR.parse("99") == "1999"


def test_season_pattern3():
    assert SeasonCode.MULTI_YEAR.parse("2011-2012") == "1112"
    assert SeasonCode.SINGLE_YEAR.parse("2011-2012") == "2011"
    assert SeasonCode.MULTI_YEAR.parse("1999-2000") == "9900"
    assert SeasonCode.SINGLE_YEAR.parse("1999-2000") == "1999"


def test_season_pattern4():
    assert SeasonCode.MULTI_YEAR.parse("2011-12") == "1112"
    assert SeasonCode.SINGLE_YEAR.parse("2011-12") == "2011"
    assert SeasonCode.MULTI_YEAR.parse("1999-00") == "9900"
    assert SeasonCode.SINGLE_YEAR.parse("1999-00") == "1999"


def test_season_pattern5():
    assert SeasonCode.MULTI_YEAR.parse("13-14") == "1314"
    assert SeasonCode.SINGLE_YEAR.parse("13-14") == "2013"
