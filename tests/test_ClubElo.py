"""Unittests for class soccerdata.ClubElo."""

import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from soccerdata import ClubElo


class TestReadByDate:
    """Tests for ClubElo.read_by_date"""

    def _check_dataframe(self, df: pd.DataFrame) -> None:
        """Check if the dataframe has the expected structure."""
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert set(df.columns) == {"country", "league", "level", "elo", "rank", "from", "to"}
        assert pd.api.types.is_numeric_dtype(df["elo"])
        assert pd.api.types.is_numeric_dtype(df["rank"])
        assert pd.api.types.is_datetime64_any_dtype(df["from"])
        assert pd.api.types.is_datetime64_any_dtype(df["to"])

    def test_default(self, elo: ClubElo) -> None:
        """It should return a dataframe with the latest ELO ratings if no date is given."""
        df = elo.read_by_date()
        self._check_dataframe(df)

    def test_string_date(self, elo: ClubElo) -> None:
        """It should accept a date string in 'YYYY-MM-DD' format."""
        df = elo.read_by_date("2017-04-01")
        self._check_dataframe(df)

        with pytest.raises(ValueError, match="time data '2017' does not match format '%Y-%m-%d'"):
            _ = elo.read_by_date("2017")

    def test_datetime_date(self, elo: ClubElo) -> None:
        """It should accept a datetime object."""
        df = elo.read_by_date(datetime(2017, 4, 1, tzinfo=timezone.utc))
        self._check_dataframe(df)

    def test_raises_on_bad_params(self, elo: ClubElo) -> None:
        """It should raise an error if the parameters are invalid."""
        with pytest.raises(
            TypeError, match="'date' must be a datetime object or string like 'YYYY-MM-DD'"
        ):
            elo.read_by_date(1 / 4)  # type: ignore


class TestReadTeamHistory:
    """Tests for ClubElo.read_team_history"""

    def _check_dataframe(self, df: pd.DataFrame) -> None:
        """Check if the dataframe has the expected structure."""
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert set(df.columns) == {"team", "country", "level", "elo", "rank", "to"}
        assert pd.api.types.is_numeric_dtype(df["elo"])
        assert pd.api.types.is_numeric_dtype(df["rank"])
        assert pd.api.types.is_datetime64_any_dtype(df["to"])

    def test_with_valid_team(self, elo: ClubElo) -> None:
        """It should return a dataframe with the ELO history for the specified club."""
        df = elo.read_team_history("Feyenoord")
        self._check_dataframe(df)

    def test_with_teamname_replacements(self, elo: ClubElo) -> None:
        """It should use the replacement names from teamname_replacements.json."""
        # ClubElo uses "Man City" as the team name
        df_original = elo.read_team_history("Man City")
        df_replacement = elo.read_team_history("Manchester City")
        assert df_original.equals(df_replacement)

    def test_raises_when_team_not_found(self, elo: ClubElo) -> None:
        """It should raise an error if the team is not found."""
        with pytest.raises(ValueError, match="No data found for team FC Knudde"):
            _ = elo.read_team_history("FC Knudde")

    def test_handles_special_characters_in_team_names(self, elo: ClubElo) -> None:
        """It should be able to deal with special characters in team names."""
        df = elo.read_team_history("Brighton & Hove Albion")
        self._check_dataframe(df)
        with pytest.raises(ValueError, match="No data found for team Team & City"):
            _ = elo.read_team_history("Team & City")

    @pytest.mark.fails_gha
    def test_respects_max_age_and_updates_cache(self, elo: ClubElo) -> None:
        """It should not use cached data if it is older than max_age."""
        max_age = timedelta(milliseconds=1)
        assert isinstance(elo.read_team_history("Feyenoord", max_age), pd.DataFrame)
        update_time = (
            (Path(__file__).parent / "appdata" / "data" / "ClubElo" / "Feyenoord.csv")
            .stat()
            .st_mtime
        )
        current_time = time.time()
        # Ensure the cache file is recently updated (within a small tolerance)
        assert current_time - update_time < 5

    def test_raises_on_bad_params(self, elo: ClubElo) -> None:
        """It should raise an error if the parameters are invalid."""
        with pytest.raises(TypeError, match="'max_age' must be of type int or datetime.timedelta"):
            _ = elo.read_team_history("Feyenoord", max_age=datetime.now(tz=timezone.utc))  # type: ignore
