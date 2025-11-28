"""
Understat Data Extractor
Extracts data from Understat into 7 database tables
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import soccerdata as sd

from .base_extractor import BaseExtractor
from scripts.utils import DatabaseManager, DataExtractionLogger, ConfigLoader


class UnderstatExtractor(BaseExtractor):
    """
    Extracts advanced xG statistics from Understat

    Handles 7 tables:
    - understat_leagues, understat_seasons
    - understat_schedule
    - understat_team_match_stats
    - understat_player_season_stats
    - understat_player_match_stats
    - understat_shot_events
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        config_loader: ConfigLoader,
        logger: Optional[DataExtractionLogger] = None,
    ):
        """Initialize Understat extractor"""
        super().__init__(
            data_source='understat',
            db_manager=db_manager,
            config_loader=config_loader,
            logger=logger,
        )

    def get_table_configs(self) -> List[Dict[str, Any]]:
        """
        Get configuration for all 7 Understat tables

        Returns:
            List of table configurations
        """
        return [
            {
                'table_name': 'understat_leagues',
                'extraction_method': 'extract_leagues',
                'conflict_columns': ['league'],
                'required_fields': ['league', 'data_source'],
            },
            {
                'table_name': 'understat_seasons',
                'extraction_method': 'extract_seasons',
                'conflict_columns': ['league', 'season'],
                'required_fields': ['league', 'season', 'data_source'],
            },
            {
                'table_name': 'understat_schedule',
                'extraction_method': 'extract_schedule',
                'conflict_columns': ['league', 'season', 'game'],
                'required_fields': ['league', 'season', 'game', 'data_source'],
            },
            {
                'table_name': 'understat_team_match_stats',
                'extraction_method': 'extract_team_match_stats',
                'conflict_columns': ['league', 'season', 'game', 'team'],
                'required_fields': ['league', 'season', 'game', 'team', 'data_source'],
            },
            {
                'table_name': 'understat_player_season_stats',
                'extraction_method': 'extract_player_season_stats',
                'conflict_columns': ['league', 'season', 'team', 'player'],
                'required_fields': ['league', 'season', 'team', 'player', 'data_source'],
            },
            {
                'table_name': 'understat_player_match_stats',
                'extraction_method': 'extract_player_match_stats',
                'conflict_columns': ['league', 'season', 'game', 'team', 'player'],
                'required_fields': ['league', 'season', 'game', 'team', 'player', 'data_source'],
            },
            {
                'table_name': 'understat_shot_events',
                'extraction_method': 'extract_shot_events',
                'conflict_columns': ['league', 'season', 'game', 'shot_id'],
                'required_fields': ['league', 'season', 'game', 'data_source'],
            },
        ]

    def extract_data(
        self,
        table_config: Dict[str, Any],
        league: str,
        season: str,
    ) -> List[Dict[str, Any]]:
        """
        Extract data for a specific Understat table

        Args:
            table_config: Table configuration
            league: League name
            season: Season identifier

        Returns:
            List of data dictionaries
        """
        extraction_method = table_config['extraction_method']
        method = getattr(self, extraction_method)
        return method(league, season)

    def _get_understat_reader(self, league: str, season: str) -> sd.Understat:
        """
        Get configured Understat reader instance

        Args:
            league: League name
            season: Season identifier

        Returns:
            Understat reader instance
        """
        soccerdata_league = self.get_soccerdata_league_id(league)

        if not soccerdata_league:
            raise ValueError(f"No soccerdata ID found for league: {league}")

        return sd.Understat(leagues=soccerdata_league, seasons=season)

    def _dataframe_to_dicts(
        self,
        df: pd.DataFrame,
        league: str,
        season: str,
    ) -> List[Dict[str, Any]]:
        """Convert pandas DataFrame to list of dictionaries"""
        if df.empty:
            return []

        df_reset = df.reset_index()

        # Clean column names
        df_reset.columns = [
            col.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
            for col in df_reset.columns
        ]

        # Add metadata
        df_reset['league'] = league
        df_reset['season'] = season
        df_reset['data_source'] = 'understat'

        # Convert to dict and clean values
        records = df_reset.to_dict('records')
        cleaned_records = []
        for record in records:
            cleaned_record = {}
            for key, value in record.items():
                if pd.isna(value):
                    cleaned_record[key] = None
                elif isinstance(value, pd.Timestamp):
                    cleaned_record[key] = value.to_pydatetime()
                else:
                    cleaned_record[key] = value
            cleaned_records.append(cleaned_record)

        return cleaned_records

    # ==== EXTRACTION METHODS ====

    def extract_leagues(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract league metadata"""
        understat = self._get_understat_reader(league, season)
        df = understat.read_leagues()

        records = []
        for league_name, row in df.iterrows():
            record = {
                'league': league_name,
                'data_source': 'understat',
                'league_id': row.get('league_id'),
                'url': row.get('url'),
            }
            records.append(record)

        return records

    def extract_seasons(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract season metadata"""
        understat = self._get_understat_reader(league, season)
        df = understat.read_seasons()

        records = []
        for (league_name, season_name), row in df.iterrows():
            record = {
                'league': league_name,
                'season': season_name,
                'data_source': 'understat',
                'season_id': row.get('season_id'),
                'year': row.get('year'),
            }
            records.append(record)

        return records

    def extract_schedule(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract match schedule with xG"""
        understat = self._get_understat_reader(league, season)
        df = understat.read_schedule()

        return self._dataframe_to_dicts(df, league, season)

    def extract_team_match_stats(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract team match statistics with xG and PPDA"""
        understat = self._get_understat_reader(league, season)
        df = understat.read_team_match_stats()

        return self._dataframe_to_dicts(df, league, season)

    def extract_player_season_stats(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract player season statistics"""
        understat = self._get_understat_reader(league, season)
        df = understat.read_player_season_stats()

        return self._dataframe_to_dicts(df, league, season)

    def extract_player_match_stats(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract player match statistics"""
        understat = self._get_understat_reader(league, season)
        df = understat.read_player_match_stats()

        return self._dataframe_to_dicts(df, league, season)

    def extract_shot_events(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract shot-level xG data with coordinates"""
        understat = self._get_understat_reader(league, season)

        try:
            df = understat.read_shot_events()
            return self._dataframe_to_dicts(df, league, season)
        except Exception as e:
            self.logger.logger.warning(
                f"No shot events data available for {league} {season}: {e}"
            )
            return []
