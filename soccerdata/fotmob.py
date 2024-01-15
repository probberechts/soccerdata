'''Scraper for http://fotmob.com.'''
import itertools
import json
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Union

import pandas as pd

from ._common import BaseRequestsReader, make_game_id, season_code
from ._config import DATA_DIR, NOCACHE, NOSTORE, TEAMNAME_REPLACEMENTS, logger

FOTMOB_DATADIR = DATA_DIR / 'Fotmob'
FOTMOB_API = 'https://www.fotmob.com/api/'


class Fotmob(BaseRequestsReader):
    """Provides pd.DataFrames from data available at http://www.fotmob.com.

    Data will be downloaded as necessary and cached locally in
    ``~/soccerdata/data/Fotmob``.

    Parameters
    ----------
    leagues : string or iterable, optional
        IDs of Leagues to include.
    seasons : string, int or list, optional
        Seasons to include. Supports multiple formats.
        Examples: '16-17'; 2016; '2016-17'; [14, 15, 16]
    proxy : 'tor' or dict or list(dict) or callable, optional
        Use a proxy to hide your IP address. Valid options are:
            - 'tor': Uses the Tor network. Tor should be running in
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
        help to avoid getting blocked.
    """

    def __init__(
        self,
        leagues: Optional[Union[str, List[str]]] = None,
        seasons: Optional[Union[str, int, Iterable[Union[str, int]]]] = None,
        proxy: Optional[
            Union[str, Dict[str, str], List[Dict[str, str]], Callable[[], Dict[str, str]]]
        ] = None,
        no_cache: bool = NOCACHE,
        no_store: bool = NOSTORE,
        data_dir: Path = FOTMOB_DATADIR,
    ):
        '''Initialize the Fotmob reader.'''
        super().__init__(
            leagues=leagues,
            proxy=proxy,
            no_cache=no_cache,
            no_store=no_store,
            data_dir=data_dir,
        )
        self.seasons = seasons  # type: ignore
        self.rate_limit = 3
        self.max_delay = 3
        if not self.no_store:
            (self.data_dir / 'seasons').mkdir(parents=True, exist_ok=True)
            (self.data_dir / 'matches').mkdir(parents=True, exist_ok=True)
            (self.data_dir / 'previews').mkdir(parents=True, exist_ok=True)
            (self.data_dir / 'events').mkdir(parents=True, exist_ok=True)

    @property
    def leagues(self) -> List[str]:
        """Return a list of selected leagues."""
        return list(self._leagues_dict.keys())

    @classmethod
    def _all_leagues(cls) -> Dict[str, str]:
        """Return a dict mapping all canonical league IDs to source league IDs."""
        res = super()._all_leagues()
        return res

    def read_leagues(self) -> pd.DataFrame:
        """Retrieve the selected leagues from the datasource.

        Returns
        -------
        pd.DataFrame
        """
        filemask = 'allLeagues'
        url = FOTMOB_API + filemask
        filepath = self.data_dir / 'allLeagues.json'
        reader = self.get(url, filepath)
        data = json.load(reader)
        leagues = []
        for k, v in data.items():
            if (k == 'favourite') | (k == 'popular') | (k == 'userSettings'):
                continue
            elif k == 'international':
                for int_league in v[0]['leagues']:
                    leagues.append(
                        {
                            'region': v[0]['ccode'],
                            'league_id': int_league['id'],
                            'league': int_league['name'],
                            'url': int_league['pageUrl'],
                        }
                    )
            else:
                for country in v:
                    for dom_league in country['leagues']:
                        leagues.append(
                            {
                                'region': country['ccode'],
                                'league_id': dom_league['id'],
                                'league': dom_league['name'],
                                'url': dom_league['pageUrl'],
                            }
                        )
        df = (
            pd.DataFrame(leagues)
            .assign(league=lambda x: x.region + '-' + x.league)
            .pipe(self._translate_league)
            .set_index('league')
            .loc[self._selected_leagues.keys()]
            .sort_index()
        )
        return df[df.index.isin(self.leagues)]

    def read_seasons(self) -> pd.DataFrame:
        """Retrieve the selected seasons for the selected leagues.

        Returns
        -------
        pd.DataFrame
        """
        df_leagues = self.read_leagues()
        seasons = []
        for lkey, league in df_leagues.iterrows():
            url_append = 'leagues?id=' + str(league.league_id)
            url = FOTMOB_API + url_append
            filemask = 'seasons/{}.json'
            filepath = self.data_dir / filemask.format(lkey)
            reader = self.get(url, filepath)
            data = json.load(reader)
            # extract season IDs
            avail_seasons = data['allAvailableSeasons']
            for season in avail_seasons:
                seasons.append(
                    {
                        'url': url_append + '&season=' + season,
                        'league': lkey,
                        'league_id': league.league_id,
                        'season': season_code(season),
                    }
                )
            # Change season id for 2122 season manually (gross)
        df = pd.DataFrame(seasons).set_index(['league', 'season']).sort_index()
        return df.loc[df.index.isin(list(itertools.product(self.leagues, self.seasons)))]

    def read_league_table(self) -> pd.DataFrame:
        """Retrieve the league table for the selected leagues

        Returns
        -------
        pd.DataFrame
        """
        filemask = 'table_{}_{}_{}.html'

        # get league IDs
        seasons = self.read_seasons()
        # collect teams
        mult_tables = []
        cup_finals = []
        seasons_list = []
        for (lkey, skey), season in seasons.iterrows():
            # Keep list of seasons for later iterating (cup finals)
            seasons_list.append(skey)
            # read html page (league overview)
            filepath = self.data_dir / filemask.format(lkey, skey, 'table')
            url = FOTMOB_API + season.url
            reader = self.get(url, filepath)
            data = json.load(reader)
            if 'tables' in data['table'][0]['data']:
                df_table = pd.json_normalize(data['table'][0]['data']['tables'][2]['table']['all'])
            else:
                df_table = pd.json_normalize(data['table'][0]['data']['table']['all'])
            cols = [
                'name',
                'id',
                'played',
                'wins',
                'draws',
                'losses',
                'scoresStr',
                'goalConDiff',
                'pts',
            ]
            df_table = df_table[df_table.columns[df_table.columns.isin(cols)]]
            df_table.insert(6, 'goalScr', df_table.scoresStr.str.split('-', expand=True)[0], True)
            df_table.insert(7, 'goalCon', df_table.scoresStr.str.split('-', expand=True)[1], True)
            df_table.drop(columns=['scoresStr'], inplace=True)
            df_table['league'] = lkey
            df_table['season'] = skey

            # If league has a playoff, add final playoff standing as a column
            if 'playoff' in data['tabs']:
                df_table['playoff'] = None
                # Get cup game finalists (for leagues with playoffs)
                if 'stats' in data['tabs']:
                    cup_finals = data['stats']['trophies']
                playoff_rounds = data['playoff']['rounds']
                for i in range(len(playoff_rounds)):
                    stage_teams = []
                    for game in playoff_rounds[i]['matchups']:
                        if not bool(game):
                            continue
                        stage = game['stage']
                        stage_teams.append(game['homeTeamId'])
                        stage_teams.append(game['awayTeamId'])
                        df_table.loc[df_table['id'].isin(stage_teams), 'playoff'] = stage
                        if stage == 'final':
                            winner = game['winner']
                            df_table.loc[df_table['id'] == winner, 'playoff'] = 'cup_final'
            mult_tables.append(df_table)
        df = pd.concat(mult_tables, axis=0)
        # Add cup finalists to table
        if bool(cup_finals):
            skey = [season[:2] for season in seasons_list]
            for final in cup_finals:
                if final['seasonName'][-2:] in skey:
                    winner = final['winner']['id']
                    finalist = final['loser']['id']
                    # Re-map season name from Fotmob so it matches soccerdata format
                    finals_season = final['seasonName'][-2:] + str(
                        int(final['seasonName'][-2:]) + 1
                    )
                    season_map = df.season == finals_season
                    df.loc[(df['id'] == winner) & season_map, 'playoff'] = 'cup_winner'
                    df.loc[(df['id'] == finalist) & season_map, 'playoff'] = 'final'
        df = (
            df.rename(columns={'Squad': 'team'})
            .replace({'team': TEAMNAME_REPLACEMENTS})
            .set_index(['league', 'season'])
            .sort_index()
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
        df_seasons = self.read_seasons()
        all_schedules = []
        url_fixtures = []
        for (lkey, skey), season in df_seasons.iterrows():
            url_stats = FOTMOB_API + season.url
            filepath_stats = self.data_dir / f'teams_{lkey}_{skey}.json'
            reader = self.get(url_stats, filepath_stats)
            data = json.load(reader)

            df = pd.json_normalize(data['matches']['allMatches'])
            url_fixtures = ['/matchDetails?matchId=' + id for id in df.id]
            df['league'] = lkey
            df['season'] = skey
            all_schedules.append(df)

        # Construct the output dataframe
        df = (
            pd.concat(all_schedules)
            .rename(
                columns={
                    'round': 'week',
                    'home.name': 'home_team',
                    'away.name': 'away_team',
                }
            )
            .replace(
                {
                    'home_team': TEAMNAME_REPLACEMENTS,
                    'away_team': TEAMNAME_REPLACEMENTS,
                }
            )
            .assign(date=lambda x: pd.to_datetime(x['status.utcTime']))
        )
        df['gameUrl'] = url_fixtures
        df['game'] = df.apply(make_game_id, axis=1)
        df = df.set_index(['league', 'season', 'game']).sort_index()
        return df

    def read_game_match_stats(
        self,
        stat_type: str = 'Top stats',
        match_id: Optional[Union[str, List[str]]] = None,
        force_cache: bool = False,
    ) -> pd.DataFrame:
        """Retrieve the match stats for the selected leagues and seasons.

        The following stat types are available:
            * 'Top stats'
            * 'Shots'
            * 'Expected goals (xG)'
            * 'Passes'
            * 'Defence'
            * 'Duels'
            * 'Discipline'

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
        # Retrieve games for which a match report is available
        df_matches = self.read_schedule(force_cache).reset_index()

        df_complete = df_matches[df_matches['status.finished'] & ~df_matches['status.cancelled']]
        # Select requested games if available
        if match_id is not None:
            iterator = df_complete[
                df_complete.id.isin([match_id] if isinstance(match_id, str) else match_id)
            ]
            if len(iterator) == 0:
                raise ValueError('No games found with the given IDs in the selected seasons.')
        else:
            iterator = df_complete
        games = []
        for i, game in iterator.iterrows():
            # Get data for specific game
            url = FOTMOB_API + game.gameUrl
            filemask = 'matches/{}.json'
            logger.info('[%s/%s] Retrieving game with id=%s', i + 1, len(iterator), game.id)
            filepath = self.data_dir / filemask.format(game.id)
            reader = self.get(url, filepath)
            game_data = json.load(reader)

            # Get home and away teams
            matchweek = game_data['general']['matchRound']
            match_time = game_data['general']['matchTimeUTCDate']
            df_home = pd.json_normalize(game_data['general']['homeTeam'])
            df_home['Matchweek'] = matchweek
            df_home['Date'] = match_time
            df_home.rename(columns={'name': 'Home Team', 'id': 'Home id'}, inplace=True)
            df_away = pd.json_normalize(game_data['general']['awayTeam'])
            df_away.rename(columns={'name': 'Away Team', 'id': 'Away id'}, inplace=True)
            df_teams = pd.concat([df_home, df_away], axis=1)
            stats = []
            stats.append(df_teams)
            # Get scores
            home_goals = game_data['header']['teams'][0]['score']
            away_goals = game_data['header']['teams'][1]['score']
            df_goals = pd.DataFrame({'Home Goals': [home_goals], 'Away Goals': [away_goals]})
            stats.append(df_goals)

            # Get stats types
            all_stats = game_data['content']['stats']['Periods']['All']['stats']
            stats_dict = {i: all_stats[i]['title'] for i in range(len(all_stats))}

            # if stat_type in stats_dict.values():
            df_stats = pd.json_normalize(
                all_stats, record_path='stats', meta=['title', 'key'], meta_prefix='cat_'
            )
            df_stat_type = df_stats[['title', 'stats', 'cat_title']].set_index('cat_title')

            if stat_type not in stats_dict.values():
                raise TypeError(f'Invalid argument: stat_type should be in {stats_dict.values()}')
            else:
                df_stat_type = df_stat_type.loc[df_stat_type.index == stat_type]
            df_stat_type = (
                df_stat_type.T.reset_index()
                .set_axis(df_stat_type.T.reset_index().iloc[0], axis=1)
                .iloc[1:]
                .rename_axis(None, axis=1)
            )
            df_stat_type = df_stat_type.iloc[:, 2:]
            for col in df_stat_type.columns:
                df_single_stat = pd.DataFrame(df_stat_type[col])
                df_stat_split = df_single_stat[col].apply(pd.Series)
                df_single_stat = pd.concat([df_single_stat, df_stat_split], axis=1)
                df_single_stat.drop(col, axis=1, inplace=True)
                df_single_stat.rename(columns={0: 'Home ' + col, 1: 'Away ' + col}, inplace=True)
                # Split percentage values into their own column
                if df_single_stat['Home ' + col].dtypes == object:
                    if (df_single_stat['Home ' + col].str.contains('%')).any():
                        home_split_stats = df_single_stat['Home ' + col].str.split(
                            r'[\(%]', expand=True
                        )
                        df_single_stat['Home ' + col] = int(home_split_stats[0].iloc[0])
                        df_single_stat['Home ' + col + ' %'] = int(home_split_stats[1].iloc[0])
                        away_split_stats = df_single_stat['Away ' + col].str.split(
                            r'[\(%]', expand=True
                        )
                        df_single_stat['Away ' + col] = int(away_split_stats[0].iloc[0])
                        df_single_stat['Away ' + col + ' %'] = int(away_split_stats[1].iloc[0])
                stats.append(df_single_stat.reset_index())
            # dfs = pd.concat(tmp_dfs, axis=1)
            # dfs = dfs.T.drop_duplicates().T
            # stats.append(tmp_dfs)
            df_game = (
                pd.concat(stats, axis=1).replace({'team': TEAMNAME_REPLACEMENTS}).sort_index()
            )
            # df_game = df_game.T.drop_duplicates().T
            games.append(df_game)
        df = (
            pd.concat(games, ignore_index=True)
            .replace({'team': TEAMNAME_REPLACEMENTS})
            .set_index(['Matchweek', 'Date', 'Home Team', 'Home id', 'Away Team', 'Away id'])
            .sort_index()
        )
        return df
