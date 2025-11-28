"""
FotMob Data Extractor
Extracts data from FotMob into 11 database tables
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import soccerdata as sd

from .base_extractor import BaseExtractor
from scripts.utils import DatabaseManager, DataExtractionLogger, ConfigLoader


class FotMobExtractor(BaseExtractor):
    """
    Extracts football statistics from FotMob

    Handles 11 tables:
    - fotmob_leagues, fotmob_seasons
    - fotmob_league_table, fotmob_schedule
    - 7 team match stat tables (Top stats, Shots, Expected goals (xG), Passes, Defence, Duels, Discipline)
    """

    TEAM_MATCH_STATS = [
        'Top stats',
        'Shots',
        'Expected goals (xG)',
        'Passes',
        'Defence',
        'Duels',
        'Discipline',
    ]

    def __init__(
        self,
        db_manager: DatabaseManager,
        config_loader: ConfigLoader,
        logger: Optional[DataExtractionLogger] = None,
    ):
        """Initialize FotMob extractor"""
        super().__init__(
            data_source='fotmob',
            db_manager=db_manager,
            config_loader=config_loader,
            logger=logger,
        )

    def get_table_configs(self) -> List[Dict[str, Any]]:
        """
        Get configuration for all 11 FotMob tables

        Returns:
            List of table configurations
        """
        configs = []

        # Meta tables
        configs.append({
            'table_name': 'fotmob_leagues',
            'extraction_method': 'extract_leagues',
            'conflict_columns': ['league'],
            'required_fields': ['league', 'data_source'],
        })

        configs.append({
            'table_name': 'fotmob_seasons',
            'extraction_method': 'extract_seasons',
            'conflict_columns': ['league', 'season'],
            'required_fields': ['league', 'season', 'data_source'],
        })

        # League table
        configs.append({
            'table_name': 'fotmob_league_table',
            'extraction_method': 'extract_league_table',
            'conflict_columns': ['league', 'season', 'team'],
            'required_fields': ['league', 'season', 'team', 'data_source'],
        })

        # Schedule
        configs.append({
            'table_name': 'fotmob_schedule',
            'extraction_method': 'extract_schedule',
            'conflict_columns': ['league', 'season', 'game'],
            'required_fields': ['league', 'season', 'game', 'data_source'],
        })

        # Team match stats (7 tables)
        for stat_type in self.TEAM_MATCH_STATS:
            # Clean stat type for table name (lowercase, replace spaces and parens)
            clean_name = (
                stat_type.lower()
                .replace('(', '')
                .replace(')', '')
                .replace(' ', '_')
            )

            configs.append({
                'table_name': f'fotmob_team_match_{clean_name}',
                'extraction_method': 'extract_team_match_stats',
                'stat_type': stat_type,
                'conflict_columns': ['league', 'season', 'game', 'team'],
                'required_fields': ['league', 'season', 'game', 'team', 'data_source'],
            })

        return configs

    def extract_data(
        self,
        table_config: Dict[str, Any],
        league: str,
        season: str,
    ) -> List[Dict[str, Any]]:
        """
        Extract data for a specific FotMob table

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

    def _get_fotmob_reader(self, league: str, season: str) -> sd.FotMob:
        """
        Get configured FotMob reader instance

        Args:
            league: League name
            season: Season identifier

        Returns:
            FotMob reader instance
        """
        # Convert standardized league name to soccerdata ID
        soccerdata_league = self.get_soccerdata_league_id(league)

        if not soccerdata_league:
            raise ValueError(f"No soccerdata ID found for league: {league}")

        # Create FotMob instance
        return sd.FotMob(leagues=soccerdata_league, seasons=season)

    def _dataframe_to_dicts(
        self,
        df: pd.DataFrame,
        league: str,
        season: str,
    ) -> List[Dict[str, Any]]:
        """
        Convert pandas DataFrame to list of dictionaries for database insertion

        Args:
            df: DataFrame to convert
            league: League name
            season: Season identifier

        Returns:
            List of dictionaries
        """
        if df.empty:
            return []

        # Reset index to include all index levels as columns
        df_reset = df.reset_index()

        # Clean column names (lowercase, replace spaces with underscores)
        df_reset.columns = [
            col.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
            for col in df_reset.columns
        ]

        # Add metadata columns
        df_reset['league'] = league
        df_reset['season'] = season
        df_reset['data_source'] = 'fotmob'

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
        fotmob = self._get_fotmob_reader(league, season)
        df = fotmob.read_leagues()

        # Convert to records
        records = []
        for league_name, row in df.iterrows():
            record = {
                'league': league_name,
                'data_source': 'fotmob',
                'league_id': row.get('league_id'),
                'region': row.get('region'),
                'url': row.get('url'),
            }
            records.append(record)

        return records

    def extract_seasons(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract season metadata"""
        fotmob = self._get_fotmob_reader(league, season)
        df = fotmob.read_seasons()

        # Seasons are indexed by (league, season)
        records = []
        for (league_name, season_name), row in df.iterrows():
            record = {
                'league': league_name,
                'season': season_name,
                'data_source': 'fotmob',
                'season_id': row.get('season_id'),
            }
            records.append(record)

        return records

    def extract_league_table(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract league standings table"""
        fotmob = self._get_fotmob_reader(league, season)
        df = fotmob.read_league_table()

        return self._dataframe_to_dicts(df, league, season)

    def extract_schedule(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract match schedule"""
        fotmob = self._get_fotmob_reader(league, season)
        df = fotmob.read_schedule()

        return self._dataframe_to_dicts(df, league, season)

    def extract_team_match_stats(
        self,
        league: str,
        season: str,
        stat_type: str
    ) -> List[Dict[str, Any]]:
        """Extract team match statistics"""
        fotmob = self._get_fotmob_reader(league, season)

        try:
            df = fotmob.read_team_match_stats(stat_type=stat_type)
            return self._dataframe_to_dicts(df, league, season)
        except Exception as e:
            self.logger.logger.warning(
                f"No {stat_type} data available for {league} {season}: {e}"
            )
            return []
