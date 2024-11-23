"""Scraper for http://fotmob.com."""

import itertools
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Callable, Optional, Union

import pandas as pd
import requests

from ._common import BaseRequestsReader, add_standardized_team_name, make_game_id
from ._config import DATA_DIR, NOCACHE, NOSTORE, TEAMNAME_REPLACEMENTS, logger

FOTMOB_DATADIR = DATA_DIR / "FotMob"
FOTMOB_API = "https://www.fotmob.com/api/"


class FotMob(BaseRequestsReader):
    """Provides pd.DataFrames from data available at http://www.fotmob.com.

    Data will be downloaded as necessary and cached locally in
    ``~/soccerdata/data/FotMob``.

    Parameters
    ----------
    leagues : string or iterable, optional
        IDs of Leagues to include.
    seasons : string, int or list, optional
        Seasons to include. Supports multiple formats.
        Examples: '16-17'; 2016; '2016-17'; [14, 15, 16]
    proxy : 'tor' or dict or list(dict) or callable, optional
        Use a proxy to hide your IP address. Valid options are:
            - 'tor': Uses the Tor network. Tor should be running in
              the background on port 9050.
            - dict: A dictionary with the proxy to use. The dict should be
              a mapping of supported protocols to proxy addresses. For example::

                  {
                      'http': 'http://10.10.1.10:3128',
                      'https': 'http://10.10.1.10:1080',
                  }

            - list(dict): A list of proxies to choose from. A different proxy will
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
        leagues: Optional[Union[str, list[str]]] = None,
        seasons: Optional[Union[str, int, Iterable[Union[str, int]]]] = None,
        proxy: Optional[
            Union[str, dict[str, str], list[dict[str, str]], Callable[[], dict[str, str]]]
        ] = None,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = FOTMOB_DATADIR,
    ):
        """Initialize the FotMob reader."""
        super().__init__(
            leagues=leagues,
            proxy=proxy,
            no_cache=no_cache,
            no_store=no_store,
            data_dir=data_dir,
        )
        self.seasons = seasons  # type: ignore
        if not self.no_store:
            (self.data_dir / "leagues").mkdir(parents=True, exist_ok=True)
            (self.data_dir / "seasons").mkdir(parents=True, exist_ok=True)
            (self.data_dir / "matches").mkdir(parents=True, exist_ok=True)

    def _init_session(self) -> requests.Session:
        session = super()._init_session()
        try:
            r = requests.get("http://46.101.91.154:6006/")
            r.raise_for_status()
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Unable to connect to the session cookie server.")
        result = r.json()
        session.headers.update(result)
        return session

    @property
    def leagues(self) -> list[str]:
        """Return a list of selected leagues."""
        return list(self._leagues_dict.keys())

    def read_leagues(self) -> pd.DataFrame:
        """Retrieve the selected leagues from the datasource.

        Returns
        -------
        pd.DataFrame
        """
        url = FOTMOB_API + "allLeagues"
        filepath = self.data_dir / "allLeagues.json"
        reader = self.get(url, filepath)
        data = json.load(reader)
        leagues = []
        for k, v in data.items():
            if k == "international":
                for int_league in v[0]["leagues"]:
                    leagues.append(
                        {
                            "region": v[0]["ccode"],
                            "league_id": int_league["id"],
                            "league": int_league["name"],
                            "url": "https://fotmob.com" + int_league["pageUrl"],
                        }
                    )
            elif k not in ("favourite", "popular", "userSettings"):
                for country in v:
                    for dom_league in country["leagues"]:
                        leagues.append(
                            {
                                "region": country["ccode"],
                                "league": dom_league["name"],
                                "league_id": dom_league["id"],
                                "url": "https://fotmob.com" + dom_league["pageUrl"],
                            }
                        )
        df = (
            pd.DataFrame(leagues)
            .assign(league=lambda x: x.region + "-" + x.league)
            .pipe(self._translate_league)
            .set_index("league")
            .loc[self._selected_leagues.keys()]
            .sort_index()
        )
        return df[df.index.isin(self.leagues)]

    def read_seasons(self) -> pd.DataFrame:
        """Retrieve the selected seasons for the selected leagues.

        Returns
        -------
        pd.DataFrame
        """
        filemask = "leagues/{}.json"
        urlmask = FOTMOB_API + "leagues?id={}"
        df_leagues = self.read_leagues()
        seasons = []
        for lkey, league in df_leagues.iterrows():
            url = urlmask.format(league.league_id)
            filepath = self.data_dir / filemask.format(lkey)
            reader = self.get(url, filepath)
            data = json.load(reader)
            # extract season IDs
            avail_seasons = data["allAvailableSeasons"]
            for season in avail_seasons:
                seasons.append(
                    {
                        "league": lkey,
                        "season": self._season_code.parse(season),
                        "league_id": league.league_id,
                        "season_id": season,
                        "url": league.url + "?season=" + season,
                    }
                )
            # Change season id for 2122 season manually (gross)
        df = pd.DataFrame(seasons).set_index(["league", "season"]).sort_index()
        return df.loc[df.index.isin(list(itertools.product(self.leagues, self.seasons)))]

    def read_league_table(self, force_cache: bool = False) -> pd.DataFrame:  # noqa: C901
        """Retrieve the league table for the selected leagues.

        Parameters
        ----------
        force_cache : bool
             By default no cached data is used for the current season.
             If True, will force the use of cached data anyway.

        Returns
        -------
        pd.DataFrame
        """
        filemask = "seasons/{}_{}.html"
        urlmask = FOTMOB_API + "leagues?id={}&season={}"

        idx = ["league", "season"]
        cols = ["team", "MP", "W", "D", "L", "GF", "GA", "GD", "Pts"]

        # get league and season IDs
        seasons = self.read_seasons()
        # collect league tables
        mult_tables = []
        for (lkey, skey), season in seasons.iterrows():
            # read html page (league overview)
            filepath = self.data_dir / filemask.format(lkey, skey)
            url = urlmask.format(season.league_id, season.season_id)
            current_season = not self._is_complete(lkey, skey)
            reader = self.get(url, filepath, no_cache=current_season and not force_cache)
            season_data = json.load(reader)
            table_data = season_data["table"][0]["data"]
            if "tables" in table_data:
                if "stage" not in idx:
                    idx.append("stage")
                groups_data = table_data["tables"]
                all_groups = []
                for i in range(len(groups_data)):
                    group_table = pd.json_normalize(groups_data[i]["table"]["all"])
                    group_table["stage"] = groups_data[i]["leagueName"]
                    all_groups.append(group_table)
                df_table = pd.concat(all_groups, axis=0)
            else:
                df_table = pd.json_normalize(table_data["table"]["all"])
            df_table[["GF", "GA"]] = df_table["scoresStr"].str.split("-", expand=True)
            df_table = df_table.rename(
                columns={
                    "name": "team",
                    "played": "MP",
                    "wins": "W",
                    "draws": "D",
                    "losses": "L",
                    "goalConDiff": "GD",
                    "pts": "Pts",
                }
            )
            df_table["league"] = lkey
            df_table["season"] = skey

            # If league has a playoff, add final playoff standing as a column
            if "playoff" in season_data["tabs"]:
                if "playoff" not in cols:
                    cols.append("playoff")
                df_table["playoff"] = None
                # Get cup game finalists (for leagues with playoffs)
                playoff_rounds = season_data["playoff"]["rounds"]
                for i in range(len(playoff_rounds)):
                    stage_teams = []
                    for game in playoff_rounds[i]["matchups"]:
                        if not bool(game):
                            continue
                        stage = game["stage"]
                        stage_teams.append(game["homeTeamId"])
                        stage_teams.append(game["awayTeamId"])
                        df_table.loc[df_table["id"].isin(stage_teams), "playoff"] = stage
                        if stage == "final":
                            winner = game["winner"]
                            df_table.loc[df_table["id"] == winner, "playoff"] = "cup_winner"
            mult_tables.append(df_table)
        return (
            pd.concat(mult_tables, axis=0)
            .rename(columns={"Squad": "team"})
            .replace({"team": TEAMNAME_REPLACEMENTS})
            .set_index(idx)
            .sort_index()[cols]
        )

    def read_schedule(self, force_cache: bool = False) -> pd.DataFrame:
        """Retrieve the game schedule for the selected leagues and seasons.

        Parameters
        ----------
        force_cache : bool
             By default no cached data is used for the current season.
             If True, will force the use of cached data anyway.

        Returns
        -------
        pd.DataFrame
        """
        filemask = "seasons/{}_{}.html"
        urlmask = FOTMOB_API + "leagues?id={}&season={}"

        cols = [
            "round",
            "week",
            "date",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "status",
            "game_id",
            "url",
        ]

        df_seasons = self.read_seasons()
        all_schedules = []
        for (lkey, skey), season in df_seasons.iterrows():
            filepath = self.data_dir / filemask.format(lkey, skey)
            url = urlmask.format(season.league_id, season.season_id)
            current_season = not self._is_complete(lkey, skey)
            reader = self.get(url, filepath, no_cache=current_season and not force_cache)
            season_data = json.load(reader)

            df = pd.json_normalize(season_data["matches"]["allMatches"])
            df["league"] = lkey
            df["season"] = skey
            all_schedules.append(df)

        # Construct the output dataframe
        df = (
            pd.concat(all_schedules)
            .rename(
                columns={
                    "roundName": "round",
                    "round": "week",
                    "home.name": "home_team",
                    "away.name": "away_team",
                    "status.reason.short": "status",
                    "pageUrl": "url",
                    "id": "game_id",
                }
            )
            .replace(
                {
                    "home_team": TEAMNAME_REPLACEMENTS,
                    "away_team": TEAMNAME_REPLACEMENTS,
                }
            )
            .assign(date=lambda x: pd.to_datetime(x["status.utcTime"], format="mixed"))
        )
        df["game"] = df.apply(make_game_id, axis=1)
        df["url"] = "https://fotmob.com" + df["url"]
        df[["home_score", "away_score"]] = df["status.scoreStr"].str.split("-", expand=True)
        return df.set_index(["league", "season", "game"]).sort_index()[cols]

    def read_team_match_stats(
        self,
        stat_type: str = "Top stats",
        opponent_stats: bool = True,
        team: Optional[Union[str, list[str]]] = None,
        force_cache: bool = False,
    ) -> pd.DataFrame:
        """Retrieve the match stats for the selected leagues and seasons.

        The following stat types are available:
            * 'Top stats'
            * 'Shots'
            * 'Expected goals (xG)'
            * 'Passes'
            * 'Defence'
            * 'Duels'
            * 'Discipline'

        Parameters
        ----------
        stat_type : str
            Type of stats to retrieve.
        opponent_stats: bool
            If True, will retrieve opponent stats.
        team: str or list of str, optional
            Team(s) to retrieve. If None, will retrieve all teams.
        force_cache : bool
            By default no cached data is used to scrape the list of available
            games for the current season. If True, will force the use of
            cached data anyway.

        Raises
        ------
        TypeError
            If ``stat_type`` is not valid.
        ValueError
            If no games with the given IDs were found for the selected seasons and leagues.

        Returns
        -------
        pd.DataFrame
        """
        filemask = "matches/{}_{}_{}.html"
        urlmask = FOTMOB_API + "matchDetails?matchId={}"

        # Retrieve games for which a match report is available
        df_matches = self.read_schedule(force_cache)
        df_complete = df_matches.loc[df_matches["status"].isin(["FT", "AET", "Pen"])]

        if team is not None:
            # get alternative names of the specified team(s)
            teams_to_check = add_standardized_team_name(team)

            # select requested teams
            iterator = df_complete.loc[
                (
                    df_complete.home_team.isin(teams_to_check)
                    | df_complete.away_team.isin(teams_to_check)
                )
            ]
            if len(iterator) == 0:
                raise ValueError("No data found for the given teams in the selected seasons.")
        else:
            iterator = df_complete
            teams_to_check = iterator.home_team.tolist() + iterator.away_team.tolist()

        stats = []
        for i, game in iterator.reset_index().iterrows():
            lkey, skey, gkey = game["league"], game["season"], game["game"]
            # Get data for specific game
            url = urlmask.format(game.game_id)
            filepath = self.data_dir / filemask.format(lkey, skey, game.game_id)
            reader = self.get(url, filepath)
            logger.info(
                "[%s/%s] Retrieving game with id=%s",
                i + 1,
                len(iterator),
                game["game_id"],
            )
            game_data = json.load(reader)

            # Get stats types
            all_stats = game_data["content"]["stats"]["Periods"]["All"]["stats"]
            try:
                selected_stats = next(stat for stat in all_stats if stat["title"] == stat_type)
            except StopIteration:
                raise ValueError(f"Invalid stat type: {stat_type}")

            df_raw_stats = pd.DataFrame(selected_stats["stats"])
            game_teams = [game.home_team, game.away_team]
            for i, team in enumerate(game_teams):
                df_team_stats = df_raw_stats.copy()
                df_team_stats["stat"] = df_team_stats["stats"].apply(lambda x: x[i])  # noqa: B023
                df_team_stats["league"] = lkey
                df_team_stats["season"] = skey
                df_team_stats["game"] = gkey
                df_team_stats["team"] = team
                if not opponent_stats:
                    df_team_stats = df_team_stats[df_team_stats.team.isin(teams_to_check)]
                df_team_stats.set_index(["league", "season", "game", "team"], inplace=True)
                df_team_stats = df_team_stats[df_team_stats["type"] != "title"]
                df_team_stats = df_team_stats.pivot(columns="title", values="stat").reset_index()
                df_team_stats.columns.name = None
                stats.append(df_team_stats)

        df = pd.concat(stats, axis=0)
        df = df.set_index(["league", "season", "game", "team"]).sort_index()
        # Split percentage values
        pct_cols = [col for col in df.columns if df[col].astype(str).str.contains("%").any()]
        for col in pct_cols:
            df[[col, col + " (%)"]] = df[col].str.split(expand=True)
            df[col + " (%)"] = df[col + " (%)"].str.extract(r"(\d+)").astype(float).div(100)
        return df
