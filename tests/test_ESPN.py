"""Unittests for class soccerdata.ESPN."""

import pandas as pd
import pytest

# Unittests -------------------------------------------------------------------


def test_espn_schedule(espn_seriea):
    assert isinstance(espn_seriea.read_schedule(), pd.DataFrame)


def test_espn_matchsheet(espn_seriea):
    assert isinstance(espn_seriea.read_matchsheet(554204), pd.DataFrame)


def test_espn_lineups(espn_seriea):
    assert isinstance(espn_seriea.read_lineup(554204), pd.DataFrame)


def test_espn_id_not_in_season(espn_seriea):
    with pytest.raises(ValueError):
        assert isinstance(espn_seriea.read_lineup(123), pd.DataFrame)
