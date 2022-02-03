"""Scraper for http://whoscored.com."""
import io
import itertools
import json
import random
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import IO, Dict, Iterable, List, Optional, Tuple, Union

import pandas as pd
from lxml import html

try:
    import undetected_chromedriver as uc
    from selenium.common.exceptions import (
        ElementClickInterceptedException,
        JavascriptException,
        NoSuchElementException,
        WebDriverException,
    )
    from selenium.webdriver.common.by import By
    from selenium.webdriver.remote.webelement import WebElement
    from selenium.webdriver.support import expected_conditions as ec
    from selenium.webdriver.support.ui import WebDriverWait

    _has_selenium = True
except ImportError:
    _has_selenium = False

from ._common import BaseReader, season_code, standardize_colnames
from ._config import DATA_DIR, NOCACHE, NOSTORE, TEAMNAME_REPLACEMENTS, logger

WHOSCORED_DATADIR = DATA_DIR / "WhoScored"
WHOSCORED_URL = "https://www.whoscored.com"


class WhoScored(BaseReader):
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
    use_tor : bool
        Whether to use the Tor network to hide your IP.
    use_addblocker : bool
        Set to True to use the AddBlocker extension. This requires
        `path_to_addblocker` to be set.
    no_cache : bool
        If True, will not use cached data.
    no_store : bool
        If True, will not store downloaded data.
    data_dir : Path
        Path to directory where data will be cached.
    path_to_browser : Path, optional
        Path to the Chrome executable.
    path_to_addblocker : Path, optional
        Path to the addblocker extension.
    """

    def __init__(
        self,
        leagues: Optional[Union[str, List[str]]] = None,
        seasons: Optional[Union[str, int, Iterable[Union[str, int]]]] = None,
        use_tor: bool = False,
        use_addblocker: bool = False,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = WHOSCORED_DATADIR,
        path_to_browser: Optional[Path] = None,
        path_to_addblocker: Optional[Path] = None,
    ):
        """Initialize the WhoScored reader."""
        super().__init__(
            no_cache=no_cache,
            no_store=no_store,
            leagues=leagues,
            use_tor=use_tor,
            data_dir=data_dir,
        )
        self.seasons = seasons  # type: ignore
        if not self.no_store:
            (self.data_dir / "seasons").mkdir(parents=True, exist_ok=True)
            (self.data_dir / "matches").mkdir(parents=True, exist_ok=True)
            (self.data_dir / "previews").mkdir(parents=True, exist_ok=True)
            (self.data_dir / "events").mkdir(parents=True, exist_ok=True)

        if not _has_selenium:
            raise ImportError("`selenium` is required to scrape data from WhoScored")

        try:
            self.driver = self._init_webdriver(
                path_to_browser,
                path_to_addblocker,
                use_tor,
                use_addblocker,
            )
        except WebDriverException as e:
            logger.error(
                """
                The ChromeDriver was unable to initiate/spawn a new
                WebBrowser. You will not be able to scrape new data.
                %s
                """,
                e,
            )

    def read_leagues(self) -> pd.DataFrame:
        """Retrieve the selected leagues from the datasource.

        Returns
        -------
        pd.DataFrame
        """
        url = WHOSCORED_URL
        filepath = self.data_dir / "tiers.json"
        reader = self._download_and_save(url, filepath, var="allRegions")

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
                        "url": league["url"],
                    }
                )

        df = (
            pd.DataFrame(leagues)
            .assign(league=lambda x: x.region + " - " + x.league)
            .pipe(self._translate_league)
            .set_index("league")
            .loc[self._selected_leagues.keys()]
            .sort_index()
        )
        return df

    def read_seasons(self) -> pd.DataFrame:
        """Retrieve the selected seasons for the selected leagues.

        Returns
        -------
        pd.DataFrame
        """
        df_leagues = self.read_leagues()

        seasons = []
        for lkey, league in df_leagues.iterrows():
            url = WHOSCORED_URL + league.url
            filemask = "seasons/{}.html"
            filepath = self.data_dir / filemask.format(lkey)
            reader = self._download_and_save(url, filepath, var=None)

            # extract team links
            tree = html.parse(reader)
            for node in tree.xpath("//select[contains(@id,'seasons')]/option"):
                # extract team IDs from links
                seasons.append(
                    {
                        "url": node.get("value"),
                        "league": lkey,
                        "league_id": league.league_id,
                        "season": season_code(node.text),
                    }
                )

        df = (
            pd.DataFrame(seasons)
            .set_index(["league", "season"])
            .sort_index()
            .loc[itertools.product(self.leagues, self.seasons)]
        )
        return df

    def _parse_season_stages(self) -> List[Dict]:
        match_selector = (
            "//div[contains(@id,'tournament-fixture')]//div[contains(@class,'divtable-row')]"
        )
        time.sleep(5 + random.random() * 5)
        WebDriverWait(self.driver, 30, poll_frequency=1).until(
            ec.presence_of_element_located((By.XPATH, match_selector))
        )
        stages = []
        node_stages = self.driver.find_elements_by_xpath("//select[contains(@id,'stages')]/option")
        for stage in node_stages:
            stages.append({"url": stage.get_attribute("value"), "name": stage.text})
        return stages

    def _parse_schedule_page(self) -> Tuple[List[Dict], Optional[WebElement]]:
        match_selector = (
            "//div[contains(@id,'tournament-fixture')]//div[contains(@class,'divtable-row')]"
        )
        time.sleep(5 + random.random() * 5)
        WebDriverWait(self.driver, 30, poll_frequency=1).until(
            ec.presence_of_element_located((By.XPATH, match_selector))
        )
        date_str = "Monday, Jan 1 2021"
        schedule_page = []
        for node in self.driver.find_elements_by_xpath(match_selector):
            if node.get_attribute("data-id"):
                time_str = node.find_element_by_xpath("./div[contains(@class,'time')]").text
                schedule_page.append(
                    {
                        # fmt: off
                        "game_id": int(
                            re.search(
                                r"Matches/(\d+)/",
                                node.find_element_by_xpath(
                                    "./div[contains(@class,'result')]//a"
                                ).get_attribute("href")).group(1)  # type: ignore
                        ),
                        # fmt: on
                        "home_team": node.find_element_by_xpath(
                            "./div[contains(@class,'team home')]//a"
                        ).text,
                        "away_team": node.find_element_by_xpath(
                            "./div[contains(@class,'team away')]//a"
                        ).text,
                        "date": datetime.strptime(f"{date_str} {time_str}", "%A, %b %d %Y %H:%M"),
                        "url": node.find_element_by_xpath(
                            "./div[contains(@class,'result')]//a"
                        ).get_attribute("href"),
                    }
                )
            else:
                date_str = node.find_element_by_xpath(
                    "./div[contains(@class,'divtable-header')]"
                ).text
                logger.info("Scraping game schedule for %s", date_str)

        try:
            next_page = self.driver.find_element_by_xpath(
                "//div[contains(@id,'date-controller')]/a[contains(@class,'previous') and not(contains(@class, 'is-disabled'))]"  # noqa: E501
            )
        except NoSuchElementException:
            next_page = None
        return schedule_page, next_page

    def _parse_schedule(self, stage: Optional[str] = None) -> List[Dict]:
        schedule = []
        # Parse first page
        page_schedule, next_page = self._parse_schedule_page()
        schedule.extend(page_schedule)
        # Go to next page
        while next_page is not None:
            try:
                next_page.click()
                logger.debug("Next page")
            except ElementClickInterceptedException:
                self._handle_banner()
            # Parse next page
            page_schedule, next_page = self._parse_schedule_page()
            schedule.extend(page_schedule)
        schedule = [dict(item, stage=stage) for item in schedule]
        return schedule

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
        df_seasons = self.read_seasons()
        filemask = "matches/{}_{}.csv"

        all_schedules = []
        for (lkey, skey), season in df_seasons.iterrows():
            filepath = self.data_dir / filemask.format(lkey, skey)
            url = WHOSCORED_URL + season.url
            current_season = not self._is_complete(lkey, skey)
            schedule = []
            if current_season and not force_cache or (not filepath.exists()) or self.no_cache:
                time.sleep(random.random() * 5)
                self.driver.get(url)
                stages = self._parse_season_stages()
                if len(stages) > 0:
                    for stage in stages:
                        url = WHOSCORED_URL + stage["url"].replace("Show", "Fixtures")
                        logger.info("Scraping game schedule with stage=%s from %s", stage, url)
                        self.driver.get(url)
                        schedule.extend(self._parse_schedule(stage=stage["name"]))
                else:
                    url = self.driver.find_element_by_xpath(
                        "//a[text()='Fixtures']"
                    ).get_attribute("href")
                    logger.info("Scraping game schedule from %s", url)
                    self.driver.get(url)
                    schedule.extend(self._parse_schedule())
                df_schedule = pd.DataFrame(schedule).assign(league=lkey, season=skey)
                if not self.no_store:
                    df_schedule.to_csv(filepath, index=False)
            else:
                logger.info("Retrieving game schedule of %s - %s from the cache", lkey, skey)
                df_schedule = pd.read_csv(filepath)
            all_schedules.append(df_schedule)

        df = (
            pd.concat(all_schedules)
            .drop_duplicates()
            .replace(
                {
                    "home_team": TEAMNAME_REPLACEMENTS,
                    "away_team": TEAMNAME_REPLACEMENTS,
                }
            )
            .set_index(["league", "season", "game_id"])
            .sort_index()
        )
        return df

    def _read_game_info(self, game_id: int) -> Dict:
        """Return game info available in the header."""
        urlmask = WHOSCORED_URL + "/Matches/{}"
        url = urlmask.format(game_id)
        data = {}
        self.driver.get(url)
        # league and season
        breadcrumb = self.driver.find_elements_by_xpath(
            "//div[@id='breadcrumb-nav']/*[not(contains(@class, 'separator'))]"
        )
        country = breadcrumb[0].text
        league, season = breadcrumb[1].text.split(" - ")
        data["league"] = {v: k for k, v in self._all_leagues().items()}[f"{country} - {league}"]
        data["season"] = season_code(season)
        # match header
        match_header = self.driver.find_element_by_xpath("//div[@id='match-header']")
        score_info = match_header.find_element_by_xpath(".//div[@class='teams-score-info']")
        data["home_team"] = score_info.find_element_by_xpath(
            "./span[contains(@class,'home team')]"
        ).text
        data["result"] = score_info.find_element_by_xpath("./span[contains(@class,'result')]").text
        data["away_team"] = score_info.find_element_by_xpath(
            "./span[contains(@class,'away team')]"
        ).text
        info_blocks = match_header.find_elements_by_xpath(".//div[@class='info-block cleared']")
        for block in info_blocks:
            for desc_list in block.find_elements_by_tag_name("dl"):
                for desc_def in desc_list.find_elements_by_tag_name("dt"):
                    desc_val = desc_def.find_element_by_xpath("./following-sibling::dd")
                    data[desc_def.text] = desc_val.text

        return data

    def read_missing_players(
        self, match_id: Optional[Union[int, List[int]]] = None, force_cache: bool = False
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
            iterator = df_schedule

        match_sheets = []
        for i, game in iterator.iterrows():
            url = urlmask.format(game.game_id)
            filepath = DATA_DIR / filemask.format(game["league"], game["season"], game["game_id"])

            logger.info(
                "[%s/%s] Retrieving game with id=%s", i + 1, len(iterator), game["game_id"]
            )
            reader = self._download_and_save(url, filepath, var=None)

            # extract missing players
            tree = html.parse(reader)
            for node in tree.xpath("//div[@id='missing-players']/div[2]/table/tbody/tr"):
                # extract team IDs from links
                match_sheets.append(
                    {
                        "game_id": game["game_id"],
                        "side": "home",
                        "player_name": node.xpath("./td[contains(@class,'pn')]/a")[0].text,
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
                        "game_id": game["game_id"],
                        "side": "away",
                        "player_name": node.xpath("./td[contains(@class,'pn')]/a")[0].text,
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
        df = pd.DataFrame(match_sheets).set_index(["game_id", "player_id"]).sort_index()
        return df

    def read_events(
        self,
        match_id: Optional[Union[int, List[int]]] = None,
        force_cache: bool = False,
        live: bool = False,
    ) -> pd.DataFrame:
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

        Raises
        ------
        ValueError
            If the given match_id could not be found in the selected seasons.

        Returns
        -------
        pd.DataFrame
        """
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
            iterator = df_schedule

        events = []
        for i, game in iterator.iterrows():
            url = urlmask.format(game["game_id"])
            # get league and season
            logger.info(
                "[%s/%s] Retrieving game with id=%s", i + 1, len(iterator), game["game_id"]
            )
            filepath = self.data_dir / filemask.format(
                game["league"], game["season"], game["game_id"]
            )

            reader = self._download_and_save(
                url,
                filepath,
                var="requirejs.s.contexts._.config.config.params.args.matchCentreData",
                no_cache=live,
            )
            json_data = json.load(reader)
            if json_data is not None and "events" in json_data:
                game_events = pd.DataFrame(json_data["events"])
                game_events["game_id"] = game["game_id"]
                events.append(game_events)
            else:
                logger.warning("No events found for game %s", game["game_id"])

        df = pd.concat(events).pipe(standardize_colnames).set_index(["game_id", "id"]).sort_index()
        df["outcome_type"] = df["outcome_type"].apply(lambda x: x.get("displayName"))
        df["period"] = df["period"].apply(lambda x: x.get("displayName"))
        return df

    @staticmethod
    def _init_webdriver(
        path_to_browser: Optional[Union[str, Path]] = None,
        path_to_addblocker: Optional[Union[str, Path]] = None,
        use_tor: bool = False,
        use_addblocker: bool = False,
    ) -> "uc.Chrome":
        """Start the Selenium driver."""
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument("--headless")
        if path_to_browser is not None:
            chrome_options.add_argument("--binary-location=" + str(path_to_browser))
        if use_addblocker and path_to_addblocker is not None:
            chrome_options.add_argument("--load-extension=" + str(path_to_addblocker))
        if use_tor:
            proxy = "socks5://127.0.0.1:9050"
            resolver_rules = "MAP * 0.0.0.0 , EXCLUDE myproxy"
            chrome_options.add_argument("--proxy-server=" + proxy)
            chrome_options.add_argument("--host-resolver-rules=" + resolver_rules)
        return uc.Chrome(options=chrome_options)

    def _download_and_save(  # noqa: C901
        self,
        url: str,
        filepath: Optional[Path] = None,
        max_age: Optional[Union[int, timedelta]] = None,
        no_cache: bool = False,
        var: Optional[str] = None,
    ) -> IO[bytes]:
        """Download file at url to filepath. Overwrites if filepath exists."""
        # Validate inputs
        if max_age is not None:
            if isinstance(max_age, int):
                _max_age = timedelta(days=max_age)
            elif isinstance(max_age, timedelta):
                _max_age = max_age
            else:
                raise TypeError("max_age must be of type int or datetime.timedelta")
        else:
            _max_age = None

        cache_invalid = False
        # Check if cached file is too old
        if no_cache or self.no_cache:
            cache_invalid = True
        if _max_age is not None and filepath is not None and filepath.exists():
            last_modified = datetime.fromtimestamp(filepath.stat().st_mtime)
            now = datetime.now()
            if (now - last_modified) > _max_age:
                cache_invalid = True

        # Download file
        if cache_invalid or filepath is None or not filepath.exists():
            logger.info("Scraping %s", url)
            self.driver.get(url)
            time.sleep(5 + random.random() * 5)
            if "Incapsula incident ID" in self.driver.page_source:
                raise WebDriverException("Your IP is blocked. Use tor to continue scraping.")

            if var is None:
                response = self.driver.execute_script("return document.body.innerHTML;").encode(
                    "utf-8"
                )
            else:
                try:
                    response = self.driver.execute_script("return " + var)
                except JavascriptException:
                    logger.error("Could not obtain %s for %s", var, url)
                    response = {}
                response = json.dumps(response).encode("utf-8")
            if not self.no_store and filepath is not None:
                filepath.parent.mkdir(parents=True, exist_ok=True)
                with filepath.open(mode="wb") as fh:
                    fh.write(response)
            return io.BytesIO(response)

        # Use cached file
        logger.debug("Retrieving %s from cache", url)
        return filepath.open(mode="rb")

    def _handle_banner(self) -> None:
        try:
            # self.driver.get(WHOSCORED_URL)
            time.sleep(2)
            self.driver.find_element_by_xpath("//button[contains(text(), 'AGREE')]").click()
            time.sleep(2)
        except NoSuchElementException:
            with open("/tmp/error.html", "w") as f:
                f.write(self.driver.page_source)
            raise ElementClickInterceptedException()
