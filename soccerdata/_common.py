import io
import json
import pprint
import random
import re
import time
import warnings
from abc import ABC, abstractmethod
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import IO, Callable, Optional, Union

import cloudscraper
import numpy as np
import pandas as pd
import requests
import selenium
import undetected_chromedriver as uc
from dateutil.relativedelta import relativedelta
from packaging import version
from selenium.common.exceptions import JavascriptException, WebDriverException

from ._config import DATA_DIR, LEAGUE_DICT, MAXAGE, TEAMNAME_REPLACEMENTS, logger


class SeasonCode(Enum):
    """How to interpret season codes.

    Attributes
    ----------
    SINGLE_YEAR: The season code is a single year, e.g. '2021'.
    MULTI_YEAR: The season code is a range of years, e.g. '2122'.
    """

    SINGLE_YEAR = "single-year"
    MULTI_YEAR = "multi-year"

    @staticmethod
    def from_league(league: str) -> "SeasonCode":
        """Return the default season code for a league.

        Parameters
        ----------
        league : str
            The league to consider.

        Raises
        ------
        ValueError
            If the league is not recognized.

        Returns
        -------
        SeasonCode
            The season code format to use.
        """
        if league not in LEAGUE_DICT:
            raise ValueError(f"Invalid league '{league}'")
        select_league_dict = LEAGUE_DICT[league]
        if "season_code" in select_league_dict:
            return SeasonCode(select_league_dict["season_code"])
        start_month = datetime.strptime(  # noqa: DTZ007
            select_league_dict.get("season_start", "Aug"),
            "%b",
        ).month
        end_month = datetime.strptime(  # noqa: DTZ007
            select_league_dict.get("season_end", "May"),
            "%b",
        ).month
        return SeasonCode.MULTI_YEAR if (end_month - start_month) < 0 else SeasonCode.SINGLE_YEAR

    @staticmethod
    def from_leagues(leagues: list[str]) -> "SeasonCode":
        """Determine the season code to use for a set of leagues.

        If the given leagues have different default season codes,
        the multi-year format is usded.

        Parameters
        ----------
        leagues : list of str
            The leagues to consider.

        Returns
        -------
        SeasonCode
            The season code format to use.
        """
        season_codes = {SeasonCode.from_league(league) for league in leagues}
        if len(season_codes) == 1:
            return season_codes.pop()
        warnings.warn(
            "The leagues have different default season codes. Using multi-year season codes.",
            stacklevel=2,
        )
        return SeasonCode.MULTI_YEAR

    def parse(self, season: Union[str, int]) -> str:  # noqa: C901
        """Convert a string or int to a standard season format."""
        season = str(season)
        patterns = [
            (
                re.compile(r"^[0-9]{4}$"),  # 1994 | 9495
                lambda s: process_four_digit_year(s),
            ),
            (
                re.compile(r"^[0-9]{2}$"),  # 94
                lambda s: process_two_digit_year(s),
            ),
            (
                re.compile(r"^[0-9]{4}-[0-9]{4}$"),  # 1994-1995
                lambda s: process_full_year_range(s),
            ),
            (
                re.compile(r"^[0-9]{4}/[0-9]{4}$"),  # 1994/1995
                lambda s: process_full_year_range(s.replace("/", "-")),
            ),
            (
                re.compile(r"^[0-9]{4}-[0-9]{2}$"),  # 1994-95
                lambda s: process_partial_year_range(s),
            ),
            (
                re.compile(r"^[0-9]{2}-[0-9]{2}$"),  # 94-95
                lambda s: process_short_year_range(s),
            ),
            (
                re.compile(r"^[0-9]{2}/[0-9]{2}$"),  # 94/95
                lambda s: process_short_year_range(s.replace("/", "-")),
            ),
        ]

        current_year = datetime.now(tz=timezone.utc).year

        def process_four_digit_year(season: str) -> str:
            """Process a 4-digit string like '1994' or '9495'."""
            if self == SeasonCode.MULTI_YEAR:
                if int(season[2:]) == int(season[:2]) + 1:
                    if season == "2021":
                        msg = (
                            f'Season id "{season}" is ambiguous: '
                            f'interpreting as "{season[:2]}-{season[-2:]}"'
                        )
                        warnings.warn(msg, stacklevel=1)
                    return season
                if season[2:] == "99":
                    return "9900"
                return season[-2:] + f"{int(season[-2:]) + 1:02d}"
            if season == "1920":
                return "1919"
            if season == "2021":
                return "2020"
            if season[:2] == "19" or season[:2] == "20":
                return season
            if int(season) <= current_year:
                return "20" + season[:2]
            return "19" + season[:2]

        def process_two_digit_year(season: str) -> str:
            """Process a 2-digit string like '94'."""
            if self == SeasonCode.MULTI_YEAR:
                if season == "99":
                    return "9900"
                return season + f"{int(season) + 1:02d}"
            if int("20" + season) <= current_year:
                return "20" + season
            return "19" + season

        def process_full_year_range(season: str) -> str:
            """Process a range of 4-digit strings like '1994-1995'."""
            if self == SeasonCode.MULTI_YEAR:
                return season[2:4] + season[-2:]
            return season[:4]

        def process_partial_year_range(season: str) -> str:
            """Process a range of 4-digit and 2-digit string like '1994-95'."""
            if self == SeasonCode.MULTI_YEAR:
                return season[2:4] + season[-2:]
            return season[:4]

        def process_short_year_range(season: str) -> str:
            """Process a range of 2-digit strings like '94-95'."""
            if self == SeasonCode.MULTI_YEAR:
                return season[:2] + season[-2:]
            if int("20" + season[:2]) <= current_year:
                return "20" + season[:2]
            return "19" + season[:2]

        for pattern, action in patterns:
            if pattern.match(season):
                return action(season)

        raise ValueError(f"Unrecognized season code: '{season}'")


