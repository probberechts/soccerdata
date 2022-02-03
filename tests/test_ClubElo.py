"""Unittests for class soccerdata.ClubElo."""
import json
from datetime import datetime, timedelta
from importlib import reload

import pandas as pd
import pytest

from soccerdata import _config as conf
from soccerdata import clubelo as foo

# Unittests -------------------------------------------------------------------
# Happy flow


def test_by_date(elo):
    assert isinstance(elo.read_by_date(), pd.DataFrame)
    assert isinstance(elo.read_by_date('2017-04-01'), pd.DataFrame)
    assert isinstance(elo.read_by_date(datetime(2017, 4, 1)), pd.DataFrame)


def test_club_hist_age(elo):
    assert isinstance(elo.read_team_history('Feyenoord'), pd.DataFrame)
    assert isinstance(elo.read_team_history('Feyenoord', 2), pd.DataFrame)
    max_age = timedelta(milliseconds=1)
    assert isinstance(elo.read_team_history('Feyenoord', max_age), pd.DataFrame)


def test_club_hist_replacement(monkeypatch, tmp_path):
    monkeypatch.setenv('SOCCERDATA_DIR', str(tmp_path))
    # no teamname_replacements.json
    reload(conf)
    assert conf.TEAMNAME_REPLACEMENTS == {}
    fp = tmp_path / "config" / "teamname_replacements.json"
    with open(fp, 'w', encoding='utf8') as outfile:
        json.dump({"Manchester City": ["Man City"]}, outfile)
    # correctly parse teamname_replacements.json
    reload(conf)
    reload(foo)
    elo = foo.ClubElo()
    assert isinstance(elo.read_team_history('Manchester City'), pd.DataFrame)


# Bad calls


def test_by_date_bad_params(elo):
    with pytest.raises(ValueError):
        elo.read_by_date('2017')
    with pytest.raises(AttributeError):
        elo.read_by_date(1 / 4)


def test_club_hist_bad_params(elo):
    with pytest.raises(TypeError):
        elo.read_team_history()  # missing argument
    with pytest.raises(ValueError):
        elo.read_team_history('FC Knudde')  # no data for team
    with pytest.raises(TypeError):
        elo.read_team_history('Feyenoord', datetime.now())  # invalid max_age type
