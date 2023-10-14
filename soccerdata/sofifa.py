"""Scraper for http://sofifa.com."""
import json
import re
from datetime import timedelta
from itertools import product
from pathlib import Path
from typing import Callable, Dict, List, Optional, Union

import pandas as pd
from lxml import html

from ._common import BaseRequestsReader, standardize_colnames
from ._config import DATA_DIR, NOCACHE, NOSTORE, TEAMNAME_REPLACEMENTS, logger

SO_FIFA_DATADIR = DATA_DIR / "SoFIFA"
SO_FIFA_API = "https://sofifa.com"


class SoFIFA(BaseRequestsReader):
    """Provides pd.DataFrames from data at http://sofifa.com.

    Data will be downloaded as necessary and cached locally in
    ``~/soccerdata/data/SoFIFA``.

    Parameters
    ----------
    leagues : string or iterable, optional
        IDs of leagues to include.
    versions : string, int or list of int, optional
        FIFA releases to include. Should be specified by their ID used in the URL
        (e.g., 230034). Alternatively, the string "all" can be used to include all
        versions and "latest" to include the latest version only. Defaults to
        "latest".
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
        leagues: Optional[Union[str, List[str]]] = None,
        versions: Union[str, int, List[int]] = "latest",
        proxy: Optional[
            Union[str, Dict[str, str], List[Dict[str, str]], Callable[[], Dict[str, str]]]
        ] = None,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = SO_FIFA_DATADIR,
    ):
        """Initialize SoFIFA reader."""
        super().__init__(
            leagues=leagues,
            proxy=proxy,
            no_cache=no_cache,
            no_store=no_store,
            data_dir=data_dir,
        )
        self.rate_limit = 1
        if versions == "latest":
            self.versions = self.read_versions().tail(n=1)
        elif versions == "all":
            self.versions = self.read_versions()
        elif isinstance(versions, int):
            self.versions = self.read_versions().loc[[versions]]
        elif isinstance(versions, list) and all(isinstance(v, int) for v in versions):
            self.versions = self.read_versions().loc[versions]
        else:
            raise ValueError(f"Invalid value for versions: {versions}")

    def read_leagues(self) -> pd.DataFrame:
        """Retrieve selected leagues from the datasource.

        Returns
        -------
        pd.DataFrame
        """
        # read home page (overview)
        filepath = self.data_dir / "leagues.json"
        urlmask = SO_FIFA_API + "/api/league"
        reader = self.get(urlmask, filepath)
        response = json.load(reader)

        # extract league links
        leagues = []
        for node in response["data"]:
            for child in node["childs"]:
                leagues.append(
                    {
                        "league_id": child["id"],
                        "league": f'[{child["nationName"]}] {child["value"]}',
                    }
                )
        return (
            pd.DataFrame(leagues)
            .pipe(self._translate_league)
            .set_index("league")
            .sort_index()
            .loc[self._selected_leagues.keys()]
        )

    def read_versions(self, max_age: Union[int, timedelta] = 1) -> pd.DataFrame:
        """Retrieve available FIFA releases and rating updates.

        Parameters
        ----------
        max_age : int for age in days, or timedelta object
            The max. age of the locally cached release history before a new
            version is downloaded.

        Raises
        ------
        TypeError
            If max_age is not an integer or timedelta object.

        Returns
        -------
        pd.DataFrame
        """
        # read home page (overview)
        filepath = self.data_dir / "index.html"
        reader = self.get(SO_FIFA_API, filepath, max_age)

        # extract FIFA releases
        versions = []
        tree = html.parse(reader)
        for i, node_fifa_edition in enumerate(tree.xpath("//header/div[2]/div/h2/div[1]/div/a")):
            fifa_edition = node_fifa_edition.text
            filepath = self.data_dir / f"updates_{fifa_edition}.html"
            url = SO_FIFA_API + node_fifa_edition.get("href")
            # check for updates on latest FIFA edition only
            reader = self.get(url, filepath, max_age=max_age if i == 0 else None)
            tree = html.parse(reader)

            for node_fifa_update in tree.xpath("//header/div[2]/div/h2/div[2]/div/a"):
                href = node_fifa_update.get("href")
                version_id = re.search(r"r=(\d+)", href).group(1)  # type: ignore
                versions.append(
                    {
                        "version_id": int(version_id),
                        "fifa_edition": fifa_edition,
                        "update": node_fifa_update.text,
                    }
                )
        return pd.DataFrame(versions).set_index("version_id").sort_index()

    def read_teams(self) -> pd.DataFrame:
        """Retrieve all teams for the selected leagues.

        Returns
        -------
        pd.DataFrame
        """
        # build url
        urlmask = SO_FIFA_API + "/teams?lg={}&r={}"
        filemask = "teams_{}_{}.html"

        # get league IDs
        leagues = self.read_leagues()

        # collect teams
        teams = []
        iterator = list(product(leagues.iterrows(), self.versions.iterrows()))
        for i, ((lkey, league), (version_id, version)) in enumerate(iterator):
            logger.info(
                "[%s/%s] Retrieving teams for %s in %s edition",
                i + 1,
                len(iterator),
                lkey,
                version["update"],
            )
            league_id = league["league_id"]
            # read html page (league overview)
            filepath = self.data_dir / filemask.format(league_id, version_id)
            url = urlmask.format(league_id, version_id)
            reader = self.get(url, filepath)

            # extract team links
            tree = html.parse(reader)
            pat_team = re.compile(r"\/team\/(\d+)\/[\w-]+\/")
            for node in tree.xpath("//table/tbody/tr"):
                # extract team IDs from links
                team_link = node.xpath(".//td[@class='col-name-wide']/a")[0]
                teams.append(
                    {
                        "team_id": int(
                            re.search(pat_team, team_link.get("href")).group(1)  # type: ignore
                        ),
                        "team": team_link.xpath("./div")[0].text,
                        "league": lkey,
                        **version.to_dict(),
                    }
                )

        # return data frame
        df = pd.DataFrame(teams).replace({"team": TEAMNAME_REPLACEMENTS}).set_index(["team_id"])
        return df

    def read_players(self, team: Optional[Union[str, List[str]]] = None) -> pd.DataFrame:
        """Retrieve all players for the selected leagues.

        Parameters
        ----------
        team: str or list of str, optional
            Team(s) to retrieve. If None, will retrieve all teams.

        Raises
        ------
        ValueError
            If no data is found for the given team(s) in the selected leagues.

        Returns
        -------
        pd.DataFrame
        """
        # build url
        urlmask = SO_FIFA_API + "/team/{}/?r={}&set=true"
        filemask = str(self.data_dir / "players_{}_{}.html")

        # get list of teams
        df_teams = self.read_teams()

        if team is not None:
            # get alternative names of the specified team(s)
            teams = [team] if isinstance(team, str) else team
            teams_to_check = []
            for team in teams:
                for alt_name, norm_name in TEAMNAME_REPLACEMENTS.items():
                    if norm_name == team:
                        teams_to_check.append(alt_name)
            teams_to_check.append(team)

            # select requested teams
            iterator = df_teams.loc[df_teams.team.isin(teams_to_check), :]
            if len(iterator) == 0:
                raise ValueError("No data found for the given teams in the selected seasons.")
        else:
            iterator = df_teams

        # collect players
        players = []
        iterator = list(product(self.versions.iterrows(), iterator.iterrows()))
        for i, ((version_id, version), (team_id, df_team)) in enumerate(iterator):
            logger.info(
                "[%s/%s] Retrieving list of players for %s in %s edition",
                i + 1,
                len(iterator),
                df_team["team"],
                version["update"],
            )

            # read html page (team overview)
            filepath = self.data_dir / filemask.format(team_id, version_id)
            url = urlmask.format(team_id, version_id)
            reader = self.get(url, filepath)

            # extract player links
            tree = html.parse(reader)
            pat_player = re.compile(r"\/player\/(\d+)\/[\w-]+\/")
            table_squad = tree.xpath("//div[@class='card']/table")
            for node in table_squad[0].xpath(
                ".//td[@class='col-name']/a[contains(@href,'/player/')]"
            ):
                # extract player IDs from links
                # extract player names from links
                players.append(
                    {
                        "player_id": int(
                            re.search(pat_player, node.get("href")).group(1)  # type: ignore
                        ),
                        "player": node.get("aria-label"),
                        "team": df_team["team"],
                        "league": df_team['league'],
                        **version.to_dict(),
                    }
                )

        # return data frame
        return pd.DataFrame(players).set_index(["player_id"])

    def read_team_ratings(self) -> pd.DataFrame:
        """Retrieve ratings for all teams in the selected leagues.

        Returns
        -------
        pd.DataFrame
        """
        # build url
        urlmask = SO_FIFA_API + "/teams?lg={}&r={}&set=true"
        filemask = "teams_{}_{}.html"

        # get league IDs
        leagues = self.read_leagues()

        # collect teams
        teams = []
        iterator = list(product(leagues.iterrows(), self.versions.iterrows()))
        for i, ((lkey, league), (version_id, version)) in enumerate(iterator):
            logger.info(
                "[%s/%s] Retrieving teams for %s in %s edition",
                i + 1,
                len(iterator),
                lkey,
                version["update"],
            )
            league_id = league["league_id"]
            # read html page (league overview)
            filepath = self.data_dir / filemask.format(league_id, version_id)
            url = urlmask.format(league_id, version_id)
            reader = self.get(url, filepath)

            # extract team links
            tree = html.parse(reader)
            for node in tree.xpath("//table/tbody/tr"):
                # extract team IDs from links
                teams.append(
                    {
                        "league": lkey,
                        "team": node.xpath(".//td[@class='col-name-wide']/a/div")[0].text,
                        "overall": node.xpath(".//td[@class='col col-oa']/span")[0].text,
                        "attack": node.xpath(".//td[@class='col col-at']/span")[0].text,
                        "midfield": node.xpath(".//td[@class='col col-md']/span")[0].text,
                        "defence": node.xpath(".//td[@class='col col-df']/span")[0].text,
                        "transfer_budget": node.xpath(".//td[@class='col col-tb']")[0].text,
                        "players": node.xpath(".//td[@class='col col-ps']")[0].text,
                        **version.to_dict(),
                    }
                )

        # return data frame
        df = (
            pd.DataFrame(teams)
            .replace({"team": TEAMNAME_REPLACEMENTS})
            .set_index(["league", "team"])
            .sort_index()
        )
        return df

    def read_player_ratings(
        self,
        team: Optional[Union[str, List[str]]] = None,
        player: Optional[Union[int, List[int]]] = None,
    ) -> pd.DataFrame:
        """Retrieve ratings for players.

        Parameters
        ----------
        team: str or list of str, optional
            Team(s) to retrieve. If None, will retrieve all teams.
        player: int or list of int, optional
            Player(s) to retrieve. If None, will retrieve all players.

        Returns
        -------
        pd.DataFrame
        """
        # build url
        urlmask = SO_FIFA_API + "/player/{}/?r={}&set=true"
        filemask = "player_{}_{}.html"

        # get player IDs
        if player is None:
            players = self.read_players(team=team).index.unique()
        elif isinstance(player, int):
            players = [player]
        else:
            players = player

        # prepare empty data frame
        ratings = []

        # define labels to use for score extraction from player profile pages
        score_labels = [
            "Overall rating",
            "Potential",
            "Crossing",
            "Finishing",
            "Heading accuracy",
            "Short passing",
            "Volleys",
            "Dribbling",
            "Curve",
            "FK Accuracy",
            "Long passing",
            "Ball control",
            "Acceleration",
            "Sprint speed",
            "Agility",
            "Reactions",
            "Balance",
            "Shot power",
            "Jumping",
            "Stamina",
            "Strength",
            "Long shots",
            "Aggression",
            "Interceptions",
            "Positioning",
            "Vision",
            "Penalties",
            "Composure",
            "Defensive awareness",
            "Standing tackle",
            "Sliding tackle",
            "GK Diving",
            "GK Handling",
            "GK Kicking",
            "GK Positioning",
            "GK Reflexes",
        ]

        iterator = list(product(self.versions.iterrows(), players))
        for i, ((version_id, version), player) in enumerate(iterator):
            logger.info(
                "[%s/%s] Retrieving ratings for player with ID %s in %s edition",
                i + 1,
                len(iterator),
                player,
                version["update"],
            )

            # read html page (player overview)
            filepath = self.data_dir / filemask.format(player, version_id)
            url = urlmask.format(player, version_id)
            reader = self.get(url, filepath)

            # extract scores one-by-one
            tree = html.parse(reader, parser=html.HTMLParser(encoding='utf8'))
            scores = {
                "player": tree.xpath("//div[@class='info']/h1")[0].text.strip(),
                **version.to_dict(),
            }
            for s in score_labels:
                nodes = tree.xpath(
                    "(//li[not(self::script)] | //div)"
                    f"[.//text()[contains(.,'{s}')]]"
                    "/span[contains(@class, 'tag')]"
                )
                # for multiple matches, only accept first match
                if len(nodes) >= 1:
                    scores[s] = nodes[0].text.strip()
                # if there's no match, put NA
                else:
                    scores[s] = None
            ratings.append(scores)
        # return data frame
        df = pd.DataFrame(ratings).pipe(standardize_colnames).set_index(["player"]).sort_index()
        return df
