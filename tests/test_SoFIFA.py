"""Unittests for class soccerdata.SoFIFA."""

import pandas as pd
import pytest

# Unittests -------------------------------------------------------------------


@pytest.mark.fails_gha
def test_sofifa_ratings(sofifa_bundesliga):
    assert isinstance(sofifa_bundesliga.read_ratings(), pd.DataFrame)
