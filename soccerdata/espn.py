"""Scraper for http://site.api.espn.com/apis/site/v2/sports/soccer."""

import itertools
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Union

import pandas as pd

from ._common import BaseRequestsReader, make_game_id, standardize_colnames
from ._config import DATA_DIR, NOCACHE, NOSTORE, TEAMNAME_REPLACEMENTS, logger

# http://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/summary?event=513466
# http://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?dates=20180901
# http://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/news
# http://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/teams

ESPN_DATADIR = DATA_DIR / "ESPN"
ESPN_API = "http://site.api.espn.com/apis/site/v2/sports/soccer"


class ESPN(BaseRequestsReader):
    """Provides pd.DataFrames from JSON api available at http://site.api.espn.com.

    Data will be downloaded as necessary and cached locally in
    ``~/soccerdata/data/ESPN``.

    Parameters
    ----------
    leagues : string or iterable, optional
        IDs of leagues to include.
    seasons : string, int or list, optional
        Seasons to include. Supports multiple formats.
        Examples: '16-17'; 2016; '2016-17'; [14, 15, 16]
    proxy : 'tor' or dict or list(dict) or callable, optional
        Use a proxy to hide your IP address. Valid options are:
            - "tor": Uses the Tor network. Tor should be running in
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
        seasons: Optional[Union[str, int, list]] = None,
        proxy: Optional[
            Union[str, dict[str, str], list[dict[str, str]], Callable[[], dict[str, str]]]
        ] = None,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = ESPN_DATADIR,
    ):
        """Initialize a new ESPN reader."""
        super().__init__(
            leagues=leagues,
            proxy=proxy,
            no_cache=no_cache,
            no_store=no_store,
            data_dir=data_dir,
        )
        self.seasons = seasons  # type: ignore

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
        urlmask = ESPN_API + "/{}/scoreboard?dates={}"
        filemask = "Schedule_{}_{}.json"

        df_list = []
        # Get match days
        for lkey, skey in itertools.product(self._selected_leagues.values(), self.seasons):
            if int(skey[:2]) > int(str(datetime.now(tz=timezone.utc).year + 1)[-2:]):
                start_date = "".join(["19", skey[:2], "07", "01"])
            else:
                start_date = "".join(["20", skey[:2], "07", "01"])

            url = urlmask.format(lkey, start_date)
            filepath = self.data_dir / filemask.format(lkey, start_date)
            reader = self.get(url, filepath)
            data = json.load(reader)

            match_dates = [
                datetime.strptime(d, "%Y-%m-%dT%H:%MZ").strftime("%Y%m%d")  # noqa: DTZ007
                for d in data["leagues"][0]["calendar"]
            ]
            for date in match_dates:
                url = urlmask.format(lkey, date)
                filepath = self.data_dir / filemask.format(lkey, date)
                current_season = not self._is_complete(lkey, skey)
                reader = self.get(url, filepath, no_cache=current_season and not force_cache)

                data = json.load(reader)
                df_list.extend(
                    [
                        {
                            "league": lkey,
                            "season": skey,
                            "date": e["date"],
                            "home_team": e["competitions"][0]["competitors"][0]["team"]["name"],
                            "away_team": e["competitions"][0]["competitors"][1]["team"]["name"],
                            "game_id": int(e["id"]),
                            "league_id": lkey,
                        }
                        for e in data["events"]
                    ]
                )
        return (
            pd.DataFrame(df_list)
            .pipe(self._translate_league)
            .replace({"home_team": TEAMNAME_REPLACEMENTS, "away_team": TEAMNAME_REPLACEMENTS})
            .assign(date=lambda x: pd.to_datetime(x["date"]))
            .dropna(subset=["home_team", "away_team", "date"])
            .assign(game=lambda df: df.apply(make_game_id, axis=1))
            .set_index(["league", "season", "game"])
            .sort_index()
        )

    def read_matchsheet(self, match_id: Optional[Union[int, list[int]]] = None) -> pd.DataFrame:
        """Retrieve match sheets for the selected leagues and seasons.

        Parameters
        ----------
        match_id : int or list of int, optional
            Retrieve the match sheet for a specific game.

        Raises
        ------
        ValueError
            If no games with the given IDs were found for the selected seasons and leagues.

        Returns
        -------
        pd.DataFrame.
        """
        urlmask = ESPN_API + "/{}/summary?event={}"
        filemask = "Summary_{}.json"

        df_schedule = self.read_schedule().reset_index()
        if match_id is not None:
            iterator = df_schedule[
                df_schedule.game_id.isin([match_id] if isinstance(match_id, int) else match_id)
            ]
            if len(iterator) == 0:
                raise ValueError(
                    "No games with the given IDs found for the selected seasons and leagues."
                )
        else:
            iterator = df_schedule

        df_list = []
        for i, match in iterator.iterrows():
            url = urlmask.format(match["league_id"], match["game_id"])
            filepath = self.data_dir / filemask.format(match["game_id"])
            reader = self.get(url, filepath)

            data = json.load(reader)
            for i in range(2):
                match_sheet = {
                    "game": match["game"],
                    "league": match["league"],
                    "season": match["season"],
                    "team": data["boxscore"]["form"][i]["team"]["displayName"],
                    "is_home": (i == 0),
                    "venue": (
                        data["gameInfo"]["venue"]["fullName"]
                        if "venue" in data["gameInfo"]
                        else None
                    ),
                    "attendance": data["gameInfo"].get("attendance"),
                    "capacity": (
                        data["gameInfo"]["venue"].get("capacity")
                        if "venue" in data["gameInfo"]
                        else None
                    ),
                    "roster": data["rosters"][i].get("roster", None),
                }
                if "statistics" in data["boxscore"]["teams"][i]:
                    for stat in data["boxscore"]["teams"][i]["statistics"]:
                        match_sheet[stat["name"]] = stat["displayValue"]
                df_list.append(match_sheet)
        return (
            pd.DataFrame(df_list)
            .replace({"team": TEAMNAME_REPLACEMENTS})
            .pipe(standardize_colnames)
            .set_index(["league", "season", "game", "team"])
            .sort_index()
        )

    def read_lineup(  # noqa: C901
        self, match_id: Optional[Union[int, list[int]]] = None
    ) -> pd.DataFrame:
        """Retrieve lineups for the selected leagues and seasons.

        Parameters
        ----------
        match_id : int or list of int, optional
            Retrieve the lineup for a specific game.

        Raises
        ------
        ValueError
            If no games with the given IDs were found for the selected seasons and leagues.

        Returns
        -------
        pd.DataFrame.
        """
        urlmask = ESPN_API + "/{}/summary?event={}"
        filemask = "Summary_{}.json"

        df_schedule = self.read_schedule().reset_index()
        if match_id is not None:
            iterator = df_schedule[
                df_schedule.game_id.isin([match_id] if isinstance(match_id, int) else match_id)
            ]
            if len(iterator) == 0:
                raise ValueError(
                    "No games with the given IDs found for the selected seasons and leagues."
                )
        else:
            iterator = df_schedule

        df_list = []
        for i, match in iterator.iterrows():
            url = urlmask.format(match["league_id"], match["game_id"])
            filepath = self.data_dir / filemask.format(match["game_id"])
            reader = self.get(url, filepath)

            data = json.load(reader)
            for i in range(2):
                if "roster" not in data["rosters"][i]:
                    logger.info(
                        "No lineup info found for team %d in game with ID=%s",
                        i + 1,
                        match["game_id"],
                    )
                    continue
                for p in data["rosters"][i]["roster"]:
                    match_sheet = {
                        "game": match["game"],
                        "league": match["league"],
                        "season": match["season"],
                        "team": data["boxscore"]["form"][i]["team"]["displayName"],
                        "is_home": (i == 0),
                        "player": p["athlete"]["displayName"],
                        "position": p["position"]["name"] if "position" in p else None,
                        "formation_place": p.get("formationPlace", None),
                    }
                    subbed_in = (
                        p["subbedIn"]
                        if isinstance(p["subbedIn"], bool)
                        else p["subbedIn"]["didSub"]
                    )
                    subbed_out = (
                        p["subbedOut"]
                        if isinstance(p["subbedOut"], bool)
                        else p["subbedOut"]["didSub"]
                    )
                    subbed_events = []
                    if isinstance(p["subbedIn"], bool) and (subbed_in or subbed_out):
                        subbed_events = (
                            [e for e in p["plays"] if e["substitution"]]
                            if isinstance(p["subbedIn"], bool)
                            else [p["subbedIn"], p["subbedOut"]]
                        )
                    else:
                        if subbed_in:
                            subbed_events.append(p["subbedIn"])
                        if subbed_out:
                            subbed_events.append(p["subbedOut"])

                    if p["starter"]:
                        match_sheet["sub_in"] = "start"
                    elif subbed_in:
                        match_sheet["sub_in"] = sum(
                            map(
                                int,
                                re.findall(
                                    r"(\d{1,3})",
                                    subbed_events[0]["clock"]["displayValue"],
                                ),
                            )
                        )
                    else:
                        match_sheet["sub_in"] = None

                    if (p["starter"] or subbed_in) and not subbed_out:
                        match_sheet["sub_out"] = "end"
                    elif subbed_out:
                        j = 0 if not subbed_in else 1
                        match_sheet["sub_out"] = sum(
                            map(
                                int,
                                re.findall(
                                    r"(\d{1,3})",
                                    subbed_events[j]["clock"]["displayValue"],
                                ),
                            )
                        )
                    else:
                        match_sheet["sub_out"] = None

                    if "stats" in p:
                        for stat in p["stats"]:
                            match_sheet[stat["name"]] = stat["value"]

                    df_list.append(match_sheet)

        if len(df_list) == 0:
            return pd.DataFrame()

        return (
            pd.DataFrame(df_list)
            .replace({"team": TEAMNAME_REPLACEMENTS})
            .pipe(standardize_colnames)
            .set_index(["league", "season", "game", "team", "player"])
            .sort_index()
        )
