"""Scraper for https://www.football-charts.com."""

import itertools
import json
from collections.abc import Callable, Iterable
from pathlib import Path

import numpy as np
import pandas as pd

from ._common import BaseRequestsReader, make_game_id
from ._config import DATA_DIR, NOCACHE, NOSTORE, TEAMNAME_REPLACEMENTS, logger

FOOTBALLCHARTS_DATADIR = DATA_DIR / "FootballCharts"
FOOTBALLCHARTS_API = "https://footballcharts-backend.onrender.com/api/v1/"
# Concept record of the archived dataset; it always resolves to the latest version.
FOOTBALLCHARTS_ARCHIVE = "https://zenodo.org/api/records/22295583/versions/latest"
FOOTBALLCHARTS_ARCHIVE_FILE = "football_charts_matches.csv"

ARCHIVE_COLUMNS = [
    "league",
    "season",
    "match_date",
    "home_team",
    "away_team",
    "ht_result",
    "ft_result",
    "first_goal_time",
    "all_goal_times",
]


class FootballCharts(BaseRequestsReader):
    """Provides pd.DataFrames from data available at https://www.football-charts.com.

    Football Charts publishes results with half-time scores and goal minutes for
    more than 90 leagues, including many lower divisions. Completed seasons are
    read from its archived dataset on Zenodo (https://doi.org/10.5281/zenodo.22295583,
    CC BY 4.0), which lists the minute of every goal. The current season, and any
    season not yet in the archive, is read from its public API, which needs no
    key (300 requests a day per IP) and gives the minute of the first goal. The
    data is free for personal and research use with attribution to
    football-charts.com.

    Data will be downloaded as necessary and cached locally in
    ``~/soccerdata/data/FootballCharts``.

    Parameters
    ----------
    leagues : string or iterable, optional
        IDs of Leagues to include.
    seasons : string, int or list, optional
        Seasons to include. Supports multiple formats.
        Examples: '16-17'; 2016; '2016-17'; [14, 15, 16]
    proxy : 'tor' or or dict or list(dict) or callable, optional
        Use a proxy to hide your IP address. Valid options are:
            - "tor": Uses the Tor network. Tor should be running in
              the background on port 9050.
            - str: The address of the proxy server to use.
            - list(str): A list of proxies to choose from. A different proxy will
              be selected from this list after failed requests, allowing rotating
              proxies.
            - callable: A function that returns a valid proxy. This function will
              be called after failed requests, allowing rotating proxies.
    no_cache : bool
        If True, will not use cached data.
    no_store : bool
        If True, will not store downloaded data.
    data_dir : Path
        Path to directory where data will be cached.
    """

    def __init__(
        self,
        leagues: str | list[str] | None = None,
        seasons: str | int | Iterable[str | int] | None = None,
        proxy: str | list[str] | Callable[[], str] | None = None,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = FOOTBALLCHARTS_DATADIR,
    ):
        """Initialize the FootballCharts reader."""
        super().__init__(
            leagues=leagues,
            proxy=proxy,
            no_cache=no_cache,
            no_store=no_store,
            data_dir=data_dir,
        )
        self.seasons = seasons
        self._archive: pd.DataFrame | None = None
        if not self.no_store:
            (self.data_dir / "matches").mkdir(parents=True, exist_ok=True)

    def _read_league_index(self) -> dict:
        """Return the API's list of leagues and the seasons it serves."""
        url = FOOTBALLCHARTS_API + "leagues/"
        filepath = self.data_dir / "leagues.json"
        reader = self.get(url, filepath, max_age=1)
        return json.load(reader)

    def _read_archive(self) -> pd.DataFrame:
        """Return the archived dataset with all completed seasons."""
        if self._archive is None:
            try:
                reader = self.get(
                    FOOTBALLCHARTS_ARCHIVE, self.data_dir / "archive.json", max_age=30
                )
                record = json.load(reader)
                file = next(f for f in record["files"] if f["key"] == FOOTBALLCHARTS_ARCHIVE_FILE)
                filepath = self.data_dir / f"archive_{record['id']}.csv"
                reader = self.get(file["links"]["self"], filepath)
                self._archive = pd.read_csv(reader, dtype=str, keep_default_na=False)[
                    ARCHIVE_COLUMNS
                ]
            except (ConnectionError, KeyError, StopIteration):
                logger.warning(
                    "Could not load the Football Charts archive. "
                    "Only the seasons served by the API are available."
                )
                self._archive = pd.DataFrame(columns=ARCHIVE_COLUMNS, dtype=str)
        return self._archive

    def read_leagues(self) -> pd.DataFrame:
        """Retrieve the selected leagues from the datasource.

        Returns
        -------
        pd.DataFrame
        """
        data = self._read_league_index()
        df = (
            pd.DataFrame(
                [
                    {
                        "league": league["league"],
                        "league_id": league["league"],
                        "country": league["country"],
                        "url": league["url"],
                    }
                    for league in data["leagues"]
                ]
            )
            .pipe(self._translate_league)
            .dropna(subset=["league"])
            .set_index("league")
            .sort_index()
        )
        return df[df.index.isin(self.leagues)]

    def read_seasons(self) -> pd.DataFrame:
        """Retrieve the selected seasons for the selected leagues.

        The ``source`` column tells where the games of each season are read
        from: the archive (completed seasons) or the API (current season).

        Returns
        -------
        pd.DataFrame
        """
        df_leagues = self.read_leagues()
        api_seasons = {
            league["league"]: set(league["seasons"])
            for league in self._read_league_index()["leagues"]
        }
        archive = self._read_archive()
        archived = archive.groupby("league")["season"].unique().to_dict()

        seasons = []
        for lkey, league in df_leagues.iterrows():
            in_archive = set(archived.get(league.league_id, []))
            for season_id in sorted(in_archive | api_seasons.get(league.league_id, set())):
                seasons.append(
                    {
                        "league": lkey,
                        "season": self._season_code.parse(season_id),
                        "league_id": league.league_id,
                        "season_id": season_id,
                        "source": "archive" if season_id in in_archive else "api",
                    }
                )
        df = (
            pd.DataFrame(seasons, columns=["league", "season", "league_id", "season_id", "source"])
            .set_index(["league", "season"])
            .sort_index()
        )
        return df.loc[df.index.isin(list(itertools.product(self.leagues, self.seasons)))]

    def _read_archive_games(self, league_id: str, season_id: str) -> pd.DataFrame:
        """Return the games of a season in the archive."""
        archive = self._read_archive()
        games = archive[(archive["league"] == league_id) & (archive["season"] == season_id)]
        return pd.DataFrame(
            {
                "date": games["match_date"],
                "home_team": games["home_team"],
                "away_team": games["away_team"],
                "score": games["ft_result"],
                "ht_score": games["ht_result"],
                "first_goal": games["first_goal_time"],
                "goals": games["all_goal_times"],
            }
        )

    def _read_api_games(self, league_id: str, season_id: str, no_cache: bool) -> pd.DataFrame:
        """Return the games of a season from the API, including upcoming fixtures."""
        url = FOOTBALLCHARTS_API + f"leagues/{league_id}/results/?season={season_id}"
        filepath = self.data_dir / "matches" / f"results_{league_id}_{season_id}.json"
        data = json.load(self.get(url, filepath, no_cache=no_cache))
        games = [
            {
                "date": game["date"],
                "home_team": game["homeTeam"],
                "away_team": game["awayTeam"],
                "score": game["score"] or "",
                "ht_score": game["ht_result"] or "",
                "first_goal": _first_goal(game),
                "goals": None,
            }
            for game in data["matches"]
        ]
        if data.get("current_season") == season_id:
            url = FOOTBALLCHARTS_API + f"leagues/{league_id}/fixtures/"
            filepath = self.data_dir / "matches" / f"fixtures_{league_id}.json"
            fixtures = json.load(self.get(url, filepath, no_cache=no_cache))
            played = {(g["date"], g["home_team"], g["away_team"]) for g in games}
            games += [
                {
                    "date": game["match_date"],
                    "home_team": game["home_team"],
                    "away_team": game["away_team"],
                    "score": "",
                    "ht_score": "",
                    "first_goal": "",
                    "goals": None,
                }
                for game in fixtures["matches"]
                if (game["match_date"], game["home_team"], game["away_team"]) not in played
            ]
        return pd.DataFrame(
            games,
            columns=[
                "date",
                "home_team",
                "away_team",
                "score",
                "ht_score",
                "first_goal",
                "goals",
            ],
        )

    def read_schedule(self, force_cache: bool = False) -> pd.DataFrame:
        """Retrieve the game schedule for the selected leagues and seasons.

        Goal minutes include stoppage time, so a goal in the fourth minute of
        second-half stoppage time is recorded as 94.
        ``first_goal_minute`` is available for every season; ``goal_minutes``,
        the minute of every goal, is available for the seasons in the archive.

        Parameters
        ----------
        force_cache : bool
             By default no cached data is used for the current season.
             If True, will force the use of cached data anyway.

        Returns
        -------
        pd.DataFrame
        """
        cols = [
            "date",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "ht_home_score",
            "ht_away_score",
            "first_goal_minute",
            "goal_minutes",
        ]

        df_seasons = self.read_seasons()
        all_schedules = []
        for (lkey, skey), season in df_seasons.iterrows():
            if season["source"] == "archive":
                games = self._read_archive_games(season["league_id"], season["season_id"])
            else:
                current_season = not self._is_complete(lkey, skey)
                games = self._read_api_games(
                    season["league_id"],
                    season["season_id"],
                    no_cache=current_season and not force_cache,
                )
            all_schedules.append(games.assign(league=lkey, season=skey))

        if len(all_schedules) == 0:
            return pd.DataFrame(
                columns=["league", "season", "game", *cols],
            ).set_index(["league", "season", "game"])

        df = pd.concat(all_schedules, ignore_index=True)
        df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
        df["home_score"], df["away_score"] = _split_score(df["score"])
        df["ht_home_score"], df["ht_away_score"] = _split_score(df["ht_score"])
        df["first_goal_minute"] = pd.array(
            [_minute(m) if m else pd.NA for m in df["first_goal"]], dtype="Int64"
        )
        df["goal_minutes"] = [
            _goal_minutes(goals, home + away)
            for goals, home, away in zip(df["goals"], df["home_score"], df["away_score"])
        ]
        df = df.replace(
            {
                "home_team": TEAMNAME_REPLACEMENTS,
                "away_team": TEAMNAME_REPLACEMENTS,
            }
        )
        df["game"] = df.apply(make_game_id, axis=1)
        return df.set_index(["league", "season", "game"]).sort_index()[cols]

    def read_league_table(self, force_cache: bool = False) -> pd.DataFrame:
        """Retrieve the league table for the selected leagues.

        The table is computed from the results, with three points for a win
        and one for a draw, and ordered by points, goal difference and goals
        scored. Point deductions are not applied.

        Parameters
        ----------
        force_cache : bool
             By default no cached data is used for the current season.
             If True, will force the use of cached data anyway.

        Returns
        -------
        pd.DataFrame
        """
        idx = ["league", "season"]
        cols = ["team", "MP", "W", "D", "L", "GF", "GA", "GD", "Pts"]

        schedule = self.read_schedule(force_cache=force_cache).reset_index()
        played = schedule.dropna(subset=["home_score", "away_score"])
        sides = []
        for team, scored, conceded in [
            ("home_team", "home_score", "away_score"),
            ("away_team", "away_score", "home_score"),
        ]:
            sides.append(
                pd.DataFrame(
                    {
                        "league": played["league"],
                        "season": played["season"],
                        "team": played[team],
                        "GF": played[scored].astype(int),
                        "GA": played[conceded].astype(int),
                    }
                )
            )
        results = pd.concat(sides, ignore_index=True)
        results["W"] = (results["GF"] > results["GA"]).astype(int)
        results["D"] = (results["GF"] == results["GA"]).astype(int)
        results["L"] = (results["GF"] < results["GA"]).astype(int)

        df = (
            results.groupby([*idx, "team"])
            .agg(
                MP=("GF", "size"),
                W=("W", "sum"),
                D=("D", "sum"),
                L=("L", "sum"),
                GF=("GF", "sum"),
                GA=("GA", "sum"),
            )
            .reset_index()
        )
        df["GD"] = df["GF"] - df["GA"]
        df["Pts"] = 3 * df["W"] + df["D"]
        df = df.sort_values(
            [*idx, "Pts", "GD", "GF", "team"],
            ascending=[True, True, False, False, False, True],
        )
        return df.set_index(idx)[cols]


def _split_score(score: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Split a score such as '2:1' into home and away goals."""
    goals = score.fillna("").str.extract(r"^\s*(\d+)\s*:\s*(\d+)\s*$")
    return (
        pd.to_numeric(goals[0]).astype("Int64"),
        pd.to_numeric(goals[1]).astype("Int64"),
    )


def _minute(minute: str) -> int:
    """Convert a goal minute such as '45+2' to minutes played."""
    base, _, extra = str(minute).strip().partition("+")
    return int(base) + int(extra or 0)


def _first_goal(game: dict) -> str:
    """Return the first-goal minute of a game from the API as a string."""
    if game.get("first_goal_time") is None:
        return ""
    return f"{game['first_goal_time']}+{game.get('first_goal_time_extra') or 0}"


def _goal_minutes(goals: str | None, total: int) -> list[int] | float:
    """Return the minute of every goal, or NaN when it is not known."""
    if goals:
        return [_minute(m) for m in goals.split(",")]
    if total is not pd.NA and total == 0:
        return []
    return np.nan
