import io
import pprint
import re
import warnings
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import IO, Dict, Iterable, List, Optional, Union

import numpy as np
import pandas as pd
import requests
from dateutil.relativedelta import relativedelta
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from ._config import DATA_DIR, LEAGUE_DICT, logger


class BaseReader:
    """Base class for data readers.

    Parameters
    ----------
    leagues : str or list of str, optional
        The leagues to read. If None, all available leagues are read.
    use_tor : bool
        Whether to use the Tor network to hide your IP.
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
        use_tor: bool = False,
        no_cache: bool = False,
        no_store: bool = False,
        data_dir: Path = DATA_DIR,
    ):
        """Create a new data reader."""
        self.proxies = {}
        if use_tor:
            self.proxies = {
                "http": "socks5h://localhost:9050",
                "https": "socks5h://localhost:9050",
            }
        self._selected_leagues = leagues  # type: ignore
        self.no_cache = no_cache
        self.no_store = no_store
        self.data_dir = data_dir
        if self.no_store:
            logger.info("Caching is disabled")
        else:
            logger.info("Saving cached data to %s", self.data_dir)
            self.data_dir.mkdir(parents=True, exist_ok=True)

    def _download_and_save(
        self,
        url: str,
        filepath: Optional[Path] = None,
        max_age: Optional[Union[int, timedelta]] = None,
        no_cache: bool = False,
    ) -> IO[bytes]:
        """Download data at `url` to `filepath`.

        If filepath does not exist, download file and save to filepath.
        If cache is invalid, download file and save to filepath.
        If no_store is enabled, does not store the downloaded data.
        If no_cache is enabled, overwrites if filepath exists.
        If filepath already exists, read file instead.

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


        Raises
        ------
        TypeError
            If max_age is not an integer or timedelta object.

        Returns
        -------
        io.BufferedIOBase
            File-like object of downloaded data.
        """
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
            headers = {
                "user-agent": UserAgent(verify_ssl=False).random,
            }
            session = requests.Session()
            retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
            session.mount("http://", HTTPAdapter(max_retries=retries))
            response = session.get(url, proxies=self.proxies, headers=headers, stream=True)
            response.raise_for_status()
            if not self.no_store and filepath is not None:
                with filepath.open(mode="wb") as fh:
                    fh.write(response.content)
            return io.BytesIO(response.content)
        # Use cached file
        return filepath.open(mode="rb")

    @classmethod
    def available_leagues(cls) -> List[str]:
        """Return a list of league IDs available for this source."""
        return sorted(cls._all_leagues().keys())

    @classmethod
    def _all_leagues(cls) -> Dict[str, str]:
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
    def _selected_leagues(self) -> Dict[str, str]:
        """Return a dict mapping selected canonical league IDs to source league IDs."""
        return self._leagues_dict

    @_selected_leagues.setter
    def _selected_leagues(self, ids: Optional[Union[str, List[str]]] = None) -> None:
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
                        { pprint.pformat(self.available_leagues()) }
                        """
                    )
                tmp_league_dict[i] = self._all_leagues()[i]
            self._leagues_dict = tmp_league_dict

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
            season_ends = date(datetime.strptime(season[-2:], "%y").year, 7, 1)
        else:
            season_ends = (
                date(
                    datetime.strptime(season[-2:], "%y").year,
                    datetime.strptime(league_dict["season_end"], "%b").month,
                    1,
                )
                + relativedelta(months=1)
            )
        return date.today() >= season_ends

    @property
    def leagues(self) -> List[str]:
        """Return a list of selected leagues."""
        return list(self._leagues_dict.keys())

    @property
    def seasons(self) -> List[str]:
        """Return a list of selected seasons."""
        return self._season_ids

    @seasons.setter
    def seasons(self, seasons: Optional[Union[str, int, Iterable[Union[str, int]]]]) -> None:
        if seasons is None:
            logger.info("No seasons provided. Will retrieve data for the last 5 seasons.")
            year = datetime.today().year
            seasons = range(year, year - 6, -1)
        if isinstance(seasons, str) or isinstance(seasons, int):
            seasons = [seasons]
        self._season_ids = [season_code(s) for s in seasons]


def season_code(season: Union[str, int]) -> str:  # noqa: C901
    """Convert a string or int to a season code like '1718'."""
    season = str(season)
    pat1 = re.compile(r"^[0-9]{4}$")  # 1994 | 9495
    pat2 = re.compile(r"^[0-9]{2}$")  # 94
    pat3 = re.compile(r"^[0-9]{4}-[0-9]{4}$")  # 1994-1995
    pat4 = re.compile(r"^[0-9]{4}/[0-9]{4}$")  # 1994/1995
    pat5 = re.compile(r"^[0-9]{4}-[0-9]{2}$")  # 1994-95
    pat6 = re.compile(r"^[0-9]{2}-[0-9]{2}$")  # 94-95

    if re.match(pat1, season):
        if int(season[2:]) == int(season[:2]) + 1:
            if season == "1920" or season == "2021":
                msg = 'Season id "{}" is ambiguous: interpreting as "{}-{}"'.format(
                    season, season[:2], season[-2:]
                )
                warnings.warn(msg)
            return season  # 9495
        elif season[2:] == "99":
            return "".join([season[2:], "00"])  # 1999
        else:
            return "".join([season[-2:], f"{int(season[-2:]) + 1:02d}"])  # 1994
    elif re.match(pat2, season):
        if season == "99":
            return "".join([season, "00"])  # 99
        else:
            return "".join([season, f"{int(season) + 1:02d}"])  # 94
    elif re.match(pat3, season):
        return "".join([season[2:4], season[-2:]])  # 1994-1995
    elif re.match(pat4, season):
        return "".join([season[2:4], season[-2:]])  # 1994/1995
    elif re.match(pat5, season):
        return "".join([season[2:4], season[-2:]])  # 1994-95
    elif re.match(pat6, season):
        return "".join([season[:2], season[-2:]])  # 94-95
    else:
        return season


def make_game_id(row: pd.Series) -> str:
    """Return a game id based on date, home and away team."""
    game_id = "{} {}-{}".format(
        row["date"].strftime("%Y-%m-%d"),
        row["home_team"],
        row["away_team"],
    )
    return game_id


def standardize_colnames(df: pd.DataFrame, cols: Optional[List[str]] = None) -> pd.DataFrame:
    """Convert DataFrame column names to snake case."""

    def to_snake(name: str) -> str:
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        name = re.sub("__([A-Z])", r"_\1", name)
        name = re.sub("([a-z0-9])([A-Z])", r"\1_\2", name)
        return name.lower().replace("-", "_").replace(" ", "")

    if cols is None:
        cols = list(df.columns)

    return df.rename(columns={c: to_snake(c) for c in cols})
