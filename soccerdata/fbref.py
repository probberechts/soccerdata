"""Scraper for http://fbref.com."""

import warnings
from datetime import datetime, timezone
from functools import reduce
from pathlib import Path
from typing import Callable, Optional, Union

import pandas as pd
from lxml import etree, html

from ._common import (
    BaseRequestsReader,
    SeasonCode,
    add_alt_team_names,
    make_game_id,
    standardize_colnames,
)
from ._config import DATA_DIR, NOCACHE, NOSTORE, TEAMNAME_REPLACEMENTS, logger

FBREF_DATADIR = DATA_DIR / "FBref"
FBREF_API = "https://fbref.com"

BIG_FIVE_DICT = {
    "Serie A": "ITA-Serie A",
    "Ligue 1": "FRA-Ligue 1",
    "La Liga": "ESP-La Liga",
    "Premier League": "ENG-Premier League",
    "Bundesliga": "GER-Bundesliga",
}


class FBref(BaseRequestsReader):
    """Provides pd.DataFrames from data at http://fbref.com.

    Data will be downloaded as necessary and cached locally in
    ``~/soccerdata/data/FBref``.

    Parameters
    ----------
    leagues : string or iterable, optional
        IDs of leagues to include. For efficiently reading data from the Top-5
        European leagues, use "Big 5 European Leagues Combined".
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
        self.rate_limit = 6
        self.seasons = seasons  # type: ignore
        # check if all top 5 leagues are selected
        if (
            set(BIG_FIVE_DICT.values()).issubset(self.leagues)
            and "Big 5 European Leagues Combined" not in self.leagues
        ):
            warnings.warn(
                "You are trying to scrape data for all of the Big 5 European leagues. "
                "This can be done more efficiently by setting "
                "leagues='Big 5 European Leagues Combined'.",
                stacklevel=1,
            )

    @property
    def leagues(self) -> list[str]:
        """Return a list of selected leagues."""
        if "Big 5 European Leagues Combined" in self._leagues_dict:
            for _, standardized_name in BIG_FIVE_DICT.items():
                if standardized_name in self._leagues_dict:
                    del self._leagues_dict[standardized_name]
        return list(self._leagues_dict.keys())

    @classmethod
    def _all_leagues(cls) -> dict[str, str]:
        """Return a dict mapping all canonical league IDs to source league IDs."""
        res = super()._all_leagues()
        res.update({"Big 5 European Leagues Combined": "Big 5 European Leagues Combined"})
        return res

    @property
    def _season_code(self) -> SeasonCode:
        if "Big 5 European Leagues Combined" in self.leagues:
            return SeasonCode.MULTI_YEAR
        return SeasonCode.from_leagues(self.leagues)

    def _is_complete(self, league: str, season: str) -> bool:
        """Check if a season is complete."""
        if league == "Big 5 European Leagues Combined":
            season_ends = datetime(
                datetime.strptime(season[-2:], "%y").year,  # noqa: DTZ007
                7,
                1,
                tzinfo=timezone.utc,
            )
            return datetime.now(tz=timezone.utc) >= season_ends
        return super()._is_complete(league, season)

    def read_leagues(self, split_up_big5: bool = False) -> pd.DataFrame:
        """Retrieve selected leagues from the datasource.

        Parameters
        ----------
        split_up_big5: bool
            If True, it will load the "Big 5 European Leagues Combined" instead of
            each league individually.

        Returns
        -------
        pd.DataFrame
        """
        url = f"{FBREF_API}/en/comps/"
        filepath = self.data_dir / "leagues.html"
        reader = self.get(url, filepath)

        # extract league links
        dfs = []
        tree = html.parse(reader)
        for html_table in tree.xpath("//table[contains(@id, 'comps')]"):
            df_table = _parse_table(html_table)
            df_table["url"] = html_table.xpath(".//th[@data-stat='league_name']/a/@href")
            dfs.append(df_table)

        df = (
            pd.concat(dfs)
            .pipe(standardize_colnames)
            .rename(columns={"competition_name": "league"})
            .pipe(self._translate_league)
            .drop_duplicates(subset="league")
            .set_index("league")
            .sort_index()
        )
        df["first_season"] = df["first_season"].apply(self._season_code.parse)
        df["last_season"] = df["last_season"].apply(self._season_code.parse)

        leagues = self.leagues
        if "Big 5 European Leagues Combined" in self.leagues and split_up_big5:
            leagues = list(
                (set(self.leagues) - {"Big 5 European Leagues Combined"})
                | set(BIG_FIVE_DICT.values())
            )
        return df[df.index.isin(leagues)]

    def read_seasons(self, split_up_big5: bool = False) -> pd.DataFrame:
        """Retrieve the selected seasons for the selected leagues.

        Parameters
        ----------
        split_up_big5: bool
            If True, it will load the "Big 5 European Leagues Combined" instead of
            each league individually.

        Returns
        -------
        pd.DataFrame
        """
        filemask = "seasons_{}.html"
        df_leagues = self.read_leagues(split_up_big5)

        seasons = []
        for lkey, league in df_leagues.iterrows():
            url = FBREF_API + league.url
            filepath = self.data_dir / filemask.format(lkey)
            reader = self.get(url, filepath)

            # extract season links
            tree = html.parse(reader)
            (html_table,) = tree.xpath("//table[@id='seasons']")
            df_table = _parse_table(html_table)
            df_table["url"] = html_table.xpath(
                "//th[@data-stat='year_id' or @data-stat='year']/a/@href"
            )
            # Override the competition name or add if missing
            df_table["Competition Name"] = lkey
            # Some tournaments have a "year" column instead of "season"
            if "Year" in df_table.columns:
                df_table.rename(columns={"Year": "Season"}, inplace=True)
            # Get the competition format
            if "Final" in df_table.columns:
                df_table["Format"] = "elimination"
            else:
                df_table["Format"] = "round-robin"
            seasons.append(df_table)

        df = pd.concat(seasons).pipe(standardize_colnames)
        df = df.rename(columns={"competition_name": "league"})
        df["season"] = df["season"].apply(self._season_code.parse)
        # if both a 20xx and 19xx season are available, drop the 19xx season
        df.drop_duplicates(subset=["league", "season"], keep="first", inplace=True)
        df = df.set_index(["league", "season"]).sort_index()
        return df.loc[(slice(None), self.seasons), ["format", "url"]]

    def read_team_season_stats(
        self, stat_type: str = "standard", opponent_stats: bool = False
    ) -> pd.DataFrame:
        """Retrieve aggregated season stats for all teams in the selected leagues and seasons.

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
        opponent_stats: bool
            If True, will retrieve opponent stats.

        Raises
        ------
        ValueError
            If ``stat_type`` is not valid.

        Returns
        -------
        pd.DataFrame
        """
        team_stats = [
            "standard",
            "keeper",
            "keeper_adv",
            "shooting",
            "passing",
            "passing_types",
            "goal_shot_creation",
            "defense",
            "possession",
            "playing_time",
            "misc",
        ]

        filemask = "teams_{}_{}_{}.html"

        if stat_type not in team_stats:
            raise ValueError(f"Invalid argument: stat_type should be in {team_stats}")

        if stat_type == "standard":
            page = "stats"
        elif stat_type == "keeper":
            page = "keepers"
        elif stat_type == "keeper_adv":
            page = "keepersadv"
        elif stat_type == "goal_shot_creation":
            page = "gca"
            stat_type = "gca"
        elif stat_type == "playing_time":
            page = "playingtime"
        else:
            page = stat_type

        if opponent_stats:
            stat_type += "_against"
        else:
            stat_type += "_for"

        # get league IDs
        seasons = self.read_seasons()

        # collect teams
        teams = []
        for (lkey, skey), season in seasons.iterrows():
            big_five = lkey == "Big 5 European Leagues Combined"
            tournament = season["format"] == "elimination"
            # read html page (league overview)
            filepath = self.data_dir / filemask.format(lkey, skey, stat_type if big_five else page)
            url = (
                FBREF_API
                + "/".join(season.url.split("/")[:-1])
                + (f"/{page}/squads/" if big_five else f"/{page}/" if tournament else "/")
                + season.url.split("/")[-1]
            )
            reader = self.get(url, filepath)

            # parse HTML and select table
            tree = html.parse(reader)
            (html_table,) = tree.xpath(
                f"//table[@id='stats_teams_{stat_type}' or @id='stats_squads_{stat_type}']"
            )
            df_table = _parse_table(html_table)
            df_table["league"] = lkey
            df_table["season"] = skey
            df_table["url"] = html_table.xpath(".//*[@data-stat='team']/a/@href")
            if big_five:
                df_table["league"] = (
                    df_table.xs("Comp", axis=1, level=1).squeeze().map(BIG_FIVE_DICT)
                )
                df_table.drop("Comp", axis=1, level=1, inplace=True)
                df_table.drop("Rk", axis=1, level=1, inplace=True)
            teams.append(df_table)

        # return data frame
        return (
            _concat(teams, key=["league", "season"])
            .rename(columns={"Squad": "team", "# Pl": "players_used"})
            .replace({"team": TEAMNAME_REPLACEMENTS})
            # .pipe(standardize_colnames)
            .set_index(["league", "season", "team"])
            .sort_index()
        )

    def read_team_match_stats(  # noqa: C901
        self,
        stat_type: str = "schedule",
        opponent_stats: bool = False,
        team: Optional[Union[str, list[str]]] = None,
        force_cache: bool = False,
    ) -> pd.DataFrame:
        """Retrieve the match logs for all teams in the selected leagues and seasons.

        The following stat types are available:
            * 'schedule'
            * 'keeper'
            * 'shooting'
            * 'passing'
            * 'passing_types'
            * 'goal_shot_creation'
            * 'defense'
            * 'possession'
            * 'misc'

        Parameters
        ----------
        stat_type: str
            Type of stats to retrieve.
        opponent_stats: bool
            If True, will retrieve opponent stats.
        team: str or list of str, optional
            Team(s) to retrieve. If None, will retrieve all teams.
        force_cache: bool
            By default no cached data is used for the current season.
            If True, will force the use of cached data anyway.

        Raises
        ------
        ValueError
            If ``stat_type`` is not valid.

        Returns
        -------
        pd.DataFrame
        """
        team_stats = [
            "schedule",
            "shooting",
            "keeper",
            "passing",
            "passing_types",
            "goal_shot_creation",
            "defense",
            "possession",
            "misc",
        ]

        filemask = "matchlogs_{}_{}_{}.html"

        if stat_type not in team_stats:
            raise ValueError(f"Invalid argument: stat_type should be in {team_stats}")

        if stat_type == "schedule" and opponent_stats:
            raise ValueError("Opponent stats are not available for the 'schedule' stat type")

        if stat_type == "goal_shot_creation":
            stat_type = "gca"

        opp_type = "against" if opponent_stats else "for"

        # get list of teams
        df_teams = self.read_team_season_stats()

        if team is not None:
            teams_to_check = add_alt_team_names(team)

            # select requested teams
            iterator = df_teams.loc[df_teams.index.isin(teams_to_check, level=2), :]
            if len(iterator) == 0:
                raise ValueError("No data found for the given teams in the selected seasons.")
        else:
            iterator = df_teams

        # collect match logs for each team
        stats = []
        for (lkey, skey, team), team_url in iterator.url.items():
            # read html page
            filepath = self.data_dir / filemask.format(team, skey, stat_type)
            if len(team_url.split("/")) == 6:  # already have season in the url
                url = (
                    FBREF_API
                    + team_url.rsplit("/", 1)[0]
                    + "/matchlogs"
                    + "/all_comps"
                    + f"/{stat_type}"
                )
            else:  # special case: latest season
                if SeasonCode.from_league(lkey) == SeasonCode.MULTI_YEAR:
                    _skey = SeasonCode.MULTI_YEAR.parse(skey)
                    season_format = "{}-{}".format(
                        datetime.strptime(_skey[:2], "%y").year,  # noqa: DTZ007
                        datetime.strptime(_skey[2:], "%y").year,  # noqa: DTZ007
                    )
                else:
                    season_format = SeasonCode.SINGLE_YEAR.parse(skey)
                url = (
                    FBREF_API
                    + team_url.rsplit("/", 1)[0]
                    + f"/{season_format}"
                    + "/matchlogs"
                    + "/all_comps"
                    + f"/{stat_type}"
                )

            current_season = not self._is_complete(lkey, skey)
            reader = self.get(url, filepath, no_cache=current_season and not force_cache)

            # parse HTML and select table
            tree = html.parse(reader)
            (html_table,) = tree.xpath(f"//table[@id='matchlogs_{opp_type}']")
            # remove for / against header
            for elem in html_table.xpath("//th[@data-stat='header_for_against']"):
                elem.text = ""
            # remove aggregate rows
            for elem in html_table.xpath("//tfoot"):
                elem.getparent().remove(elem)
            # parse table
            df_table = _parse_table(html_table)
            df_table["season"] = skey
            df_table["team"] = team
            df_table["Time"] = [
                x.get("csk", None) for x in html_table.xpath(".//td[@data-stat='start_time']")
            ]
            df_table["Match Report"] = [
                (
                    mlink.xpath("./a/@href")[0]
                    if mlink.xpath("./a") and mlink.xpath("./a")[0].text == "Match Report"
                    else None
                )
                for mlink in html_table.xpath(".//td[@data-stat='match_report']")
            ]
            nb_levels = df_table.columns.nlevels
            if nb_levels == 2:
                df_table = df_table.drop(["Match Report", "Time"], axis=1, level=1)
            stats.append(df_table)

        # return data frame
        df = (
            _concat(stats, key=["league", "season", "team"])
            .replace(
                {
                    "Opponent": TEAMNAME_REPLACEMENTS,
                }
            )
            .rename(columns={"Comp": "league"})
            .pipe(self._translate_league)
            .pipe(
                standardize_colnames,
                cols=[
                    "Team",
                    "Opponent",
                    "Venue",
                    "Date",
                    "Time",
                    "Round",
                    "Day",
                    "Result",
                    "Match Report",
                ],
            )
        )
        df["date"] = pd.to_datetime(df["date"]).ffill()
        # create match id column
        df_tmp = df[["team", "opponent", "venue", "date"]].copy()
        df_tmp.columns = ["team", "opponent", "venue", "date"]
        df_tmp["home_team"] = df_tmp.apply(
            lambda x: x["team"] if x["venue"] == "Home" else x["opponent"], axis=1
        )
        df_tmp["away_team"] = df_tmp.apply(
            lambda x: x["team"] if x["venue"] == "Away" else x["opponent"], axis=1
        )
        df["game"] = df_tmp.apply(make_game_id, axis=1)
        return (
            df
            # .dropna(subset="league")
            .set_index(["league", "season", "team", "game"])
            .sort_index()
            .loc[self.leagues]
        )

    def read_player_season_stats(self, stat_type: str = "standard") -> pd.DataFrame:
        """Retrieve players from the datasource for the selected leagues and seasons.

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

        Raises
        ------
        TypeError
            If ``stat_type`` is not valid.

        Returns
        -------
        pd.DataFrame
        """
        player_stats = [
            "standard",
            "keeper",
            "keeper_adv",
            "shooting",
            "passing",
            "passing_types",
            "goal_shot_creation",
            "defense",
            "possession",
            "playing_time",
            "misc",
        ]

        filemask = "players_{}_{}_{}.html"

        if stat_type not in player_stats:
            raise TypeError(f"Invalid argument: stat_type should be in {player_stats}")

        if stat_type == "standard":
            page = "stats"
        elif stat_type == "goal_shot_creation":
            page = "gca"
            stat_type = "gca"
        elif stat_type == "playing_time":
            page = "playingtime"
        elif stat_type == "keeper":
            page = "keepers"
        elif stat_type == "keeper_adv":
            page = "keepersadv"
        else:
            page = stat_type

        # get league IDs
        seasons = self.read_seasons()

        # collect players
        players = []
        for (lkey, skey), season in seasons.iterrows():
            big_five = lkey == "Big 5 European Leagues Combined"
            filepath = self.data_dir / filemask.format(lkey, skey, stat_type)
            url = (
                FBREF_API
                + "/".join(season.url.split("/")[:-1])
                + f"/{page}"
                + ("/players/" if big_five else "/")
                + season.url.split("/")[-1]
            )
            reader = self.get(url, filepath)
            tree = html.parse(reader)
            # remove icons
            for elem in tree.xpath("//td[@data-stat='comp_level']//span"):
                elem.getparent().remove(elem)
            if big_five:
                df_table = _parse_table(tree)
                df_table[("Unnamed: league", "league")] = (
                    df_table.xs("Comp", axis=1, level=1).squeeze().map(BIG_FIVE_DICT)
                )
                df_table[("Unnamed: season", "season")] = skey
                df_table.drop("Comp", axis=1, level=1, inplace=True)
            else:
                (el,) = tree.xpath(f"//comment()[contains(.,'div_stats_{stat_type}')]")
                parser = etree.HTMLParser(recover=True)
                (html_table,) = etree.fromstring(el.text, parser).xpath(
                    f"//table[contains(@id, 'stats_{stat_type}')]"
                )
                df_table = _parse_table(html_table)
                df_table[("Unnamed: league", "league")] = lkey
                df_table[("Unnamed: season", "season")] = skey
            df_table = _fix_nation_col(df_table)
            players.append(df_table)

        # return dataframe
        df = _concat(players, key=["league", "season"])
        df = df[df.Player != "Player"]
        return (
            df.drop("Matches", axis=1, level=0)
            .drop("Rk", axis=1, level=0)
            .rename(columns={"Squad": "team"})
            .replace({"team": TEAMNAME_REPLACEMENTS})
            .pipe(standardize_colnames, cols=["Player", "Nation", "Pos", "Age", "Born"])
            .set_index(["league", "season", "team", "player"])
            .sort_index()
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
        # get league IDs
        seasons = self.read_seasons(split_up_big5=True)

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
                url_fixtures,
                filepath_fixtures,
                no_cache=current_season and not force_cache,
            )
            tree = html.parse(reader)
            html_table = tree.xpath("//table[contains(@id, 'sched')]")[0]
            df_table = _parse_table(html_table)
            df_table["Match Report"] = [
                (
                    mlink.xpath("./a/@href")[0]
                    if mlink.xpath("./a") and mlink.xpath("./a")[0].text == "Match Report"
                    else None
                )
                for mlink in html_table.xpath(".//td[@data-stat='match_report']")
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
        return df.set_index(["league", "season", "game"]).sort_index()

    def _parse_teams(self, tree: etree.ElementTree) -> list[dict]:
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

    def read_player_match_stats(
        self,
        stat_type: str = "summary",
        match_id: Optional[Union[str, list[str]]] = None,
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
        TypeError
            If ``stat_type`` is not valid.

        Returns
        -------
        pd.DataFrame
        """
        match_stats = [
            "summary",
            "keepers",
            "passing",
            "passing_types",
            "defense",
            "possession",
            "misc",
        ]

        urlmask = FBREF_API + "/en/matches/{}"
        filemask = "match_{}.html"

        if stat_type not in match_stats:
            raise TypeError(f"Invalid argument: stat_type should be in {match_stats}")

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
        for i, game in iterator.reset_index().iterrows():
            url = urlmask.format(game["game_id"])
            # get league and season
            logger.info(
                "[%s/%s] Retrieving game with id=%s",
                i + 1,
                len(iterator),
                game["game_id"],
            )
            filepath = self.data_dir / filemask.format(game["game_id"])
            reader = self.get(url, filepath)
            tree = html.parse(reader)
            (home_team, away_team) = self._parse_teams(tree)
            id_format = "keeper_stats_{}" if stat_type == "keepers" else "stats_{}_" + stat_type
            html_table = tree.find("//table[@id='" + id_format.format(home_team["id"]) + "']")
            if html_table is not None:
                df_table = _parse_table(html_table)
                df_table["team"] = home_team["name"]
                df_table["game"] = game["game"]
                df_table["league"] = game["league"]
                df_table["season"] = game["season"]
                df_table["game_id"] = game["game_id"]
                stats.append(df_table)
            else:
                logger.warning("No stats found for home team for game with id=%s", game["game_id"])
            html_table = tree.find("//table[@id='" + id_format.format(away_team["id"]) + "']")
            if html_table is not None:
                df_table = _parse_table(html_table)
                df_table["team"] = away_team["name"]
                df_table["game"] = game["game"]
                df_table["league"] = game["league"]
                df_table["season"] = game["season"]
                df_table["game_id"] = game["game_id"]
                stats.append(df_table)
            else:
                logger.warning("No stats found for away team for game with id=%s", game["game_id"])

        df = _concat(stats, key=["game"])
        df = df[~df.Player.str.contains(r"^\d+\sPlayers$")]
        return (
            df.rename(columns={"#": "jersey_number"})
            .replace({"team": TEAMNAME_REPLACEMENTS})
            .pipe(standardize_colnames, cols=["Player", "Nation", "Pos", "Age", "Min"])
            .set_index(["league", "season", "game", "team", "player"])
            .sort_index()
        )

    def read_lineup(
        self,
        match_id: Optional[Union[str, list[str]]] = None,
        force_cache: bool = False,
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
        for i, game in iterator.reset_index().iterrows():
            url = urlmask.format(game["game_id"])
            # get league and season
            logger.info(
                "[%s/%s] Retrieving game with id=%s",
                i + 1,
                len(iterator),
                game["game_id"],
            )
            filepath = self.data_dir / filemask.format(game["game_id"])
            reader = self.get(url, filepath)
            tree = html.parse(reader)
            teams = self._parse_teams(tree)
            html_tables = tree.xpath("//div[@class='lineup']")
            for i, html_table in enumerate(html_tables):
                # parse lineup table
                df_table = _parse_table(html_table)
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
                # augment with stats
                html_stats_table = tree.find(
                    "//table[@id='" + "stats_{}_summary".format(teams[i]["id"]) + "']"
                )
                df_stats_table = _parse_table(html_stats_table)
                df_stats_table = df_stats_table.droplevel(0, axis=1)[["Player", "#", "Pos", "Min"]]
                df_stats_table.columns = [
                    "player",
                    "jersey_number",
                    "position",
                    "minutes_played",
                ]
                df_stats_table["jersey_number"] = df_stats_table["jersey_number"].astype("Int64")
                df_table["jersey_number"] = df_table["jersey_number"].astype("Int64")
                df_table = pd.merge(
                    df_table, df_stats_table, on=["player", "jersey_number"], how="left"
                )
                df_table["minutes_played"] = df_table["minutes_played"].fillna(0)
                lineups.append(df_table)
        return pd.concat(lineups).set_index(["league", "season", "game"])

    def read_events(
        self,
        match_id: Optional[Union[str, list[str]]] = None,
        force_cache: bool = False,
    ) -> pd.DataFrame:
        """Retrieve match events for the selected seasons or selected matches.

        The data returned includes the timing of goals, cards and substitutions.
        Also includes the players who are involved in the event.

        Parameters
        ----------
        match_id : int or list of int, optional
            Retrieve the events for a specific game.
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

        events = []
        for i, game in iterator.reset_index().iterrows():
            match_events = []
            url = urlmask.format(game["game_id"])
            # get league and season
            logger.info(
                "[%s/%s] Retrieving game with id=%s",
                i + 1,
                len(iterator),
                game["game_id"],
            )
            filepath = self.data_dir / filemask.format(game["game_id"])
            reader = self.get(url, filepath)
            tree = html.parse(reader)
            teams = self._parse_teams(tree)
            for team, tid in zip(teams, ["a", "b"]):
                html_events = tree.xpath(f"////*[@id='events_wrap']/div/div[@class='event {tid}']")
                for e in html_events:
                    minute = e.xpath("./div[1]")[0].text.replace("&rsquor;", "").strip()
                    score = e.xpath("./div[1]/small/span")[0].text
                    player1 = e.xpath("./div[2]/div[2]/div")[0].text_content().strip()
                    if e.xpath("./div[2]/div[2]/small/a"):
                        player2 = e.xpath("./div[2]/div[2]/small/a")[0].text
                    else:
                        player2 = None
                    event_type = e.xpath("./div[2]/div[1]/@class")[0].split(" ")[1]
                    match_events.append(
                        {
                            "team": team["name"],
                            "minute": minute,
                            "score": score,
                            "player1": player1,
                            "player2": player2,
                            "event_type": event_type,
                        }
                    )
            df_match_events = pd.DataFrame(match_events)
            df_match_events["game"] = game["game"]
            df_match_events["league"] = game["league"]
            df_match_events["season"] = game["season"]
            if len(df_match_events) > 0:
                df_match_events.sort_values(by="minute", inplace=True)
            events.append(df_match_events)

        if len(events) == 0:
            return pd.DataFrame()

        return (
            pd.concat(events)
            .replace({"team": TEAMNAME_REPLACEMENTS})
            .set_index(["league", "season", "game"])
            .sort_index()
            .dropna(how="all")
        )

    def read_shot_events(
        self,
        match_id: Optional[Union[str, list[str]]] = None,
        force_cache: bool = False,
    ) -> pd.DataFrame:
        """Retrieve shooting data for the selected seasons or selected matches.

        The data returned includes who took the shot, when, with which body
        part and from how far away. Additionally, the player creating the
        chance and also the creation before this are included in the data.

        Parameters
        ----------
        match_id : int or list of int, optional
            Retrieve the shots for a specific game.
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
        for i, game in iterator.reset_index().iterrows():
            url = urlmask.format(game["game_id"])
            # get league anigd season
            logger.info(
                "[%s/%s] Retrieving game with id=%s",
                i + 1,
                len(iterator),
                game["game_id"],
            )
            filepath = self.data_dir / filemask.format(game["game_id"])
            reader = self.get(url, filepath)
            tree = html.parse(reader)
            html_table = tree.find("//table[@id='shots_all']")
            if html_table is not None:
                df_table = _parse_table(html_table)
                df_table["league"] = game["league"]
                df_table["season"] = game["season"]
                df_table["game"] = game["game"]
                shots.append(df_table)
            else:
                logger.warning("No shot data found for game with id=%s", game["game_id"])

        if len(shots) == 0:
            return pd.DataFrame()

        return (
            _concat(shots, key=["game"])
            .rename(columns={"Squad": "team"})
            .replace({"team": TEAMNAME_REPLACEMENTS})
            .pipe(
                standardize_colnames,
                cols=[
                    "Outcome",
                    "Minute",
                    "Distance",
                    "Player",
                    "Body Part",
                    "Notes",
                    "Event",
                ],
            )
            .set_index(["league", "season", "game"])
            .sort_index()
            .dropna(how="all")
        )


def _parse_table(html_table: html.HtmlElement) -> pd.DataFrame:
    """Parse HTML table into a dataframe.

    Parameters
    ----------
    html_table : lxml.html.HtmlElement
        HTML table to clean up.

    Returns
    -------
    pd.DataFrame
    """
    # remove icons
    for elem in html_table.xpath("//span[contains(@class, 'f-i')]"):
        etree.strip_elements(elem.getparent(), "span", with_tail=False)
    # remove sep rows
    for elem in html_table.xpath("//tbody/tr[contains(@class, 'spacer')]"):
        elem.getparent().remove(elem)
    # remove thead rows in the table body
    for elem in html_table.xpath("//tbody/tr[contains(@class, 'thead')]"):
        elem.getparent().remove(elem)
    # parse HTML to dataframe
    (df_table,) = pd.read_html(html.tostring(html_table), flavor="lxml")
    return df_table.convert_dtypes()


def _concat(dfs: list[pd.DataFrame], key: list[str]) -> pd.DataFrame:
    """Merge matching tables scraped from different pages.

    The level 0 headers are not consistent across seasons and leagues, this
    function tries to determine uniform column names.

    If there are dataframes with different columns, we will use the ones from
    the dataframe with the most columns.

    Parameters
    ----------
    dfs : list(pd.DataFrame)
        Input dataframes.
    key : list(str)
        List of columns that uniquely identify each df.

    Returns
    -------
    pd.DataFrame
        Concatenated dataframe with uniform column names.
    """
    all_columns = []

    # Step 0: Sort dfs by the number of columns
    dfs = sorted(dfs, key=lambda x: len(x.columns), reverse=True)

    # Step 1: Clean up the columns of each dataframe that should be merged
    for df in dfs:
        columns = pd.DataFrame(df.columns.tolist())
        # Set "Unnamed: ..." column names to None
        columns.replace(to_replace=r"^Unnamed:.*", value=None, regex=True, inplace=True)
        if columns.shape[1] == 2:
            # Set "" column names to None
            columns.replace(to_replace="", value=None, inplace=True)
            # Move None column names to level 0
            mask = pd.isnull(columns[1])
            columns.loc[mask, [0, 1]] = columns.loc[mask, [1, 0]].values

            # We'll try to replace some the None values in step 2
            all_columns.append(columns.copy())
            # But for now, we assume that we cannot replace them and move all
            # missing columns to level 1 and replace them with the empty string
            mask = pd.isnull(columns[0])
            columns.loc[mask, [0, 1]] = columns.loc[mask, [1, 0]].values
            columns.loc[mask, 1] = ""
            df.columns = pd.MultiIndex.from_tuples(columns.to_records(index=False).tolist())

    # throw a warning if not all dataframes have the same length and level 1 columns
    if len(all_columns) and all_columns[0].shape[1] == 2:
        for i, columns in enumerate(all_columns):
            if not columns[1].equals(all_columns[0][1]):
                res = all_columns[0].merge(columns, indicator=True, how="outer")
                warnings.warn(
                    (
                        "Different columns found for {first} and {cur}.\n\n"
                        + "The following columns are missing in {first}: {extra_cols}.\n\n"
                        + "The following columns are missing in {cur}: {missing_cols}.\n\n"
                        + "The columns of the dataframe with the most columns will be used."
                    ).format(
                        first=dfs[0].iloc[:1][key].values,
                        cur=dfs[i].iloc[:1][key].values,
                        extra_cols=", ".join(
                            map(
                                str,
                                res.loc[res["_merge"] == "left_only", [0, 1]]
                                .to_records(index=False)
                                .tolist(),
                            )
                        ),
                        missing_cols=", ".join(
                            map(
                                str,
                                res.loc[res["_merge"] == "right_only", [0, 1]]
                                .to_records(index=False)
                                .tolist(),
                            )
                        ),
                    ),
                    stacklevel=1,
                )

    if len(all_columns) and all_columns[0].shape[1] == 2:
        # Step 2: Look for the most complete level 0 columns
        columns = reduce(lambda left, right: left.combine_first(right), all_columns)

        # Step 3: Make sure columns are consistent
        mask = pd.isnull(columns[0])
        columns.loc[mask, [0, 1]] = columns.loc[mask, [1, 0]].values
        columns.loc[mask, 1] = ""
        column_idx = pd.MultiIndex.from_tuples(columns.to_records(index=False).tolist())

        for i, df in enumerate(dfs):
            if df.columns.equals(column_idx):
                # This dataframe already has the uniform column index
                pass
            if len(df.columns) == len(column_idx):
                # This dataframe has the same number of columns and the same
                # level 1 columns, we assume that the level 0 columns can be
                # replaced
                df.columns = column_idx
            else:
                # This dataframe has a different number of columns, so we want
                # to make sure its columns match with column_idx
                dfs[i] = df.reindex(columns=column_idx, fill_value=None)

    return pd.concat(dfs)


def _fix_nation_col(df_table: pd.DataFrame) -> pd.DataFrame:
    """Fix the "Nation" column.

    Adds a 'nations' column for international games based on the team's name.

    Parameters
    ----------
    df_table : pd.DataFrame
        Input dataframe.

    Returns
    -------
    pd.DataFrame
    """
    if "Nation" not in df_table.columns.get_level_values(1):
        df_table.loc[:, (slice(None), "Squad")] = (
            df_table.xs("Squad", axis=1, level=1)
            .squeeze()
            .apply(lambda x: x if isinstance(x, str) and x != "Squad" else None)
        )
        df_table.insert(
            2,
            ("Unnamed: nation", "Nation"),
            df_table.xs("Squad", axis=1, level=1).squeeze(),
        )
    return df_table
