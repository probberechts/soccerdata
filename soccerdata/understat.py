"""Scraper for understat.com."""

import itertools
import json
from collections.abc import Iterable
from html import unescape
from pathlib import Path
from typing import Any, Callable, Optional, Union

import pandas as pd

from ._common import BaseRequestsReader, make_game_id
from ._config import DATA_DIR, NOCACHE, NOSTORE, TEAMNAME_REPLACEMENTS

UNDERSTAT_DATADIR = DATA_DIR / "Understat"
UNDERSTAT_URL = "https://understat.com"

SHOT_SITUATIONS = {
    "OpenPlay": "Open Play",
    "FromCorner": "From Corner",
    "SetPiece": "Set Piece",
    "DirectFreekick": "Direct Freekick",
}

SHOT_BODY_PARTS = {
    "RightFoot": "Right Foot",
    "LeftFoot": "Left Foot",
    "OtherBodyParts": "Other",
}

SHOT_RESULTS = {
    "Goal": "Goal",
    "OwnGoal": "Own Goal",
    "BlockedShot": "Blocked Shot",
    "SavedShot": "Saved Shot",
    "MissedShots": "Missed Shot",
    "ShotOnPost": "Shot On Post",
}


class Understat(BaseRequestsReader):
    """Provides pd.DataFrames from data at https://understat.com.

    Data will be downloaded as necessary and cached locally in
    ``~/soccerdata/data/Understat``.

    Parameters
    ----------
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
        seasons: Optional[Union[str, int, Iterable[Union[str, int]]]] = None,
        proxy: Optional[
            Union[str, dict[str, str], list[dict[str, str]], Callable[[], dict[str, str]]]
        ] = None,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = UNDERSTAT_DATADIR,
    ):
        """Initialize a new Understat reader."""
        super().__init__(
            leagues=leagues,
            proxy=proxy,
            no_cache=no_cache,
            no_store=no_store,
            data_dir=data_dir,
        )
        self.seasons = seasons  # type: ignore

    def read_leagues(self) -> pd.DataFrame:
        """Retrieve the selected leagues from the datasource.

        Returns
        -------
        pd.DataFrame
        """
        data = self._read_leagues()

        leagues = {}

        league_data = data["statData"]
        for league_stat in league_data:
            league_id = league_stat["league_id"]
            if league_id not in leagues:
                league = league_stat["league"]
                league_slug = league.replace(" ", "_")
                leagues[league_id] = {
                    "league_id": league_id,
                    "league": league,
                    "url": UNDERSTAT_URL + f"/league/{league_slug}",
                }

        index = "league"
        if len(leagues) == 0:
            return pd.DataFrame(index=index)

        df = (
            pd.DataFrame.from_records(list(leagues.values()))
            .pipe(self._translate_league)
            .set_index(index)
            .sort_index()
            .convert_dtypes()
        )

        valid_leagues = [league for league in self.leagues if league in df.index]
        return df.loc[valid_leagues]

    def read_seasons(self) -> pd.DataFrame:
        """Retrieve the selected seasons from the datasource.

        Returns
        -------
        pd.DataFrame
        """
        data = self._read_leagues()

        seasons = {}

        league_data = data["statData"]
        for league_stat in league_data:
            league_id = league_stat["league_id"]
            year = int(league_stat["year"])
            month = int(league_stat["month"])
            season_id = year if month >= 7 else year - 1
            key = (league_id, season_id)
            if key not in seasons:
                league = league_stat["league"]
                league_slug = league.replace(" ", "_")
                season = f"{season_id}/{season_id + 1}"
                seasons[key] = {
                    "league_id": league_id,
                    "league": league,
                    "season_id": season_id,
                    "season": self._season_code.parse(season),
                    "url": UNDERSTAT_URL + f"/league/{league_slug}/{season_id}",
                }

        index = ["league", "season"]
        if len(seasons) == 0:
            return pd.DataFrame(index=index)

        df = (
            pd.DataFrame.from_records(list(seasons.values()))
            .pipe(self._translate_league)
            .set_index(index)
            .sort_index()
            .convert_dtypes()
        )

        all_seasons = itertools.product(self.leagues, self.seasons)
        valid_seasons = [season for season in all_seasons if season in df.index]
        return df.loc[valid_seasons]

    def read_schedule(
        self, include_matches_without_data: bool = True, force_cache: bool = False
    ) -> pd.DataFrame:
        """Retrieve the matches for the selected leagues and seasons.

        Parameters
        ----------
        include_matches_without_data : bool
            By default matches with and without data are returned.
            If False, will only return matches with data.

        force_cache : bool
             By default no cached data is used for the current season.
             If True, will force the use of cached data anyway.

        Returns
        -------
        pd.DataFrame
        """
        df_seasons = self.read_seasons()

        matches = []

        for (league, season), league_season in df_seasons.iterrows():
            league_id = league_season["league_id"]
            season_id = league_season["season_id"]
            url = league_season["url"]

            is_current_season = not self._is_complete(league, season)
            no_cache = is_current_season and not force_cache

            data = self._read_league_season(url, league_id, season_id, no_cache)

            matches_data = data["datesData"]
            for match in matches_data:
                match_id = _as_int(match["id"])
                has_home_xg = match["xG"]["h"] not in ("0", None)
                has_away_xg = match["xG"]["a"] not in ("0", None)
                has_data = has_home_xg or has_away_xg
                matches.append(
                    {
                        "league_id": league_id,
                        "league": league,
                        "season_id": season_id,
                        "season": season,
                        "game_id": match_id,
                        "date": match["datetime"],
                        "home_team_id": _as_int(match["h"]["id"]),
                        "away_team_id": _as_int(match["a"]["id"]),
                        "home_team": _as_str(match["h"]["title"]),
                        "away_team": _as_str(match["a"]["title"]),
                        "away_team_code": match["a"]["short_title"],
                        "home_team_code": match["h"]["short_title"],
                        "home_goals": _as_int(match["goals"]["h"]),
                        "away_goals": _as_int(match["goals"]["a"]),
                        "home_xg": _as_float(match["xG"]["h"]),
                        "away_xg": _as_float(match["xG"]["a"]),
                        "is_result": _as_bool(match["isResult"]),
                        "has_data": has_data,
                        "url": UNDERSTAT_URL + f"/match/{match_id}",
                    }
                )

        index = ["league", "season", "game"]
        if len(matches) == 0:
            return pd.DataFrame(index=index)

        df = (
            pd.DataFrame.from_records(matches)
            .assign(date=lambda g: pd.to_datetime(g["date"], format="%Y-%m-%d %H:%M:%S"))
            .replace(
                {
                    "home_team": TEAMNAME_REPLACEMENTS,
                    "away_team": TEAMNAME_REPLACEMENTS,
                }
            )
            .assign(game=lambda g: g.apply(make_game_id, axis=1))
            .set_index(index)
            .sort_index()
            .convert_dtypes()
        )

        if not include_matches_without_data:
            df = df[df["has_data"]]

        return df

    def read_team_match_stats(self, force_cache: bool = False) -> pd.DataFrame:
        """Retrieve the team match stats for the selected leagues and seasons.

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

        stats = {}

        for (league, season), league_season in df_seasons.iterrows():
            league_id = league_season["league_id"]
            season_id = league_season["season_id"]
            url = league_season["url"]

            is_current_season = not self._is_complete(league, season)
            no_cache = is_current_season and not force_cache

            data = self._read_league_season(url, league_id, season_id, no_cache)

            schedule = {}
            matches = {}

            matches_data = data["datesData"]
            for match in matches_data:
                match_id = _as_int(match["id"])
                match_date = match["datetime"]
                schedule[match_id] = {
                    "league_id": league_id,
                    "league": league,
                    "season_id": season_id,
                    "season": season,
                    "game_id": match_id,
                    "date": match["datetime"],
                    "home_team_id": _as_int(match["h"]["id"]),
                    "away_team_id": _as_int(match["a"]["id"]),
                    "home_team": _as_str(match["h"]["title"]),
                    "away_team": _as_str(match["a"]["title"]),
                    "away_team_code": _as_str(match["a"]["short_title"]),
                    "home_team_code": _as_str(match["h"]["short_title"]),
                }
                for side in ("h", "a"):
                    team_id = _as_int(match[side]["id"])
                    matches[(match_date, team_id)] = match_id

            teams_data = data["teamsData"]
            for team in teams_data.values():
                team_id = _as_int(team["id"])
                for match in team["history"]:
                    match_date = match["date"]
                    match_id = matches[(match_date, team_id)]
                    team_side = match["h_a"]
                    prefix = "home" if team_side == "h" else "away"

                    if match_id not in stats:
                        stats[match_id] = schedule[match_id]

                    ppda = match["ppda"]
                    team_ppda = (ppda["att"] / ppda["def"]) if ppda["def"] != 0 else pd.NA

                    stats[match_id].update(
                        {
                            f"{prefix}_points": _as_int(match["pts"]),
                            f"{prefix}_expected_points": _as_float(match["xpts"]),
                            f"{prefix}_goals": _as_int(match["scored"]),
                            f"{prefix}_xg": _as_float(match["xG"]),
                            f"{prefix}_np_xg": _as_float(match["npxG"]),
                            f"{prefix}_np_xg_difference": _as_float(match["npxGD"]),
                            f"{prefix}_ppda": _as_float(team_ppda),
                            f"{prefix}_deep_completions": _as_int(match["deep"]),
                        }
                    )

        index = ["league", "season", "game"]
        if len(stats) == 0:
            return pd.DataFrame(index=index)

        return (
            pd.DataFrame.from_records(list(stats.values()))
            .assign(date=lambda g: pd.to_datetime(g["date"], format="%Y-%m-%d %H:%M:%S"))
            .replace(
                {
                    "home_team": TEAMNAME_REPLACEMENTS,
                    "away_team": TEAMNAME_REPLACEMENTS,
                }
            )
            .assign(game=lambda g: g.apply(make_game_id, axis=1))
            .set_index(index)
            .sort_index()
            .convert_dtypes()
        )

    def read_player_season_stats(self, force_cache: bool = False) -> pd.DataFrame:
        """Retrieve the player season stats for the selected leagues and seasons.

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

        stats = []
        for (league, season), league_season in df_seasons.iterrows():
            league_id = league_season["league_id"]
            season_id = league_season["season_id"]
            url = league_season["url"]

            is_current_season = not self._is_complete(league, season)
            no_cache = is_current_season and not force_cache

            data = self._read_league_season(url, league_id, season_id, no_cache)

            teams_data = data["teamsData"]
            team_mapping = {}
            for team in teams_data.values():
                team_name = _as_str(team["title"])
                team_id = _as_int(team["id"])
                team_mapping[team_name] = team_id

            players_data = data["playersData"]
            for player in players_data:
                player_team_name = player["team_title"]
                if "," in player_team_name:  # pick first team if multiple teams are listed
                    player_team_name = player_team_name.split(",")[0]
                player_team_name = _as_str(player_team_name)
                player_team_id = team_mapping[player_team_name]
                stats.append(
                    {
                        "league": league,
                        "league_id": league_id,
                        "season": season,
                        "season_id": season_id,
                        "team": player_team_name,
                        "team_id": player_team_id,
                        "player": _as_str(player["player_name"]),
                        "player_id": _as_int(player["id"]),
                        "position": _as_str(player["position"]),
                        "matches": _as_int(player["games"]),
                        "minutes": _as_int(player["time"]),
                        "goals": _as_int(player["goals"]),
                        "xg": _as_float(player["xG"]),
                        "np_goals": _as_int(player["npg"]),
                        "np_xg": _as_float(player["npxG"]),
                        "assists": _as_int(player["assists"]),
                        "xa": _as_float(player["xA"]),
                        "shots": _as_int(player["shots"]),
                        "key_passes": _as_int(player["key_passes"]),
                        "yellow_cards": _as_int(player["yellow_cards"]),
                        "red_cards": _as_int(player["red_cards"]),
                        "xg_chain": _as_float(player["xGChain"]),
                        "xg_buildup": _as_float(player["xGBuildup"]),
                    }
                )

        index = ["league", "season", "team", "player"]
        if len(stats) == 0:
            return pd.DataFrame(index=index)

        return (
            pd.DataFrame.from_records(stats)
            .replace(
                {
                    "team": TEAMNAME_REPLACEMENTS,
                }
            )
            .set_index(index)
            .sort_index()
            .convert_dtypes()
        )

    def read_player_match_stats(
        self, match_id: Optional[Union[int, list[int]]] = None
    ) -> pd.DataFrame:
        """Retrieve the player match stats for the selected leagues and seasons.

        Parameters
        ----------
        match_id : int or list of int, optional
            Retrieve the player match stats for a specific match.

        Raises
        ------
        ValueError
            If the given match_id could not be found in the selected seasons.

        Returns
        -------
        pd.DataFrame
        """
        df_schedule = self.read_schedule(include_matches_without_data=False)
        df_results = self._select_matches(df_schedule, match_id)

        stats = []
        for (league, season, game), league_season_game in df_results.iterrows():
            league_id = league_season_game["league_id"]
            season_id = league_season_game["season_id"]
            game_id = league_season_game["game_id"]
            url = league_season_game["url"]

            data = self._read_match(url, game_id)
            if data is None:
                continue

            match_info = data["match_info"]
            team_id_to_name = {
                match_info[side]: _as_str(match_info[f"team_{side}"]) for side in ("h", "a")
            }

            players_data = data["rostersData"]
            for team_players in players_data.values():
                for player in team_players.values():
                    team_id = player["team_id"]
                    team = team_id_to_name[team_id]
                    stats.append(
                        {
                            "league": league,
                            "league_id": league_id,
                            "season": season,
                            "season_id": season_id,
                            "game_id": game_id,
                            "game": game,
                            "team": team,
                            "team_id": _as_int(team_id),
                            "player": _as_str(player["player"]),
                            "player_id": _as_int(player["player_id"]),
                            "position": _as_str(player["position"]),
                            "position_id": _as_int(player["positionOrder"]),
                            "minutes": _as_int(player["time"]),
                            "goals": _as_int(player["goals"]),
                            "own_goals": _as_int(player["own_goals"]),
                            "shots": _as_int(player["shots"]),
                            "xg": _as_float(player["xG"]),
                            "xg_chain": _as_float(player["xGChain"]),
                            "xg_buildup": _as_float(player["xGBuildup"]),
                            "assists": _as_int(player["assists"]),
                            "xa": _as_float(player["xA"]),
                            "key_passes": _as_int(player["key_passes"]),
                            "yellow_cards": _as_int(player["yellow_card"]),
                            "red_cards": _as_int(player["red_card"]),
                        }
                    )

        index = ["league", "season", "game", "team", "player"]
        if len(stats) == 0:
            return pd.DataFrame(index=index)

        return (
            pd.DataFrame.from_records(stats)
            .replace(
                {
                    "team": TEAMNAME_REPLACEMENTS,
                }
            )
            .set_index(index)
            .sort_index()
            .convert_dtypes()
        )

    def read_shot_events(self, match_id: Optional[Union[int, list[int]]] = None) -> pd.DataFrame:
        """Retrieve the shot events for the selected matches or the selected leagues and seasons.

        Parameters
        ----------
        match_id : int or list of int, optional
            Retrieve the shot events for a specific match.

        Raises
        ------
        ValueError
            If the given match_id could not be found in the selected seasons.

        Returns
        -------
        pd.DataFrame
        """
        df_schedule = self.read_schedule(include_matches_without_data=False)
        df_results = self._select_matches(df_schedule, match_id)

        shots = []
        for (league, season, game), league_season_game in df_results.iterrows():
            league_id = league_season_game["league_id"]
            season_id = league_season_game["season_id"]
            game_id = league_season_game["game_id"]
            url = league_season_game["url"]

            data = self._read_match(url, game_id)
            if data is None:
                continue

            match_info = data["match_info"]
            team_name_to_id = {
                _as_str(match_info[f"team_{side}"]): _as_int(match_info[side])
                for side in ("h", "a")
            }

            rosters_data = data["rostersData"]
            player_name_to_id = {}
            for team_data in rosters_data.values():
                for player in team_data.values():
                    player_name = _as_str(player["player"])
                    player_id = _as_int(player["id"])
                    player_name_to_id[player_name] = player_id

            shots_data = data["shotsData"]
            for team_shots in shots_data.values():
                for shot in team_shots:
                    team_side = shot["h_a"]
                    team = _as_str(shot[f"{team_side}_team"])
                    team_id = team_name_to_id[team]
                    assist_player = _as_str(shot["player_assisted"])
                    assist_player_id = player_name_to_id.get(assist_player, pd.NA)
                    shots.append(
                        {
                            "league_id": league_id,
                            "league": league,
                            "season_id": season_id,
                            "season": season,
                            "game_id": game_id,
                            "game": game,
                            "date": shot["date"],
                            "shot_id": _as_int(shot["id"]),
                            "team_id": team_id,
                            "team": team,
                            "player_id": _as_int(shot["player_id"]),
                            "player": shot["player"],
                            "assist_player_id": assist_player_id,
                            "assist_player": assist_player,
                            "xg": _as_float(shot["xG"]),
                            "location_x": _as_float(shot["X"]),
                            "location_y": _as_float(shot["Y"]),
                            "minute": _as_int(shot["minute"]),
                            "body_part": SHOT_BODY_PARTS.get(shot["shotType"], pd.NA),
                            "situation": SHOT_SITUATIONS.get(shot["situation"], pd.NA),
                            "result": SHOT_RESULTS.get(shot["result"], pd.NA),
                        }
                    )

        index = ["league", "season", "game", "team", "player"]
        if len(shots) == 0:
            return pd.DataFrame(index=index)

        return (
            pd.DataFrame.from_records(shots)
            .assign(date=lambda g: pd.to_datetime(g["date"], format="%Y-%m-%d %H:%M:%S"))
            .replace(
                {
                    "team": TEAMNAME_REPLACEMENTS,
                }
            )
            .set_index(index)
            .sort_index()
            .convert_dtypes()
        )

    def _select_matches(
        self,
        df_schedule: pd.DataFrame,
        match_id: Optional[Union[int, list[int]]] = None,
    ) -> pd.DataFrame:
        if match_id is not None:
            match_ids = [match_id] if isinstance(match_id, int) else match_id
            df = df_schedule[df_schedule["game_id"].isin(match_ids)]
            if df.empty:
                raise ValueError("No matches found with the given IDs in the selected seasons.")
        else:
            df = df_schedule

        return df

    def _read_leagues(self, no_cache: bool = False) -> dict:
        url = UNDERSTAT_URL
        filepath = self.data_dir / "leagues.json"
        response = self.get(url, filepath, no_cache=no_cache, var="statData")
        return json.load(response)

    def _read_league_season(
        self, url: str, league_id: int, season_id: int, no_cache: bool = False
    ) -> dict:
        filepath = self.data_dir / f"league_{league_id}_season_{season_id}.json"
        response = self.get(
            url,
            filepath,
            no_cache=no_cache,
            var=["datesData", "playersData", "teamsData"],
        )
        return json.load(response)

    def _read_match(self, url: str, match_id: int) -> Optional[dict]:
        try:
            filepath = self.data_dir / f"match_{match_id}.json"
            response = self.get(url, filepath, var=["match_info", "rostersData", "shotsData"])
            data = json.load(response)
        except ConnectionError:
            data = None

        return data


def _as_bool(value: Any) -> Optional[bool]:
    try:
        return bool(value)
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> Optional[int]:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_str(value: Any) -> Optional[str]:
    try:
        return unescape(value)
    except (TypeError, ValueError):
        return None
