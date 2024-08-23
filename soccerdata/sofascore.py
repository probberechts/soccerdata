"""Scraper for https://www.sofascore.com/."""

import itertools
import json
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Union

import pandas as pd

from ._common import BaseRequestsReader, make_game_id
from ._config import DATA_DIR, NOCACHE, NOSTORE, TEAMNAME_REPLACEMENTS

SOFASCORE_DATADIR = DATA_DIR / "Sofascore"
SOFASCORE_API = "https://api.sofascore.com/api/v1/"


class Sofascore(BaseRequestsReader):
    """Provides pd.DataFrames from data available at http://www.sofascore.com.

    Data will be downloaded as necessary and cached locally in
    ``~/soccerdata/data/Sofascore``.

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
        data_dir: Path = SOFASCORE_DATADIR,
    ):
        """Initialize the Sofascore reader."""
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

    def read_leagues(self) -> pd.DataFrame:
        """Retrieve the selected leagues from the datasource.

        Returns
        -------
        pd.DataFrame
        """
        url = SOFASCORE_API + "config/unique-tournaments/EN/football"
        filepath = self.data_dir / "leagues.json"
        reader = self.get(url, filepath)
        data = json.load(reader)
        leagues = []
        for k in data["uniqueTournaments"]:
            leagues.append(
                {
                    "league_id": k["id"],
                    "league": k["name"],
                }
            )
        df = (
            pd.DataFrame(leagues)
            .pipe(self._translate_league)
            .assign(region=lambda x: x["league"].str.split("-").str[0])
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
        seasons = []
        df_leagues = self.read_leagues()
        for lkey, league in df_leagues.iterrows():
            url = SOFASCORE_API + "unique-tournament/{}/seasons"
            filepath = self.data_dir / filemask.format(lkey)
            reader = self.get(url.format(league.league_id), filepath)
            data = json.load(reader)["seasons"]
            for season in data:
                seasons.append(
                    {
                        "league": lkey,
                        "season": self._season_code.parse(season["year"]),
                        "league_id": league.league_id,
                        "season_id": season["id"],
                    }
                )
        df = pd.DataFrame(seasons).set_index(["league", "season"]).sort_index()

        return df.loc[df.index.isin(list(itertools.product(self.leagues, self.seasons)))]

    def read_league_table(self, force_cache: bool = False) -> pd.DataFrame:
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
        urlmask = SOFASCORE_API + "unique-tournament/{}/season/{}/standings/total"

        idx = ["league", "season"]
        cols = ["team", "MP", "W", "D", "L", "GF", "GA", "GD", "Pts"]

        seasons = self.read_seasons()
        # collect league tables
        mult_tables = []
        for (lkey, skey), season in seasons.iterrows():
            filepath = self.data_dir / filemask.format(lkey, skey)
            url = urlmask.format(season.league_id, season.season_id)
            current_season = not self._is_complete(lkey, skey)
            reader = self.get(url, filepath, no_cache=current_season and not force_cache)
            season_data = json.load(reader)
            for row in season_data["standings"][0]["rows"]:
                mult_tables.append(
                    {
                        "league": lkey,
                        "season": skey,
                        "team": row["team"]["name"],
                        "MP": row["matches"],
                        "W": row["wins"],
                        "D": row["draws"],
                        "L": row["losses"],
                        "GF": row["scoresFor"],
                        "GA": row["scoresAgainst"],
                        "GD": row["scoresFor"] - row["scoresAgainst"],
                        "Pts": row["points"],
                    }
                )
            df = (
                pd.DataFrame(mult_tables)
                .set_index(idx)
                .replace({"team": TEAMNAME_REPLACEMENTS})
                .sort_index()[cols]
            )
        return df

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
        urlmask1 = SOFASCORE_API + "unique-tournament/{}/season/{}/rounds"
        urlmask2 = SOFASCORE_API + "unique-tournament/{}/season/{}/events/round/{}"
        filemask1 = "matches/rounds_{}_{}.json"
        filemask2 = "matches/round_matches_{}_{}_{}.json"

        cols = [
            "round",
            "week",
            "date",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "game_id",
        ]

        df_seasons = self.read_seasons()
        all_schedules = []
        for (lkey, skey), season in df_seasons.iterrows():
            filepath1 = self.data_dir / filemask1.format(lkey, skey)
            url1 = urlmask1.format(season["league_id"], season["season_id"])
            current_season = not self._is_complete(lkey, skey)
            reader1 = self.get(url1, filepath1, no_cache=current_season and not force_cache)
            season_data = json.load(reader1)
            rounds = season_data["rounds"]

            for round in rounds:  # noqa: A001
                filepath2 = self.data_dir / filemask2.format(lkey, skey, round["round"])
                url2 = urlmask2.format(season["league_id"], season["season_id"], round["round"])
                reader2 = self.get(url2, filepath2, no_cache=current_season and not force_cache)
                match_data = json.load(reader2)
                for _match in match_data["events"]:
                    if _match["status"]["code"] == 100 or _match["status"]["code"] == 0:
                        if _match["status"]["code"] == 100:
                            home_score = int(_match["homeScore"]["current"])
                            away_score = int(_match["awayScore"]["current"])
                        else:
                            home_score = float("nan")  # type: ignore
                            away_score = float("nan")  # type: ignore

                        all_schedules.append(
                            {
                                "league": lkey,
                                "season": skey,
                                "round": round["round"],
                                "week": _match["roundInfo"]["round"],
                                "date": datetime.fromtimestamp(
                                    _match["startTimestamp"], tz=timezone.utc
                                ),
                                "home_team": _match["homeTeam"]["name"],
                                "away_team": _match["awayTeam"]["name"],
                                "home_score": home_score,
                                "away_score": away_score,
                                "game_id": _match["id"],
                            }
                        )

        df = pd.DataFrame(all_schedules).replace(
            {
                "home_team": TEAMNAME_REPLACEMENTS,
                "away_team": TEAMNAME_REPLACEMENTS,
            }
        )
        df["game"] = df.apply(make_game_id, axis=1)
        return df.set_index(["league", "season", "game"]).sort_index()[cols]
