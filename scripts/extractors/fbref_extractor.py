"""
FBref Data Extractor
Extracts data from FBref (Football Reference) into 44 database tables
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
import soccerdata as sd

from .base_extractor import BaseExtractor
from scripts.utils import DatabaseManager, DataExtractionLogger, ConfigLoader


class FBrefExtractor(BaseExtractor):
    """
    Extracts comprehensive football statistics from FBref

    Handles 44 tables:
    - fbref_leagues, fbref_seasons
    - 11 team season stat tables
    - 9 team match stat tables
    - 11 player season stat tables
    - 7 player match stat tables
    - fbref_schedule, fbref_lineups, fbref_events, fbref_shot_events
    """

    # Stat types for different categories
    TEAM_SEASON_STATS = [
        'standard', 'keeper', 'keeper_adv', 'shooting', 'passing',
        'passing_types', 'goal_shot_creation', 'defense', 'possession',
        'playing_time', 'misc'
    ]

    TEAM_MATCH_STATS = [
        'schedule', 'keeper', 'shooting', 'passing', 'passing_types',
        'goal_shot_creation', 'defense', 'possession', 'misc'
    ]

    PLAYER_SEASON_STATS = [
        'standard', 'keeper', 'keeper_adv', 'shooting', 'passing',
        'passing_types', 'goal_shot_creation', 'defense', 'possession',
        'playing_time', 'misc'
    ]

    PLAYER_MATCH_STATS = [
        'summary', 'keepers', 'passing', 'passing_types',
        'defense', 'possession', 'misc'
    ]

    def __init__(
        self,
        db_manager: DatabaseManager,
        config_loader: ConfigLoader,
        logger: Optional[DataExtractionLogger] = None,
    ):
        """Initialize FBref extractor"""
        super().__init__(
            data_source='fbref',
            db_manager=db_manager,
            config_loader=config_loader,
            logger=logger,
        )

    def get_table_configs(self) -> List[Dict[str, Any]]:
        """
        Get configuration for all 44 FBref tables

        Returns:
            List of table configurations
        """
        configs = []

        # Meta tables
        configs.append({
            'table_name': 'fbref_leagues',
            'extraction_method': 'extract_leagues',
            'conflict_columns': ['league'],
            'required_fields': ['league', 'data_source'],
        })

        configs.append({
            'table_name': 'fbref_seasons',
            'extraction_method': 'extract_seasons',
            'conflict_columns': ['league', 'season'],
            'required_fields': ['league', 'season', 'data_source'],
        })

        # Team season stats (11 tables)
        for stat_type in self.TEAM_SEASON_STATS:
            configs.append({
                'table_name': f'fbref_team_season_{stat_type}',
                'extraction_method': 'extract_team_season_stats',
                'stat_type': stat_type,
                'conflict_columns': ['league', 'season', 'team'],
                'required_fields': ['league', 'season', 'team', 'data_source'],
            })

        # Team match stats (9 tables)
        for stat_type in self.TEAM_MATCH_STATS:
            configs.append({
                'table_name': f'fbref_team_match_{stat_type}',
                'extraction_method': 'extract_team_match_stats',
                'stat_type': stat_type,
                'conflict_columns': ['league', 'season', 'team', 'game'],
                'required_fields': ['league', 'season', 'team', 'game', 'data_source'],
            })

        # Player season stats (11 tables)
        for stat_type in self.PLAYER_SEASON_STATS:
            configs.append({
                'table_name': f'fbref_player_season_{stat_type}',
                'extraction_method': 'extract_player_season_stats',
                'stat_type': stat_type,
                'conflict_columns': ['league', 'season', 'team', 'player'],
                'required_fields': ['league', 'season', 'team', 'player', 'data_source'],
            })

        # Player match stats (7 tables)
        for stat_type in self.PLAYER_MATCH_STATS:
            configs.append({
                'table_name': f'fbref_player_match_{stat_type}',
                'extraction_method': 'extract_player_match_stats',
                'stat_type': stat_type,
                'conflict_columns': ['league', 'season', 'game', 'team', 'player'],
                'required_fields': ['league', 'season', 'game', 'team', 'player', 'data_source'],
            })

        # Schedule (match-level data)
        configs.append({
            'table_name': 'fbref_schedule',
            'extraction_method': 'extract_schedule',
            'conflict_columns': ['league', 'season', 'game'],
            'required_fields': ['league', 'season', 'game', 'date', 'data_source'],
        })

        # Lineups
        configs.append({
            'table_name': 'fbref_lineups',
            'extraction_method': 'extract_lineups',
            'conflict_columns': ['league', 'season', 'game', 'team', 'player'],
            'required_fields': ['league', 'season', 'game', 'team', 'player', 'data_source'],
        })

        # Events
        configs.append({
            'table_name': 'fbref_events',
            'extraction_method': 'extract_events',
            'conflict_columns': ['league', 'season', 'game', 'minute', 'event_id'],
            'required_fields': ['league', 'season', 'game', 'minute', 'data_source'],
        })

        # Shot events
        configs.append({
            'table_name': 'fbref_shot_events',
            'extraction_method': 'extract_shot_events',
            'conflict_columns': ['league', 'season', 'game', 'minute', 'player'],
            'required_fields': ['league', 'season', 'game', 'minute', 'player', 'data_source'],
        })

        return configs

    def extract_data(
        self,
        table_config: Dict[str, Any],
        league: str,
        season: str,
    ) -> List[Dict[str, Any]]:
        """
        Extract data for a specific FBref table

        Args:
            table_config: Table configuration
            league: League name
            season: Season identifier

        Returns:
            List of data dictionaries
        """
        extraction_method = table_config['extraction_method']
        stat_type = table_config.get('stat_type')

        # Get method by name
        method = getattr(self, extraction_method)

        # Call extraction method
        if stat_type:
            return method(league, season, stat_type)
        else:
            return method(league, season)

    def _get_fbref_reader(self, league: str, season: str) -> sd.FBref:
        """
        Get configured FBref reader instance

        Args:
            league: League name
            season: Season identifier

        Returns:
            FBref reader instance
        """
        # Convert standardized league name to soccerdata ID
        soccerdata_league = self.get_soccerdata_league_id(league)

        if not soccerdata_league:
            raise ValueError(f"No soccerdata ID found for league: {league}")

        # Create FBref instance
        return sd.FBref(leagues=soccerdata_league, seasons=season)

    def _dataframe_to_dicts(
        self,
        df: pd.DataFrame,
        league: str,
        season: str,
        flatten_columns: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Convert pandas DataFrame to list of dictionaries for database insertion

        Args:
            df: DataFrame to convert
            league: League name
            season: Season identifier
            flatten_columns: Whether to flatten MultiIndex columns

        Returns:
            List of dictionaries
        """
        if df.empty:
            return []

        # Reset index to include all index levels as columns
        df_reset = df.reset_index()

        # Flatten MultiIndex columns if present
        if flatten_columns and isinstance(df_reset.columns, pd.MultiIndex):
            df_reset.columns = ['_'.join(map(str, col)).strip('_') for col in df_reset.columns.values]

        # Clean column names (lowercase, replace spaces with underscores)
        df_reset.columns = [
            col.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
            for col in df_reset.columns
        ]

        # Add metadata columns
        df_reset['league'] = league
        df_reset['season'] = season
        df_reset['data_source'] = 'fbref'

        # Convert to dictionary records
        records = df_reset.to_dict('records')

        # Clean values (convert NaN to None, etc.)
        cleaned_records = []
        for record in records:
            cleaned_record = {}
            for key, value in record.items():
                # Convert pandas NA/NaN to None
                if pd.isna(value):
                    cleaned_record[key] = None
                # Convert pandas Timestamp to datetime
                elif isinstance(value, pd.Timestamp):
                    cleaned_record[key] = value.to_pydatetime()
                else:
                    cleaned_record[key] = value
            cleaned_records.append(cleaned_record)

        return cleaned_records

    # ==== EXTRACTION METHODS ====

    def extract_leagues(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract league metadata"""
        fbref = self._get_fbref_reader(league, season)
        df = fbref.read_leagues()

        # Convert to records (leagues are indexed by league name)
        records = []
        for league_name, row in df.iterrows():
            record = {
                'league': league_name,
                'data_source': 'fbref',
                'first_season': row.get('first_season'),
                'last_season': row.get('last_season'),
                'tier': row.get('tier'),
                'url': row.get('url'),
            }
            records.append(record)

        return records

    def extract_seasons(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract season metadata"""
        fbref = self._get_fbref_reader(league, season)
        df = fbref.read_seasons()

        # Seasons are indexed by (league, season)
        records = []
        for (league_name, season_name), row in df.iterrows():
            record = {
                'league': league_name,
                'season': season_name,
                'data_source': 'fbref',
                'url': row.get('url'),
            }
            records.append(record)

        return records

    def extract_team_season_stats(
        self,
        league: str,
        season: str,
        stat_type: str
    ) -> List[Dict[str, Any]]:
        """Extract team season statistics"""
        fbref = self._get_fbref_reader(league, season)
        df = fbref.read_team_season_stats(stat_type=stat_type)

        return self._dataframe_to_dicts(df, league, season)

    def extract_team_match_stats(
        self,
        league: str,
        season: str,
        stat_type: str
    ) -> List[Dict[str, Any]]:
        """Extract team match statistics"""
        fbref = self._get_fbref_reader(league, season)

        if stat_type == 'schedule':
            # Use read_schedule for schedule data
            df = fbref.read_schedule()
        else:
            df = fbref.read_team_match_stats(stat_type=stat_type)

        return self._dataframe_to_dicts(df, league, season)

    def extract_player_season_stats(
        self,
        league: str,
        season: str,
        stat_type: str
    ) -> List[Dict[str, Any]]:
        """Extract player season statistics"""
        fbref = self._get_fbref_reader(league, season)
        df = fbref.read_player_season_stats(stat_type=stat_type)

        return self._dataframe_to_dicts(df, league, season)

    def extract_player_match_stats(
        self,
        league: str,
        season: str,
        stat_type: str
    ) -> List[Dict[str, Any]]:
        """Extract player match statistics"""
        fbref = self._get_fbref_reader(league, season)
        df = fbref.read_player_match_stats(stat_type=stat_type)

        return self._dataframe_to_dicts(df, league, season)

    def extract_schedule(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract match schedule"""
        fbref = self._get_fbref_reader(league, season)
        df = fbref.read_schedule()

        return self._dataframe_to_dicts(df, league, season)

    def extract_lineups(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract match lineups"""
        fbref = self._get_fbref_reader(league, season)

        try:
            df = fbref.read_lineup()
            return self._dataframe_to_dicts(df, league, season)
        except Exception as e:
            self.logger.logger.warning(f"No lineup data available: {e}")
            return []

    def extract_events(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract match events"""
        fbref = self._get_fbref_reader(league, season)

        try:
            df = fbref.read_events()
            return self._dataframe_to_dicts(df, league, season)
        except Exception as e:
            self.logger.logger.warning(f"No event data available: {e}")
            return []

    def extract_shot_events(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract shot events"""
        fbref = self._get_fbref_reader(league, season)

        try:
            df = fbref.read_shot_events()
            return self._dataframe_to_dicts(df, league, season)
        except Exception as e:
            self.logger.logger.warning(f"No shot event data available: {e}")
            return []
