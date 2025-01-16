"""Scraper for http://whoscored.com."""

import itertools
import json
import re
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Callable, Literal, Optional, Union

import numpy as np
import pandas as pd
from lxml import html
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
)
from selenium.webdriver.common.by import By

from ._common import BaseSeleniumReader, make_game_id, standardize_colnames
from ._config import DATA_DIR, NOCACHE, NOSTORE, TEAMNAME_REPLACEMENTS, logger

WHOSCORED_DATADIR = DATA_DIR / "WhoScored"
WHOSCORED_URL = "https://www.whoscored.com"

COLS_EVENTS = {
    # The ID of the game
    "game_id": np.nan,
    # 'PreMatch', 'FirstHalf', 'SecondHalf', 'PostGame'
    "period": np.nan,
    # Integer indicating the minute of the event, ignoring stoppage time
    "minute": -1,
    # Integer indicating the second of the event, ignoring stoppage time
    "second": -1,
    # Integer indicating the minute of the event, taking into account stoppage time
    "expanded_minute": -1,
    # String describing the event type (e.g. 'Goal', 'Yellow Card', etc.)
    "type": np.nan,
    # String describing the event outcome ('Succesful' or 'Unsuccessful')
    "outcome_type": np.nan,
    # The ID of the team that the event is associated with
    "team_id": np.nan,
    # The name of the team that the event is associated with
    "team": np.nan,
    # The ID of the player that the event is associated with
    "player_id": np.nan,
    # The name of the player that the event is associated with
    "player": np.nan,
    # Coordinates of the event's location
    "x": np.nan,
    "y": np.nan,
    "end_x": np.nan,
    "end_y": np.nan,
    # Coordinates of a shot's location
    "goal_mouth_y": np.nan,
    "goal_mouth_z": np.nan,
    # The coordinates where the ball was blocked
    "blocked_x": np.nan,
    "blocked_y": np.nan,
    # List of dicts with event qualifiers
    "qualifiers": [],
    # Some boolean flags
    "is_touch": False,
    "is_shot": False,
    "is_goal": False,
    # 'Yellow', 'Red', 'SecondYellow'
    "card_type": np.nan,
    # The ID of an associated event
    "related_event_id": np.nan,
    # The ID of a secondary player that the event is associated with
    "related_player_id": np.nan,
}


def _parse_url(url: str) -> dict:
    """Parse a URL from WhoScored.

    Parameters
    ----------
    url : str
        URL to parse.

    Raises
    ------
    ValueError
        If the URL could not be parsed.

    Returns
    -------
    dict
    """
    patt = (
        r"^(?:https:\/\/www.whoscored.com)?\/"
        + r"(?:regions\/(\d+)\/)?"
        + r"(?:tournaments\/(\d+)\/)?"
        + r"(?:seasons\/(\d+)\/)?"
        + r"(?:stages\/(\d+)\/)?"
        + r"(?:matches\/(\d+)\/)?"
    )
    matches = re.search(patt, url, re.IGNORECASE)
    if matches:
        return {
            "region_id": matches.group(1),
            "league_id": matches.group(2),
            "season_id": matches.group(3),
            "stage_id": matches.group(4),
            "match_id": matches.group(5),
        }
    raise ValueError(f"Could not parse URL: {url}")


