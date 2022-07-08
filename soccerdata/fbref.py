"""Scraper for http://fbref.com."""
import itertools
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

import numpy as np
import pandas as pd
from lxml import etree, html

from ._common import (
    BaseRequestsReader,
    make_game_id,
    season_code,
    standardize_colnames,
)
from ._config import DATA_DIR, NOCACHE, NOSTORE, TEAMNAME_REPLACEMENTS, logger

FBREF_DATADIR = DATA_DIR / "FBref"
FBREF_API = "https://fbref.com"


class FBref(BaseRequestsReader):
    """Provides pd.DataFrames from data at http://fbref.com.

    Data will be downloaded as necessary and cached locally in
    ``~/soccerdata/data/FBref``.

    Parameters
    ----------
    leagues : string or iterable, optional
        IDs of leagues to include.
    seasons : string, int or list, optional
        Seasons to include. Supports multiple formats.
        Examples: '16-17'; 2016; '2016-17'; [14, 15, 16]
    proxy : 'tor' or or dict or list(dict) or callable, optional
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
        leagues: Optional[Union[str, List[str]]] = None,
        seasons: Optional[Union[str, int, List]] = None,
        proxy: Optional[
            Union[str, Dict[str, str], List[Dict[str, str]], Callable[[], Dict[str, str]]]
        ] = None,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = FBREF_DATADIR,
    ):
        """Initialize FBref reader."""
        super().__init__(
            leagues=leagues,
            proxy=proxy,
            no_cache=no_cache,
            no_store=no_store,
            data_dir=data_dir,
        )
        self.rate_limit = 3
        self.seasons = seasons  # type: ignore

    def read_leagues(self) -> pd.DataFrame:
        """Retrieve selected leagues from the datasource.

        Returns
        -------
        pd.DataFrame
        """
        url = f"{FBREF_API}/en/comps/"
        filepath = self.data_dir / "leagues.html"
        reader = self.get(url, filepath)

        # extract league links
        leagues = []
        tree = html.parse(reader)
        for table in tree.xpath("//table[contains(@id, 'comps')]"):
            df_table = pd.read_html(etree.tostring(table, method="html"))[0]
            df_table["url"] = table.xpath(".//th[@data-stat='league_name']/a/@href")
            leagues.append(df_table)
        df = (
            pd.concat(leagues)
            .pipe(standardize_colnames)
            .rename(columns={"competition_name": "league"})
            .pipe(self._translate_league)
            .drop_duplicates(subset="league")
            .set_index("league")
            .sort_index()
        )
        df["country"] = df["country"].apply(
            lambda x: x.split(" ")[1] if isinstance(x, str) else None
        )
        return df[df.index.isin(self._selected_leagues.keys())]

    def read_seasons(self) -> pd.DataFrame:
        """Retrieve the selected seasons for the selected leagues.

        Returns
        -------
        pd.DataFrame
        """
        df_leagues = self.read_leagues()

        seasons = []
        for lkey, league in df_leagues.iterrows():
            url = FBREF_API + league.url
            filemask = "seasons_{}.html"
            filepath = self.data_dir / filemask.format(lkey)
            reader = self.get(url, filepath)

            # extract season links
            tree = html.parse(reader)
            df_table = pd.read_html(etree.tostring(tree), attrs={"id": "seasons"})[0]
            df_table["url"] = tree.xpath("//table[@id='seasons']//th[@data-stat='season']/a/@href")
            seasons.append(df_table)

        df = (
            pd.concat(seasons)
            .pipe(standardize_colnames)
            .rename(columns={"competition_name": "league"})
            .pipe(self._translate_league)
        )
        df["season"] = df["season"].apply(lambda x: season_code(x))
        df = df.set_index(["league", "season"]).sort_index()
        return df.loc[
            df.index.isin(itertools.product(self._selected_leagues.keys(), self.seasons))
        ]

    def read_team_season_stats(self, stat_type: str = "standard") -> pd.DataFrame:
        """Retrieve teams from the datasource for the selected leagues.

        The following stat types are available:
            * 'standard'
            * 'keeper'
            * 'keeper_adv'
            * 'shooting'
            * 'passing'
            * 'passing_types'
            * 'goal_shot_creation'
            * 'defense'
            * 'possession'
            * 'playing_time'
            * 'misc'

        Parameters
        ----------
        stat_type: str
            Type of stats to retrieve.

        Returns
        -------
        pd.DataFrame
        """
        # build url
        filemask = "teams_{}_{}.html"

        # get league IDs
        seasons = self.read_seasons()

        if stat_type == "goal_shot_creation":
            stat_type = "gca"

        # collect teams
        teams = []
        for (lkey, skey), season in seasons.iterrows():
            # read html page (league overview)
            filepath = self.data_dir / filemask.format(lkey, skey)
            url = FBREF_API + season.url
            reader = self.get(url, filepath)

            # extract team links
            tree = html.parse(reader)
            df_table = pd.read_html(
                etree.tostring(tree), attrs={"id": f"stats_squads_{stat_type}_for"}
            )[0]
            df_table["url"] = tree.xpath(
                f"//table[@id='stats_squads_{stat_type}_for']//th[@data-stat='squad']/a/@href"
            )
            df_table["league"] = lkey
            df_table["season"] = skey
            teams.append(df_table)

        # return data frame
        df = pd.concat(teams)
        rename_unnamed(df)
        df = (
            df.rename(columns={"Squad": "team"})
            .replace({"team": TEAMNAME_REPLACEMENTS})
            .set_index(["league", "season", "team"])
            .sort_index()
        )
        return df

    def read_player_season_stats(self, stat_type: str = "standard") -> pd.DataFrame:
        """Retrieve players from the datasource for the selected leagues.

        The following stat types are available:
            * 'standard'
            * 'shooting'
            * 'passing'
            * 'passing_types'
            * 'goal_shot_creation'
            * 'defense'
            * 'possession'
            * 'playing_time'
            * 'misc'
            * 'keeper'
            * 'keeper_adv'

        Parameters
        ----------
        stat_type :str
            Type of stats to retrieve.

        Returns
        -------
        pd.DataFrame
        """
        # build url
        filemask = "team_{}_{}_{}.html"

        # get league IDs
        teams = self.read_team_season_stats()

        if stat_type == "goal_shot_creation":
            stat_type = "gca"

        # collect teams
        players = []
        for (lkey, skey, tkey), team in teams.iterrows():
            # read html page (league overview)
            filepath = self.data_dir / filemask.format(lkey, skey, tkey)
            url = FBREF_API + team.url.item()
            print(url)
            reader = self.get(url, filepath)

            # extract team links
            tree = html.parse(reader)
            try:
                table = tree.xpath(f"//table[contains(@id, 'stats_{stat_type}')]")[0]
            except IndexError:
                logger.error("%s not available for %s in %s %s", stat_type, tkey, lkey, skey)
                continue
            df_table = pd.read_html(etree.tostring(table))[0]
            df_table["league"] = lkey
            df_table["season"] = skey
            df_table["team"] = tkey
            players.append(df_table)

        # return data frame
        df = pd.concat(players)
        rename_unnamed(df)
        df = (
            df.drop("Matches", axis=1, level=0)
            .rename(columns={"Player": "player"})
            .set_index(["league", "season", "team", "player"])
            .sort_index()
        )
        df["Nation"] = df["Nation"].apply(
            lambda x: x.split(" ")[1] if isinstance(x, str) else None
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
        # get league IDs
        seasons = self.read_seasons()

        # collect teams
        schedule = []
        for (lkey, skey), season in seasons.iterrows():
            # read html page (league overview)
            url_stats = FBREF_API + season.url
            filepath_stats = self.data_dir / f"teams_{lkey}_{skey}.html"
            reader = self.get(url_stats, filepath_stats)
            tree = html.parse(reader)

            url_fixtures = FBREF_API + tree.xpath("//a[text()='Scores & Fixtures']")[0].get("href")
            filepath_fixtures = self.data_dir / f"schedule_{lkey}_{skey}.html"
            current_season = not self._is_complete(lkey, skey)
            reader = self.get(
                url_fixtures, filepath_fixtures, no_cache=current_season and not force_cache
            )
            tree = html.parse(reader)
            table = tree.xpath("//table[contains(@id, 'sched')]")[0]
            df_table = pd.read_html(etree.tostring(table))[0]
            df_table["Match Report"] = [
                mlink.xpath("./a/@href")[0]
                if mlink.xpath("./a") and mlink.xpath("./a")[0].text == "Match Report"
                else None
                for mlink in table.xpath(".//td[@data-stat='match_report']")
            ]
            df_table["league"] = lkey
            df_table["season"] = skey
            df_table = df_table.dropna(how="all")
            schedule.append(df_table)
        df = (
            pd.concat(schedule)
            .rename(
                columns={
                    "Wk": "week",
                    "Home": "home_team",
                    "Away": "away_team",
                    "xG": "home_xg",
                    "xG.1": "away_xg",
                }
            )
            .replace(
                {
                    "home_team": TEAMNAME_REPLACEMENTS,
                    "away_team": TEAMNAME_REPLACEMENTS,
                }
            )
            .pipe(standardize_colnames)
        )
        df["date"] = pd.to_datetime(df["date"]).ffill()
        df["game"] = df.apply(make_game_id, axis=1)
        df.loc[~df.match_report.isna(), "game_id"] = (
            df.loc[~df.match_report.isna(), "match_report"].str.split("/").str[3]
        )
        df = df.set_index(["league", "season", "game"]).sort_index()
        return df

    def _parse_teams(self, tree: etree.ElementTree) -> List[Dict]:
        """Parse the teams from a match summary page.

        Parameters
        ----------
        tree : etree.ElementTree
            The match summary page.

        Returns
        -------
        list of dict
        """
        team_nodes = tree.xpath("//div[@class='scorebox']//strong/a")[:2]
        teams = []
        for team in team_nodes:
            teams.append({"id": team.get("href").split("/")[3], "name": team.text.strip()})
        return teams

    def read_lineup(
        self, match_id: Optional[Union[str, List[str]]] = None, force_cache: bool = False
    ) -> pd.DataFrame:
        """Retrieve lineups for the selected leagues and seasons.

        Parameters
        ----------
        match_id : int or list of int, optional
            Retrieve the lineup for a specific game.
        force_cache : bool
            By default no cached data is used to scrape the list of available
            games for the current season. If True, will force the use of
            cached data anyway.

        Raises
        ------
        ValueError
            If no games with the given IDs were found for the selected seasons and leagues.

        Returns
        -------
        pd.DataFrame.
        """
        urlmask = FBREF_API + "/en/matches/{}"
        filemask = "match_{}.html"

        # Retrieve games for which a match report is available
        df_schedule = self.read_schedule(force_cache).reset_index()
        df_schedule = df_schedule[~df_schedule.game_id.isna() & ~df_schedule.match_report.isnull()]
        # Select requested games if available
        if match_id is not None:
            iterator = df_schedule[
                df_schedule.game_id.isin([match_id] if isinstance(match_id, str) else match_id)
            ]
            if len(iterator) == 0:
                raise ValueError("No games found with the given IDs in the selected seasons.")
        else:
            iterator = df_schedule

        lineups = []
        for i, game in iterator.iterrows():
            url = urlmask.format(game["game_id"])
            # get league and season
            logger.info(
                "[%s/%s] Retrieving game with id=%s", i + 1, len(iterator), game["game_id"]
            )
            filepath = self.data_dir / filemask.format(game["game_id"])
            reader = self.get(url, filepath)
            tree = html.parse(reader)
            teams = self._parse_teams(tree)
            tables = tree.xpath("//div[@class='lineup']")
            for i, table in enumerate(tables):
                df_table = pd.read_html(etree.tostring(table))[0]
                df_table.columns = ["jersey_number", "player"]
                df_table["team"] = teams[i]["name"]
                if "Bench" in df_table.jersey_number.values:
                    bench_idx = df_table.index[df_table.jersey_number == "Bench"][0]
                    df_table.loc[:bench_idx, "is_starter"] = True
                    df_table.loc[bench_idx:, "is_starter"] = False
                    df_table["game"] = game["game"]
                    df_table["league"] = game["league"]
                    df_table["season"] = game["season"]
                    df_table["game"] = game["game"]
                    df_table.drop(bench_idx, inplace=True)
                lineups.append(df_table)
        df = pd.concat(lineups).set_index(["league", "season", "game", "team", "player"])
        # TODO: sub in, sub out, position
        return df

    def read_player_match_stats(
        self,
        stat_type: str = "summary",
        match_id: Optional[Union[str, List[str]]] = None,
        force_cache: bool = False,
    ) -> pd.DataFrame:
        """Retrieve the match stats for the selected leagues and seasons.

        The following stat types are available:
            * 'summary'
            * 'keepers'
            * 'passing'
            * 'passing_types'
            * 'defense'
            * 'possession'
            * 'misc'

        Parameters
        ----------
        stat_type : str
            Type of stats to retrieve.
        match_id : int or list of int, optional
            Retrieve the event stream for a specific game.
        force_cache : bool
            By default no cached data is used to scrape the list of available
            games for the current season. If True, will force the use of
            cached data anyway.

        Raises
        ------
        ValueError
            If no games with the given IDs were found for the selected seasons and leagues.

        Returns
        -------
        pd.DataFrame
        """
        urlmask = FBREF_API + "/en/matches/{}"
        filemask = "match_{}.html"

        # Retrieve games for which a match report is available
        df_schedule = self.read_schedule(force_cache).reset_index()
        df_schedule = df_schedule[~df_schedule.game_id.isna() & ~df_schedule.match_report.isnull()]
        # Selec requested games if available
        if match_id is not None:
            iterator = df_schedule[
                df_schedule.game_id.isin([match_id] if isinstance(match_id, str) else match_id)
            ]
            if len(iterator) == 0:
                raise ValueError("No games found with the given IDs in the selected seasons.")
        else:
            iterator = df_schedule

        stats = []
        for i, game in iterator.iterrows():
            url = urlmask.format(game["game_id"])
            # get league and season
            logger.info(
                "[%s/%s] Retrieving game with id=%s", i + 1, len(iterator), game["game_id"]
            )
            filepath = self.data_dir / filemask.format(game["game_id"])
            reader = self.get(url, filepath)
            tree = html.parse(reader)
            (home_team, away_team) = self._parse_teams(tree)
            if stat_type == "keepers":
                id_format = "keeper_stats_{}"
            else:
                id_format = "stats_{}_" + stat_type
            table = tree.xpath("//table[@id='" + id_format.format(home_team["id"]) + "']")[0]
            df_table = pd.read_html(etree.tostring(table))[0]
            df_table["team"] = home_team["name"]
            df_table["game_id"] = game["game_id"]
            stats.append(df_table)
            table = tree.xpath("//table[@id='" + id_format.format(away_team["id"]) + "']")[0]
            df_table = pd.read_html(etree.tostring(table))[0]
            df_table["team"] = away_team["name"]
            df_table["game"] = game["game"]
            df_table["league"] = game["league"]
            df_table["season"] = game["season"]
            df_table["game"] = game["game"]
            stats.append(df_table)

        df = pd.concat(stats)
        rename_unnamed(df)
        df = df[~df.Player.str.contains(r"^\d+\sPlayers$")]
        df = (
            df.rename(columns={"Player": "player"})
            .replace({"team": TEAMNAME_REPLACEMENTS})
            .set_index(["league", "season", "game", "team", "player"])
            .sort_index()
        )
        return df

    def read_shot_events(
        self, match_id: Optional[Union[str, List[str]]] = None, force_cache: bool = False
    ) -> pd.DataFrame:
        """Retrieve shooting and shot creation event data for the selected seasons or selected matches.

        The data returned includes who took the shot, when, with which body
        part and from how far away. Additionally, the player creating the
        chance and also the creation before this are included in the data.

        Parameters
        ----------
        match_id : int or list of int, optional
            Retrieve the lineup for a specific game.
        force_cache : bool
            By default no cached data is used to scrape the list of available
            games for the current season. If True, will force the use of
            cached data anyway.

        Raises
        ------
        ValueError
            If no games with the given IDs were found for the selected seasons and leagues.

        Returns
        -------
        pd.DataFrame.
        """
        urlmask = FBREF_API + "/en/matches/{}"
        filemask = "match_{}.html"

        # Retrieve games for which a match report is available
        df_schedule = self.read_schedule(force_cache).reset_index()
        df_schedule = df_schedule[~df_schedule.game_id.isna() & ~df_schedule.match_report.isnull()]
        # Selec requested games if available
        if match_id is not None:
            iterator = df_schedule[
                df_schedule.game_id.isin([match_id] if isinstance(match_id, str) else match_id)
            ]
            if len(iterator) == 0:
                raise ValueError("No games found with the given IDs in the selected seasons.")
        else:
            iterator = df_schedule

        shots = []
        for i, game in iterator.iterrows():
            url = urlmask.format(game["game_id"])
            # get league and season
            logger.info(
                "[%s/%s] Retrieving game with id=%s", i + 1, len(iterator), game["game_id"]
            )
            filepath = self.data_dir / filemask.format(game["game_id"])
            reader = self.get(url, filepath)
            tree = html.parse(reader)
            df_table = pd.read_html(etree.tostring(tree), attrs={"id": "shots_all"})[0]
            df_table["league"] = game["league"]
            df_table["season"] = game["season"]
            df_table["game"] = game["game"]
            shots.append(df_table)

        df = pd.concat(shots)
        rename_unnamed(df)
        df = (
            df.rename(columns={"Squad": "team"})
            .replace({"team": TEAMNAME_REPLACEMENTS})
            .pipe(
                standardize_colnames,
                cols=["Outcome", "Minute", "Distance", "Player", "Body Part", "Notes", "Event"],
            )
            .set_index(["league", "season", "game", "team", "player"])
            .sort_index()
            .dropna(how="all")
        )
        return df


def rename_unnamed(df: pd.DataFrame) -> None:
    """Rename unamed columns name for Pandas DataFrame.

    See https://stackoverflow.com/questions/30322581/pandas-read-multiindexed-csv-with-blanks

    Parameters
    ----------
    df : pd.DataFrame object
        Input dataframe
    """
    columns = pd.DataFrame(df.columns.tolist())
    columns.loc[columns[0].str.startswith("Unnamed:"), 0] = np.nan
    # columns[0] = columns[0].fillna(method="ffill")
    mask = pd.isnull(columns[0])
    columns[0] = columns[0].fillna("")
    columns.loc[mask, [0, 1]] = columns.loc[mask, [1, 0]].values
    df.columns = pd.MultiIndex.from_tuples(columns.to_records(index=False).tolist())
    # return df
