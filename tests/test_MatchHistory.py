"""Unittests for class soccerdata.MatchHistory."""

import pandas as pd


# Unittests -------------------------------------------------------------------
# Reader
def test_epl_2y(match_epl_2y):
    df = match_epl_2y.read_games()
    assert isinstance(df, pd.DataFrame)
    assert len(df.index.get_level_values("season").unique()) == 2