class WhoScored(BaseSeleniumReader):
    """Provides pd.DataFrames from data available at http://whoscored.com.

    Data will be downloaded as necessary and cached locally in
    ``~/soccerdata/data/WhoScored``.

    Parameters
    ----------
    leagues : string or iterable, optional
        IDs of Leagues to include.
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
    path_to_browser : Path, optional
        Path to the Chrome executable.
    headless : bool, default: True
        If True, will run Chrome in headless mode. Setting this to False might
        help to avoid getting blocked. Only supported for Selenium <4.13.
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
        data_dir: Path = WHOSCORED_DATADIR,
        path_to_browser: Optional[Path] = None,
        headless: bool = False,
    ):
        """Initialize the WhoScored reader."""
        super().__init__(
            leagues=leagues,
            proxy=proxy,
            no_cache=no_cache,
            no_store=no_store,
            data_dir=data_dir,
            path_to_browser=path_to_browser,
            headless=headless,
        )
        self.seasons = seasons  # type: ignore
        self.rate_limit = 5
        self.max_delay = 5
        if not self.no_store:
            (self.data_dir / "seasons").mkdir(parents=True, exist_ok=True)
            (self.data_dir / "matches").mkdir(parents=True, exist_ok=True)
            (self.data_dir / "previews").mkdir(parents=True, exist_ok=True)
            (self.data_dir / "events").mkdir(parents=True, exist_ok=True)

    def read_leagues(self) -> pd.DataFrame:
        """Retrieve the selected leagues from the datasource.

        Returns
        -------
        pd.DataFrame
        """
        url = WHOSCORED_URL
        filepath = self.data_dir / "tiers.json"
        reader = self.get(url, filepath, var="allRegions")

        data = json.load(reader)

        leagues = []
        for region in data:
            for league in region["tournaments"]:
                leagues.append(
                    {
                        "region_id": region["id"],
                        "region": region["name"],
                        "league_id": league["id"],
                        "league": league["name"],
                    }
                )

        return (
            pd.DataFrame(leagues)
            .assign(league=lambda x: x.region + " - " + x.league)
            .pipe(self._translate_league)
            .set_index("league")
            .loc[self._selected_leagues.keys()]
            .sort_index()
        )

    def read_seasons(self) -> pd.DataFrame:
        """Retrieve the selected seasons for the selected leagues.

        Returns
        -------
        pd.DataFrame
        """
        df_leagues = self.read_leagues()

        seasons = []
        for lkey, league in df_leagues.iterrows():
            url = (
                WHOSCORED_URL
                + f"/Regions/{league['region_id']}"
                + f"/Tournaments/{league['league_id']}"
            )
            filemask = "seasons/{}.html"
            filepath = self.data_dir / filemask.format(lkey)
            reader = self.get(url, filepath, var=None)

            # extract team links
            tree = html.parse(reader)
            for node in tree.xpath("//select[contains(@id,'seasons')]/option"):
                # extract team IDs from links
                season_url = node.get("value")
                season_id = _parse_url(season_url)["season_id"]
                seasons.append(
                    {
                        "league": lkey,
                        "season": self._season_code.parse(node.text),
                        "region_id": league.region_id,
                        "league_id": league.league_id,
                        "season_id": season_id,
                    }
                )

        return (
            pd.DataFrame(seasons)
            .set_index(["league", "season"])
            .sort_index()
            .loc[itertools.product(self.leagues, self.seasons)]
        )

    def read_season_stages(self, force_cache: bool = False) -> pd.DataFrame:
        """Retrieve the season stages for the selected leagues.

        Parameters
        ----------
        force_cache : bool
             By default no cached data is used for the current season.
             If True, will force the use of cached data anyway.

        Returns
        -------
        pd.DataFrame
        """
        df_seasons = self.read_seasons()
        filemask = "seasons/{}_{}.html"

        season_stages = []
        for (lkey, skey), season in df_seasons.iterrows():
            current_season = not self._is_complete(lkey, skey)

            # get season page
            url = (
                WHOSCORED_URL
                + f"/Regions/{season['region_id']}"
                + f"/Tournaments/{season['league_id']}"
                + f"/Seasons/{season['season_id']}"
            )
            filepath = self.data_dir / filemask.format(lkey, skey)
            reader = self.get(url, filepath, var=None, no_cache=current_season and not force_cache)
            tree = html.parse(reader)

            # get default season stage
            fixtures_url = tree.xpath("//a[text()='Fixtures']/@href")[0]
            stage_id = _parse_url(fixtures_url)["stage_id"]
            season_stages.append(
                {
                    "league": lkey,
                    "season": skey,
                    "region_id": season.region_id,
                    "league_id": season.league_id,
                    "season_id": season.season_id,
                    "stage_id": stage_id,
                    "stage": None,
                }
            )

            # extract additional stages
            for node in tree.xpath("//select[contains(@id,'stages')]/option"):
                stage_url = node.get("value")
                stage_id = _parse_url(stage_url)["stage_id"]
                season_stages.append(
                    {
                        "league": lkey,
                        "season": skey,
                        "region_id": season.region_id,
                        "league_id": season.league_id,
                        "season_id": season.season_id,
                        "stage_id": stage_id,
                        "stage": node.text,
                    }
                )

        return (
            pd.DataFrame(season_stages)
            .drop_duplicates(subset=["league", "season", "stage_id"], keep="last")
            .set_index(["league", "season"])
            .sort_index()
            .loc[itertools.product(self.leagues, self.seasons)]
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
        df_season_stages = self.read_season_stages(force_cache=force_cache)
        filemask_schedule = "matches/{}_{}_{}_{}.json"

        all_schedules = []
        for (lkey, skey), stage in df_season_stages.iterrows():
            current_season = not self._is_complete(lkey, skey)
            stage_id = stage["stage_id"]
            stage_name = stage["stage"]

            # get the calendar of the season stage
            season_stage_url = (
                WHOSCORED_URL
                + f"/Regions/{stage['region_id']}"
                + f"/Tournaments/{stage['league_id']}"
                + f"/Seasons/{stage['season_id']}"
                + f"/Stages/{stage['stage_id']}"
            )
            if stage_name is not None:
                calendar_filepath = self.data_dir / f"matches/{lkey}_{skey}_{stage_id}.html"
                logger.info(
                    "Retrieving calendar for %s %s (%s)",
                    lkey,
                    skey,
                    stage_name,
                )
            else:
                calendar_filepath = self.data_dir / f"matches/{lkey}_{skey}.html"
                logger.info(
                    "Retrieving calendar for %s %s",
                    lkey,
                    skey,
                )
            calendar = self.get(
                season_stage_url,
                calendar_filepath,
                var="wsCalendar",
                no_cache=current_season and not force_cache,
            )
            mask = json.load(calendar)["mask"]

            # get the fixtures for each month
            it = [(year, month) for year in mask for month in mask[year]]
            for i, (year, month) in enumerate(it):
                filepath = self.data_dir / filemask_schedule.format(lkey, skey, stage_id, month)
                url = WHOSCORED_URL + f"/tournaments/{stage_id}/data/?d={year}{(int(month)+1):02d}"

                if stage_name is not None:
                    logger.info(
                        "[%s/%s] Retrieving fixtures for %s %s (%s)",
                        i + 1,
                        len(it),
                        lkey,
                        skey,
                        stage_name,
                    )
                else:
                    logger.info(
                        "[%s/%s] Retrieving fixtures for %s %s",
                        i + 1,
                        len(it),
                        lkey,
                        skey,
                    )

                reader = self.get(
                    url, filepath, var=None, no_cache=current_season and not force_cache
                )
                data = json.load(reader)
                for tournament in data["tournaments"]:
                    df_schedule = pd.DataFrame(tournament["matches"])
                    df_schedule["league"] = lkey
                    df_schedule["season"] = skey
                    df_schedule["stage"] = stage_name
                    all_schedules.append(df_schedule)

        if len(all_schedules) == 0:
            return pd.DataFrame(index=["league", "season", "game"])

        # Construct the output dataframe
        return (
            pd.concat(all_schedules)
            .drop_duplicates(subset=["id"])
            .replace(
                {
                    "homeTeamName": TEAMNAME_REPLACEMENTS,
                    "awayTeamName": TEAMNAME_REPLACEMENTS,
                }
            )
            .rename(
                columns={
                    "homeTeamName": "home_team",
                    "awayTeamName": "away_team",
                    "id": "game_id",
                    "startTimeUtc": "date",
                }
            )
            .assign(date=lambda x: pd.to_datetime(x["date"]))
            .assign(game=lambda df: df.apply(make_game_id, axis=1))
            .pipe(standardize_colnames)
            .set_index(["league", "season", "game"])
            .sort_index()
        )

    def _read_game_info(self, game_id: int) -> dict:
        """Return game info available in the header."""
        urlmask = WHOSCORED_URL + "/Matches/{}"
        url = urlmask.format(game_id)
        data = {}
        self._driver.get(url)
        # league and season
        breadcrumb = self._driver.find_elements(
            By.XPATH,
            "//div[@id='breadcrumb-nav']/*[not(contains(@class, 'separator'))]",
        )
        country = breadcrumb[0].text
        league, season = breadcrumb[1].text.split(" - ")
        data["league"] = {v: k for k, v in self._all_leagues().items()}[f"{country} - {league}"]
        data["season"] = self._season_code.parse(season)
        # match header
        match_header = self._driver.find_element(By.XPATH, "//div[@id='match-header']")
        score_info = match_header.find_element(By.XPATH, ".//div[@class='teams-score-info']")
        data["home_team"] = score_info.find_element(
            By.XPATH, "./span[contains(@class,'home team')]"
        ).text
        data["result"] = score_info.find_element(
            By.XPATH, "./span[contains(@class,'result')]"
        ).text
        data["away_team"] = score_info.find_element(
            By.XPATH, "./span[contains(@class,'away team')]"
        ).text
        info_blocks = match_header.find_elements(By.XPATH, ".//div[@class='info-block cleared']")
        for block in info_blocks:
            for desc_list in block.find_elements(By.TAG_NAME, "dl"):
                for desc_def in desc_list.find_elements(By.TAG_NAME, "dt"):
                    desc_val = desc_def.find_element(By.XPATH, "./following-sibling::dd")
                    data[desc_def.text] = desc_val.text

        return data

    def read_missing_players(
        self,
        match_id: Optional[Union[int, list[int]]] = None,
        force_cache: bool = False,
    ) -> pd.DataFrame:
        """Retrieve a list of injured and suspended players ahead of each game.

        Parameters
        ----------
        match_id : int or list of int, optional
            Retrieve the missing players for a specific game.
        force_cache : bool
            By default no cached data is used to scrapre the list of available
            games for the current season. If True, will force the use of
            cached data anyway.

        Raises
        ------
        ValueError
            If the given match_id could not be found in the selected seasons.

        Returns
        -------
        pd.DataFrame
        """
        urlmask = WHOSCORED_URL + "/Matches/{}/Preview"
        filemask = "WhoScored/previews/{}_{}/{}.html"

        df_schedule = self.read_schedule(force_cache).reset_index()
        if match_id is not None:
            iterator = df_schedule[
                df_schedule.game_id.isin([match_id] if isinstance(match_id, int) else match_id)
            ]
            if len(iterator) == 0:
                raise ValueError("No games found with the given IDs in the selected seasons.")
        else:
            iterator = df_schedule.sample(frac=1)

        match_sheets = []
        for i, (_, game) in enumerate(iterator.iterrows()):
            url = urlmask.format(game.game_id)
            filepath = DATA_DIR / filemask.format(game["league"], game["season"], game["game_id"])

            logger.info(
                "[%s/%s] Retrieving game with id=%s",
                i + 1,
                len(iterator),
                game["game_id"],
            )
            reader = self.get(url, filepath, var=None)

            # extract missing players
            tree = html.parse(reader)
            for node in tree.xpath("//div[@id='missing-players']/div[2]/table/tbody/tr"):
                # extract team IDs from links
                match_sheets.append(
                    {
                        "league": game["league"],
                        "season": game["season"],
                        "game": game["game"],
                        "game_id": game["game_id"],
                        "team": game["home_team"],
                        "player": node.xpath("./td[contains(@class,'pn')]/a")[0].text,
                        "player_id": int(
                            node.xpath("./td[contains(@class,'pn')]/a")[0]
                            .get("href")
                            .split("/")[2]
                        ),
                        "reason": node.xpath("./td[contains(@class,'reason')]/span")[0].get(
                            "title"
                        ),
                        "status": node.xpath("./td[contains(@class,'confirmed')]")[0].text,
                    }
                )
            for node in tree.xpath("//div[@id='missing-players']/div[3]/table/tbody/tr"):
                # extract team IDs from links
                match_sheets.append(
                    {
                        "league": game["league"],
                        "season": game["season"],
                        "game": game["game"],
                        "game_id": game["game_id"],
                        "team": game["away_team"],
                        "player": node.xpath("./td[contains(@class,'pn')]/a")[0].text,
                        "player_id": int(
                            node.xpath("./td[contains(@class,'pn')]/a")[0]
                            .get("href")
                            .split("/")[2]
                        ),
                        "reason": node.xpath("./td[contains(@class,'reason')]/span")[0].get(
                            "title"
                        ),
                        "status": node.xpath("./td[contains(@class,'confirmed')]")[0].text,
                    }
                )

        if len(match_sheets) == 0:
            return pd.DataFrame(index=["league", "season", "game", "team", "player"])

        return (
            pd.DataFrame(match_sheets)
            .set_index(["league", "season", "game", "team", "player"])
            .sort_index()
        )

    def read_events(  # noqa: C901
        self,
        match_id: Optional[Union[int, list[int]]] = None,
        force_cache: bool = False,
        live: bool = False,
        output_fmt: Optional[str] = "events",
        retry_missing: bool = True,
        on_error: Literal["raise", "skip"] = "raise",
    ) -> Optional[Union[pd.DataFrame, dict[int, list], "OptaLoader"]]:  # type: ignore  # noqa: F821
        """Retrieve the the event data for each game in the selected leagues and seasons.

        Parameters
        ----------
        match_id : int or list of int, optional
            Retrieve the event stream for a specific game.
        force_cache : bool
            By default no cached data is used to scrape the list of available
            games for the current season. If True, will force the use of
            cached data anyway.
        live : bool
            If True, will not return a cached copy of the event data. This is
            usefull to scrape live data.
        output_fmt : str, default: 'events'
            The output format of the returned data. Possible values are:
                - 'events' (default): Returns a dataframe with all events.
                - 'raw': Returns the original unformatted WhoScored JSON.
                - 'spadl': Returns a dataframe with the SPADL representation
                  of the original events.
                  See https://socceraction.readthedocs.io/en/latest/documentation/SPADL.html#spadl
                - 'atomic-spadl': Returns a dataframe with the Atomic-SPADL representation
                  of the original events.
                  See https://socceraction.readthedocs.io/en/latest/documentation/SPADL.html#atomic-spadl
                - 'loader': Returns a socceraction.data.opta.OptaLoader
                  instance, which can be used to retrieve the actual data.
                  See https://socceraction.readthedocs.io/en/latest/modules/generated/socceraction.data.opta.OptaLoader.html#socceraction.data.opta.OptaLoader
                - None: Doesn't return any data. This is useful to just cache
                  the data without storing the events in memory.
        retry_missing : bool
            If no events were found for a game in a previous attempt, will
            retry to scrape the events
        on_error : "raise" or "skip", default: "raise"
            Wheter to raise an exception or to skip the game if an error occurs.

        Raises
        ------
        ValueError
            If the given match_id could not be found in the selected seasons.
        ConnectionError
            If the match page could not be retrieved.
        ImportError
            If the requested output format is 'spadl', 'atomic-spadl' or
            'loader' but the socceraction package is not installed.

        Returns
        -------
        See the description of the ``output_fmt`` parameter.
        """
        output_fmt = output_fmt.lower() if output_fmt is not None else None
        if output_fmt in ["loader", "spadl", "atomic-spadl"]:
            if self.no_store:
                raise ValueError(
                    f"The '{output_fmt}' output format is not supported "
                    "when using the 'no_store' option."
                )
            try:
                from socceraction.atomic.spadl import convert_to_atomic
                from socceraction.data.opta import OptaLoader
                from socceraction.data.opta.loader import _eventtypesdf
                from socceraction.data.opta.parsers import WhoScoredParser
                from socceraction.spadl.opta import convert_to_actions

                if output_fmt == "loader":
                    import socceraction
                    from packaging import version

                    if version.parse(socceraction.__version__) < version.parse("1.2.3"):
                        raise ImportError(
                            "The 'loader' output format requires socceraction >= 1.2.3"
                        )
            except ImportError:
                raise ImportError(
                    "The socceraction package is required to use the 'spadl' "
                    "or 'atomic-spadl' output format. "
                    "Please install it with `pip install socceraction`."
                )
        urlmask = WHOSCORED_URL + "/Matches/{}/Live"
        filemask = "events/{}_{}/{}.json"

        df_schedule = self.read_schedule(force_cache).reset_index()
        if match_id is not None:
            iterator = df_schedule[
                df_schedule.game_id.isin([match_id] if isinstance(match_id, int) else match_id)
            ]
            if len(iterator) == 0:
                raise ValueError("No games found with the given IDs in the selected seasons.")
        else:
            iterator = df_schedule.sample(frac=1)

        events = {}
        player_names = {}
        team_names = {}
        for i, (_, game) in enumerate(iterator.iterrows()):
            url = urlmask.format(game["game_id"])
            # get league and season
            logger.info(
                "[%s/%s] Retrieving game with id=%s",
                i + 1,
                len(iterator),
                game["game_id"],
            )
            filepath = self.data_dir / filemask.format(
                game["league"], game["season"], game["game_id"]
            )

            try:
                reader = self.get(
                    url,
                    filepath,
                    var="require.config.params['args'].matchCentreData",
                    no_cache=live,
                )
                reader_value = reader.read()
                if retry_missing and reader_value == b"null" or reader_value == b"":
                    reader = self.get(
                        url,
                        filepath,
                        var="require.config.params['args'].matchCentreData",
                        no_cache=True,
                    )
            except ConnectionError as e:
                if on_error == "skip":
                    logger.warning("Error while scraping game %s: %s", game["game_id"], e)
                    continue
                raise
            reader.seek(0)
            json_data = json.load(reader)
            if json_data is not None:
                player_names.update(
                    {int(k): v for k, v in json_data["playerIdNameDictionary"].items()}
                )
                team_names.update(
                    {
                        int(json_data[side]["teamId"]): json_data[side]["name"]
                        for side in ["home", "away"]
                    }
                )
                if "events" in json_data:
                    game_events = json_data["events"]
                    if output_fmt == "events":
                        df_events = pd.DataFrame(game_events)
                        df_events["game"] = game["game"]
                        df_events["league"] = game["league"]
                        df_events["season"] = game["season"]
                        df_events["game_id"] = game["game_id"]
                        events[game["game_id"]] = df_events
                    elif output_fmt == "raw":
                        events[game["game_id"]] = game_events
                    elif output_fmt in ["spadl", "atomic-spadl"]:
                        parser = WhoScoredParser(
                            str(filepath),
                            competition_id=game["league"],
                            season_id=game["season"],
                            game_id=game["game_id"],
                        )
                        df_events = (
                            pd.DataFrame.from_dict(parser.extract_events(), orient="index")
                            .merge(_eventtypesdf, on="type_id", how="left")
                            .reset_index(drop=True)
                        )
                        df_actions = convert_to_actions(
                            df_events, home_team_id=int(json_data["home"]["teamId"])
                        )
                        if output_fmt == "spadl":
                            events[game["game_id"]] = df_actions
                        else:
                            events[game["game_id"]] = convert_to_atomic(df_actions)

            else:
                logger.warning("No events found for game %s", game["game_id"])

        if output_fmt is None:
            return None

        if output_fmt == "raw":
            return events

        if output_fmt == "loader":
            return OptaLoader(
                root=self.data_dir,
                parser="whoscored",
                feeds={
                    "whoscored": str(Path("events/{competition_id}_{season_id}/{game_id}.json"))
                },
            )

        if len(events) == 0:
            return pd.DataFrame(index=["league", "season", "game"])

        df = (
            pd.concat(events.values())
            .pipe(standardize_colnames)
            .assign(
                player=lambda x: x.player_id.replace(player_names),
                team=lambda x: x.team_id.replace(team_names).replace(TEAMNAME_REPLACEMENTS),
            )
        )

        if output_fmt == "events":
            df = df.set_index(["league", "season", "game"]).sort_index()
            # add missing columns
            for col, default in COLS_EVENTS.items():
                if col not in df.columns:
                    df[col] = default
            df["outcome_type"] = df["outcome_type"].apply(
                lambda x: x.get("displayName") if pd.notnull(x) else x
            )
            df["card_type"] = df["card_type"].apply(
                lambda x: x.get("displayName") if pd.notnull(x) else x
            )
            df["type"] = df["type"].apply(lambda x: x.get("displayName") if pd.notnull(x) else x)
            df["period"] = df["period"].apply(
                lambda x: x.get("displayName") if pd.notnull(x) else x
            )
            df = df[list(COLS_EVENTS.keys())]

        return df

    def _handle_banner(self) -> None:
        try:
            # self._driver.get(WHOSCORED_URL)
            time.sleep(2)
            self._driver.find_element(By.XPATH, "//button[./span[text()='AGREE']]").click()
            time.sleep(2)
        except NoSuchElementException:
            # with open("/tmp/error.html", "w") as f:
            # f.write(self._driver.page_source)
            raise ElementClickInterceptedException()
