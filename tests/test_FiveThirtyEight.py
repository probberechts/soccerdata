"""Unittests for class soccerdata.FiveThirtyEight."""

import pandas as pd
import pytest

import soccerdata as foo

# Unittests -------------------------------------------------------------------
# Happy flow


def test_five38_league_ids(five38_laliga):
    assert isinstance(five38_laliga._selected_leagues, dict)


def test_five38_leagues(five38_laliga):
    assert isinstance(five38_laliga.read_leagues(), pd.DataFrame)


def test_five38_games(five38_laliga):
    assert isinstance(five38_laliga.read_games(), pd.DataFrame)


def test_five38_forecasts(five38_laliga):
    assert isinstance(five38_laliga.read_forecasts(), pd.DataFrame)


def test_five38_clinches(five38_laliga):
    assert isinstance(five38_laliga.read_clinches(), pd.DataFrame)


def test_five38_league_ids_ll(five38_laliga):
    assert isinstance(five38_laliga._selected_leagues, dict)


def test_five38_leagues_ll(five38_laliga):
    assert isinstance(five38_laliga.read_leagues(), pd.DataFrame)


def test_five38_games_ll(five38_laliga):
    assert isinstance(five38_laliga.read_games(), pd.DataFrame)


def test_five38_forecasts_ll(five38_laliga):
    assert isinstance(five38_laliga.read_forecasts(), pd.DataFrame)


def test_five38_clinches_ll(five38_laliga):
    assert isinstance(five38_laliga.read_clinches(), pd.DataFrame)


def test_five38_laliga(five38_laliga):
    df = five38_laliga.read_leagues()
    assert len(df) == 1
    assert df.loc['ESP-La Liga', 'long_name'] == 'La Liga'


def test_league_counts(five38):
    assert len(five38._selected_leagues) == len(five38.read_leagues())
    assert len(five38._selected_leagues) == len(
        five38.read_games().reset_index()['league'].unique()
    )
    assert len(five38._selected_leagues) == len(
        five38.read_forecasts().reset_index()['league'].unique()
    )


def test_league_matches_games(five38):
    assert set(five38.read_games().reset_index().league) == set(
        five38.read_leagues().reset_index().league
    )


def test_league_matches_forecasts(five38):
    assert set(five38.read_forecasts().reset_index().league) == set(
        five38.read_leagues().reset_index().league
    )


def test_league_matches_clinches(five38):
    assert set(five38.read_clinches().reset_index().league) == set(
        five38.read_leagues().reset_index().league
    )


# Bad inits


def test_five38_league_value_error():
    with pytest.raises(ValueError):
        foo.FiveThirtyEight('xxx')


def test_five38_league_type_error():
    with pytest.raises(TypeError):
        foo.FiveThirtyEight(1)  # type: ignore
