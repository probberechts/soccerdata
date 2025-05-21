"""Scraper for http://www.football-data.co.uk/data.php."""

import itertools
from pathlib import Path
from typing import IO, Callable, Optional, Union

import pandas as pd

from ._common import BaseRequestsReader, make_game_id
from ._config import DATA_DIR, NOCACHE, NOSTORE, TEAMNAME_REPLACEMENTS, logger

MATCH_HISTORY_DATA_DIR = DATA_DIR / "MatchHistory"
MATCH_HISTORY_API = "https://www.football-data.co.uk"


def _parse_csv(raw_data: IO[bytes], lkey: str, skey: str) -> pd.DataFrame:
    logger.info("Parsing league=%s season=%s", lkey, skey)
    if int(skey) >= 2425:
        # Since 2024-25, the CSV files are encoded in UTF-8-SIG
        df_games = pd.read_csv(
            raw_data,
            encoding="UTF-8-SIG",
            on_bad_lines="warn",
        )
    else:
        df_games = pd.read_csv(
            raw_data,
            encoding="latin-1",
            on_bad_lines="warn",
        )
    return df_games


class MatchHistory(BaseRequestsReader):
    """Provides pd.DataFrames from CSV files available at http://www.football-data.co.uk/data.php.

    Data will be downloaded as necessary and cached locally in
    ``~/soccerdata/data/MatchHistory``.

    Parameters
    ----------
    leagues : string or iterable
        IDs of leagues to include.
    seasons : string, int or list
        Seasons to include. Supports multiple formats.
        Examples: '16-17'; 2016; '2016-17'; [14, 15, 16]
    proxy : 'tor' or or dict or list(dict) or callable, optional
        Use a proxy to hide your IP address. Valid options are:
            - "tor": Uses the Tor network. Tor should be running in
              the background on port 9050.
            - str: The address of the proxy server to use.
            - list(str): A list of proxies to choose from. A different proxy will
              be selected from this list after failed requests, allowing rotating
              proxies.
            - callable: A function that returns a valid proxy. This function will
              be called after failed requests, allowing rotating proxies.
    no_cache : bool
        If True, will not use cached data.
    no_store : bool
        If True, will not store downloaded data.
    data_dir : Path, optional
        Path to directory where data will be cached.
    """

    def __init__(
        self,
        leagues: Optional[Union[str, list[str]]] = None,
        seasons: Optional[Union[str, int, list]] = None,
        proxy: Optional[Union[str, list[str], Callable[[], str]]] = None,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = MATCH_HISTORY_DATA_DIR,
    ):
        super().__init__(
            leagues=leagues, proxy=proxy, no_cache=no_cache, no_store=no_store, data_dir=data_dir
        )
        self.seasons = seasons  # type: ignore

    def read_games(self) -> pd.DataFrame:
        """Retrieve game history for the selected leagues and seasons.

        Column names are explained here: http://www.football-data.co.uk/notes.txt

        Returns
        -------
        pd.DataFrame
        """
        urlmask = MATCH_HISTORY_API + "/mmz4281/{}/{}.csv"
        filemask = "{}_{}.csv"
        col_rename = {
            "Div": "league",
            "Date": "date",
            "Time": "time",
            "HomeTeam": "home_team",
            "AwayTeam": "away_team",
            "Referee": "referee",
        }

        df_list = []
        for lkey, skey in itertools.product(self._selected_leagues.values(), self.seasons):
            filepath = self.data_dir / filemask.format(lkey, skey)
            url = urlmask.format(skey, lkey)
            current_season = not self._is_complete(lkey, skey)

            reader = self.get(url, filepath, no_cache=current_season)
            df_games = _parse_csv(reader, lkey, skey).assign(season=skey)

            if "Time" not in df_games.columns:
                df_games["Time"] = "12:00"
            df_games["Time"] = df_games["Time"].fillna("12:00")
            df_list.append(df_games)

        df = (
            pd.concat(df_list, sort=False)
            .rename(columns=col_rename)
            .assign(
                date=lambda x: pd.to_datetime(
                    x["date"] + " " + x["time"], format="mixed", dayfirst=True
                )
            )
            .drop("time", axis=1)
            .pipe(self._translate_league)
            .replace(
                {
                    "home_team": TEAMNAME_REPLACEMENTS,
                    "away_team": TEAMNAME_REPLACEMENTS,
                }
            )
            .dropna(subset=["home_team", "away_team"])
        )

        df = df.loc[:, ~df.columns.str.contains("^Unnamed")]
        df["game"] = df.apply(make_game_id, axis=1)
        df.set_index(["league", "season", "game"], inplace=True)
        df.sort_index(inplace=True)
        return df