class BaseReader(ABC):
    """Base class for data readers.

    Parameters
    ----------
    leagues : str or list of str, optional
        The leagues to read. If None, all available leagues are read.
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
        leagues: Optional[Union[str, list[str]]] = None,
        proxy: Optional[
            Union[str, dict[str, str], list[dict[str, str]], Callable[[], dict[str, str]]]
        ] = None,
        no_cache: bool = False,
        no_store: bool = False,
        data_dir: Path = DATA_DIR,
    ):
        """Create a new data reader."""
        if isinstance(proxy, str) and proxy.lower() == "tor":
            self.proxy = lambda: {
                "http": "socks5://127.0.0.1:9050",
                "https": "socks5://127.0.0.1:9050",
            }
        elif isinstance(proxy, dict):
            self.proxy = lambda: proxy
        elif isinstance(proxy, list):
            self.proxy = lambda: random.choice(proxy)
        elif callable(proxy):
            self.proxy = proxy
        else:
            self.proxy = dict

        self._selected_leagues = leagues  # type: ignore
        self.no_cache = no_cache
        self.no_store = no_store
        self.data_dir = data_dir
        self.rate_limit = 0
        self.max_delay = 0
        if self.no_store:
            logger.info("Caching is disabled")
        else:
            logger.info("Saving cached data to %s", self.data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)

    def get(
        self,
        url: str,
        filepath: Optional[Path] = None,
        max_age: Optional[Union[int, timedelta]] = MAXAGE,
        no_cache: bool = False,
        var: Optional[Union[str, Iterable[str]]] = None,
    ) -> IO[bytes]:
        """Load data from `url`.

        By default, the source of `url` is downloaded and saved to `filepath`.
        If `filepath` exists, the `url` is not visited and the cached data is
        returned.

        Parameters
        ----------
        url : str
            URL to download.
        filepath : Path, optional
            Path to save downloaded file. If None, downloaded data is not cached.
        max_age : int for age in days, or timedelta object
            The max. age of locally cached file before re-download.
        no_cache : bool
            If True, will not use cached data. Overrides the class property.
        var : str or list of str, optional
            Return a JavaScript variable instead of the page source.

        Raises
        ------
        TypeError
            If max_age is not an integer or timedelta object.

        Returns
        -------
        io.BufferedIOBase
            File-like object of downloaded data.
        """
        is_cached = self._is_cached(filepath, max_age)
        if no_cache or self.no_cache or not is_cached:
            logger.debug("Scraping %s", url)
            return self._download_and_save(url, filepath, var)
        logger.debug("Retrieving %s from cache", url)
        if filepath is None:
            raise ValueError("No filepath provided for cached data.")
        return filepath.open(mode="rb")

    def _is_cached(
        self,
        filepath: Optional[Path] = None,
        max_age: Optional[Union[int, timedelta]] = None,
    ) -> bool:
        """Check if `filepath` contains valid cached data.

        Parameters
        ----------
        filepath : Path, optional
            Path where file should be cached. If None, return False.
        max_age : int for age in days, or timedelta object
            The max. age of locally cached file.

        Raises
        ------
        TypeError
            If max_age is not an integer or timedelta object.

        Returns
        -------
        bool
            True in case of a cache hit, otherwise False.
        """
        # Validate inputs
        if max_age is not None:
            if isinstance(max_age, int):
                _max_age = timedelta(days=max_age)
            elif isinstance(max_age, timedelta):
                _max_age = max_age
            else:
                raise TypeError("'max_age' must be of type int or datetime.timedelta")
        else:
            _max_age = None

        cache_invalid = False
        # Check if cached file is too old
        if _max_age is not None and filepath is not None and filepath.exists():
            last_modified = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc)
            now = datetime.now(timezone.utc)
            if (now - last_modified) > _max_age:
                cache_invalid = True

        return not cache_invalid and filepath is not None and filepath.exists()

    @abstractmethod
    def _download_and_save(
        self,
        url: str,
        filepath: Optional[Path] = None,
        var: Optional[Union[str, Iterable[str]]] = None,
    ) -> IO[bytes]:
        """Download data at `url` to `filepath`.

        Parameters
        ----------
        url : str
            URL to download.
        filepath : Path, optional
            Path to save downloaded file. If None, downloaded data is not cached.
        var : str or list of str, optional
            Return a JavaScript variable instead of the page source.

        Returns
        -------
        io.BufferedIOBase
            File-like object of downloaded data.
        """

    @classmethod
    def available_leagues(cls) -> list[str]:
        """Return a list of league IDs available for this source."""
        return sorted(cls._all_leagues().keys())

    @classmethod
    def _all_leagues(cls) -> dict[str, str]:
        """Return a dict mapping all canonical league IDs to source league IDs."""
        if not hasattr(cls, "_all_leagues_dict"):
            cls._all_leagues_dict = {  # type: ignore
                k: v[cls.__name__] for k, v in LEAGUE_DICT.items() if cls.__name__ in v
            }
        return cls._all_leagues_dict  # type: ignore

    @classmethod
    def _translate_league(cls, df: pd.DataFrame, col: str = "league") -> pd.DataFrame:
        """Map source league ID to canonical ID."""
        flip = {v: k for k, v in cls._all_leagues().items()}
        mask = ~df[col].isin(flip)
        df.loc[mask, col] = np.nan
        df[col] = df[col].replace(flip)
        return df

    @property
    def _selected_leagues(self) -> dict[str, str]:
        """Return a dict mapping selected canonical league IDs to source league IDs."""
        return self._leagues_dict

    @_selected_leagues.setter
    def _selected_leagues(self, ids: Optional[Union[str, list[str]]] = None) -> None:
        if ids is None:
            self._leagues_dict = self._all_leagues()
        else:
            if len(ids) == 0:
                raise ValueError("Empty iterable not allowed for 'leagues'")
            if isinstance(ids, str):
                ids = [ids]
            tmp_league_dict = {}
            for i in ids:
                if i not in self._all_leagues():
                    raise ValueError(
                        f"""
                        Invalid league '{i}'. Valid leagues are:
                        {pprint.pformat(self.available_leagues())}
                        """
                    )
                tmp_league_dict[i] = self._all_leagues()[i]
            self._leagues_dict = tmp_league_dict

    @property
    def _season_code(self) -> SeasonCode:
        return SeasonCode.from_leagues(self.leagues)

    def _is_complete(self, league: str, season: str) -> bool:
        """Check if a season is complete."""
        if league in LEAGUE_DICT:
            league_dict = LEAGUE_DICT[league]
        else:
            flip = {v: k for k, v in self._all_leagues().items()}
            if league in flip:
                league_dict = LEAGUE_DICT[flip[league]]
            else:
                raise ValueError(f"Invalid league '{league}'")
        if "season_end" not in league_dict:
            season_ends = datetime(
                datetime.strptime(season[-2:], "%y").year,  # noqa: DTZ007
                7,
                1,
                tzinfo=timezone.utc,
            )
        else:
            season_ends = datetime(
                datetime.strptime(season[-2:], "%y").year,  # noqa: DTZ007
                datetime.strptime(  # noqa: DTZ007
                    league_dict["season_end"], "%b"
                ).month,
                1,
                tzinfo=timezone.utc,
            ) + relativedelta(months=1)
        return datetime.now(tz=timezone.utc) >= season_ends

    @property
    def leagues(self) -> list[str]:
        """Return a list of selected leagues."""
        return list(self._leagues_dict.keys())

    @property
    def seasons(self) -> list[str]:
        """Return a list of selected seasons."""
        return self._season_ids

    @seasons.setter
    def seasons(self, seasons: Optional[Union[str, int, Iterable[Union[str, int]]]]) -> None:
        if seasons is None:
            logger.info("No seasons provided. Will retrieve data for the last 5 seasons.")
            year = datetime.now(tz=timezone.utc).year
            seasons = [f"{y - 1}-{y}" for y in range(year, year - 6, -1)]
        if isinstance(seasons, (str, int)):
            seasons = [seasons]
        self._season_ids = [self._season_code.parse(s) for s in seasons]


class BaseRequestsReader(BaseReader):
    """Base class for readers that use the Python requests module."""

    def __init__(
        self,
        leagues: Optional[Union[str, list[str]]] = None,
        proxy: Optional[
            Union[str, dict[str, str], list[dict[str, str]], Callable[[], dict[str, str]]]
        ] = None,
        no_cache: bool = False,
        no_store: bool = False,
        data_dir: Path = DATA_DIR,
    ):
        """Initialize the reader."""
        super().__init__(
            no_cache=no_cache,
            no_store=no_store,
            leagues=leagues,
            proxy=proxy,
            data_dir=data_dir,
        )

        self._session = self._init_session()

    def _init_session(self) -> requests.Session:
        session = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "linux", "mobile": False}
        )
        session.proxies.update(self.proxy())
        return session

    def _download_and_save(
        self,
        url: str,
        filepath: Optional[Path] = None,
        var: Optional[Union[str, Iterable[str]]] = None,
    ) -> IO[bytes]:
        """Download file at url to filepath. Overwrites if filepath exists."""
        for i in range(5):
            try:
                response = self._session.get(url, stream=True)
                time.sleep(self.rate_limit + random.random() * self.max_delay)
                response.raise_for_status()
                if var is not None:
                    if isinstance(var, str):
                        var = [var]
                    var_names = "|".join(var)
                    template_understat = rb"(%b)+[\s\t]*=[\s\t]*JSON\.parse\('(.*)'\)"
                    pattern_understat = template_understat % bytes(var_names, encoding="utf-8")
                    results = re.findall(pattern_understat, response.content)
                    data = {
                        key.decode("unicode_escape"): json.loads(value.decode("unicode_escape"))
                        for key, value in results
                    }
                    payload = json.dumps(data).encode("utf-8")
                else:
                    payload = response.content
                if not self.no_store and filepath is not None:
                    with filepath.open(mode="wb") as fh:
                        fh.write(payload)
                return io.BytesIO(payload)
            except Exception:
                logger.exception(
                    "Error while scraping %s. Retrying... (attempt %d of 5).",
                    url,
                    i + 1,
                )
                self._session = self._init_session()
                continue

        raise ConnectionError(f"Could not download {url}.")


class BaseSeleniumReader(BaseReader):
    """Base class for readers that use Selenium."""

    def __init__(
        self,
        leagues: Optional[Union[str, list[str]]] = None,
        proxy: Optional[
            Union[str, dict[str, str], list[dict[str, str]], Callable[[], dict[str, str]]]
        ] = None,
        no_cache: bool = False,
        no_store: bool = False,
        data_dir: Path = DATA_DIR,
        path_to_browser: Optional[Path] = None,
        headless: bool = True,
    ):
        """Initialize the reader."""
        super().__init__(
            no_cache=no_cache,
            no_store=no_store,
            leagues=leagues,
            proxy=proxy,
            data_dir=data_dir,
        )
        self.path_to_browser = path_to_browser
        self.headless = headless

        try:
            self._driver = self._init_webdriver()
        except WebDriverException as e:
            logger.error(
                """
                The ChromeDriver was unable to initiate/spawn a new
                WebBrowser. You will not be able to scrape new data.
                %s
                """,
                e,
            )

    def _init_webdriver(self) -> "uc.Chrome":
        """Start the Selenium driver."""
        # Quit existing driver
        if hasattr(self, "_driver"):
            self._driver.quit()
        # Start a new driver
        chrome_options = uc.ChromeOptions()
        if self.headless:
            print("Starting ChromeDriver in headless mode.", selenium.__version__)
            if version.parse(selenium.__version__) >= version.parse("4.13.0"):
                raise ValueError(
                    "Headless mode is not supported for Selenium 4.13.0 and above. "
                    "Please downgrade to a lower version of Selenium or set "
                    "'headless=False'."
                )
            chrome_options.add_argument("--headless")
        else:
            chrome_options.headless = False
        if self.path_to_browser is not None:
            chrome_options.add_argument("--binary-location=" + str(self.path_to_browser))
        proxy = self.proxy()
        if len(proxy):
            proxy_str = ";".join(f"{prot}={url}" for prot, url in proxy.items())
            resolver_rules = "MAP * ~NOTFOUND , EXCLUDE 127.0.0.1"
            chrome_options.add_argument("--proxy-server=" + proxy_str)
            chrome_options.add_argument("--host-resolver-rules=" + resolver_rules)
        return uc.Chrome(options=chrome_options)

    def _download_and_save(
        self,
        url: str,
        filepath: Optional[Path] = None,
        var: Optional[Union[str, Iterable[str]]] = None,
    ) -> IO[bytes]:
        """Download file at url to filepath. Overwrites if filepath exists."""
        for i in range(5):
            try:
                self._driver.get(url)
                time.sleep(self.rate_limit + random.random() * self.max_delay)
                if "Incapsula incident ID" in self._driver.page_source:
                    raise WebDriverException(
                        "Your IP is blocked. Use tor or a proxy to continue scraping."
                    )
                if var is None:
                    response = self._driver.execute_script(
                        "return document.body.innerHTML;"
                    ).encode("utf-8")
                    if response == b"":
                        raise Exception("Empty response.")
                else:
                    if not isinstance(var, str):
                        raise NotImplementedError("Only implemented for single variables.")
                    try:
                        response = json.dumps(self._driver.execute_script("return " + var)).encode(
                            "utf-8"
                        )
                    except JavascriptException:
                        response = json.dumps(None).encode("utf-8")
                if not self.no_store and filepath is not None:
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    with filepath.open(mode="wb") as fh:
                        fh.write(response)
                return io.BytesIO(response)
            except Exception:
                logger.exception(
                    "Error while scraping %s. Retrying in %d seconds... (attempt %d of 5).",
                    url,
                    i * 10,
                    i + 1,
                )
                time.sleep(i * 10)
                self._driver = self._init_webdriver()
                continue

        raise ConnectionError(f"Could not download {url}.")


def make_game_id(row: pd.Series) -> str:
    """Return a game id based on date, home and away team."""
    if pd.isnull(row["date"]):
        game_id = "{}-{}".format(
            row["home_team"],
            row["away_team"],
        )
    else:
        game_id = "{} {}-{}".format(
            row["date"].strftime("%Y-%m-%d"),
            row["home_team"],
            row["away_team"],
        )
    return game_id


def add_alt_team_names(team: Union[str, list[str]]) -> set[str]:
    """Add a set of alternative team names for a standardized team name.

    If a standardized team name is given, add the set of alternative
    names used by the data sources. If a non-standardized name is given,
    a set only containing the given name is returned.

    Parameters
    ----------
    team : str or list of str
        The team name(s) to consider.

    Returns
    -------
    set of str
        A set contraining the given team name(s) and alternative names.
    """
    teams = [team] if isinstance(team, str) else team

    alt_teams = set()
    for team in teams:
        for alt_name, norm_name in TEAMNAME_REPLACEMENTS.items():
            if norm_name == team:
                alt_teams.add(alt_name)
        alt_teams.add(team)
    return alt_teams


def add_standardized_team_name(team: Union[str, list[str]]) -> set[str]:
    """Add the standardized team name for a non-standardized team name.

    If a non-standardized team name is given, add the standardized
    name. If a standardized name is given, a set only containing the given
    name is returned.

    Parameters
    ----------
    team : str or list of str
        The team name(s) to consider.

    Returns
    -------
    set of str
        A set contraining the given team name(s) and standardized names.
    """
    teams = [team] if isinstance(team, str) else team
    std_teams = set()
    for team in teams:
        for alt_name, norm_name in TEAMNAME_REPLACEMENTS.items():
            if alt_name == team:
                std_teams.add(norm_name)
        std_teams.add(team)
    return std_teams


def standardize_colnames(df: pd.DataFrame, cols: Optional[list[str]] = None) -> pd.DataFrame:
    """Convert DataFrame column names to snake case."""

    def to_snake(name: str) -> str:
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        name = re.sub("__([A-Z])", r"_\1", name)
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
        return name.lower().replace("-", "_").replace(" ", "")

    if df.columns.nlevels > 1 and cols is None:
        # only standardize the first level
        new_df = df.copy()
        new_cols = [to_snake(c) for c in df.columns.levels[0]]
        new_df.columns = new_df.columns.set_levels(new_cols, level=0)
        return new_df

    if cols is None:
        cols = list(df.columns)

    return df.rename(columns={c: to_snake(c) for c in cols})


def get_proxy() -> dict[str, str]:
    """Return a public proxy."""
    # list of free proxy apis
    # protocols: http, https, socks4 and socks5
    list_of_proxy_content = [
        "https://proxylist.geonode.com/api/proxy-list?sort_by=lastChecked&sort_type=desc",
    ]

    # extracting json data from this list of proxies
    full_proxy_list = []
    for proxy_url in list_of_proxy_content:
        proxy_json = json.loads(requests.get(proxy_url).text)["data"]
        full_proxy_list.extend(proxy_json)

        if not full_proxy_list:
            logger.info("There are currently no proxies available. Exiting...")
            return {}
        logger.info(f"Found {len(full_proxy_list)} proxy servers. Checking...")

    # creating proxy dict
    final_proxy_list = []
    for proxy in full_proxy_list:
        protocol = proxy["protocols"][0]
        ip_ = proxy["ip"]
        port = proxy["port"]

        proxy = {
            "https": protocol + "://" + ip_ + ":" + port,
            "http": protocol + "://" + ip_ + ":" + port,
        }

        final_proxy_list.append(proxy)

    # trying proxy
    for proxy in final_proxy_list:
        if check_proxy(proxy):
            return proxy

    logger.info("There are currently no proxies available. Exiting...")
    return {}


def check_proxy(proxy: dict) -> bool:
    """Check if proxy is working."""
    try:
        r0 = requests.get("https://ipinfo.io/json", proxies=proxy, timeout=15)
        return r0.status_code == 200
    except Exception as error:
        logger.error(f"BAD PROXY: Reason: {error!s}\n")
        return False
