"""
SoFIFA Data Extractor
Extracts EA Sports FC (FIFA) ratings data from SoFIFA into 6 database tables
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import soccerdata as sd

from .base_extractor import BaseExtractor
from ..utils import DatabaseManager, DataExtractionLogger, ConfigLoader


class SoFIFAExtractor(BaseExtractor):
    """
    Extracts EA Sports FC player and team ratings from SoFIFA

    Handles 6 tables:
    - sofifa_leagues
    - sofifa_versions
    - sofifa_teams
    - sofifa_players
    - sofifa_team_ratings
    - sofifa_player_ratings
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        config_loader: ConfigLoader,
        logger: Optional[DataExtractionLogger] = None,
    ):
        """Initialize SoFIFA extractor"""
        super().__init__(
            data_source='sofifa',
            db_manager=db_manager,
            config_loader=config_loader,
            logger=logger,
        )

    def get_table_configs(self) -> List[Dict[str, Any]]:
        """Get configuration for all 6 SoFIFA tables"""
        return [
            {
                'table_name': 'sofifa_leagues',
                'extraction_method': 'extract_leagues',
                'conflict_columns': ['league'],
                'required_fields': ['league', 'data_source'],
            },
            {
                'table_name': 'sofifa_versions',
                'extraction_method': 'extract_versions',
                'conflict_columns': ['version_id'],
                'required_fields': ['version_id', 'data_source'],
            },
            {
                'table_name': 'sofifa_teams',
                'extraction_method': 'extract_teams',
                'conflict_columns': ['league', 'team'],
                'required_fields': ['league', 'team', 'data_source'],
            },
            {
                'table_name': 'sofifa_players',
                'extraction_method': 'extract_players',
                'conflict_columns': ['league', 'team', 'player'],
                'required_fields': ['league', 'team', 'player', 'data_source'],
            },
            {
                'table_name': 'sofifa_team_ratings',
                'extraction_method': 'extract_team_ratings',
                'conflict_columns': ['league', 'team', 'version_id'],
                'required_fields': ['league', 'team', 'data_source'],
            },
            {
                'table_name': 'sofifa_player_ratings',
                'extraction_method': 'extract_player_ratings',
                'conflict_columns': ['league', 'team', 'player', 'version_id'],
                'required_fields': ['league', 'team', 'player', 'data_source'],
            },
        ]

    def extract_data(
        self,
        table_config: Dict[str, Any],
        league: str,
        season: str,
    ) -> List[Dict[str, Any]]:
        """Extract data for a specific SoFIFA table"""
        extraction_method = table_config['extraction_method']
        method = getattr(self, extraction_method)
        return method(league, season)

    def _get_sofifa_reader(self, league: str):
        """Get configured SoFIFA reader instance"""
        soccerdata_league = self.get_soccerdata_league_id(league)

        if not soccerdata_league:
            raise ValueError(f"No soccerdata ID found for league: {league}")

        return sd.SoFIFA(leagues=soccerdata_league)

    def _dataframe_to_dicts(
        self,
        df: pd.DataFrame,
        league: str,
    ) -> List[Dict[str, Any]]:
        """Convert pandas DataFrame to list of dictionaries"""
        if df.empty:
            return []

        df_reset = df.reset_index()
        df_reset.columns = [
            col.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
            for col in df_reset.columns
        ]

        df_reset['league'] = league
        df_reset['data_source'] = 'sofifa'

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
        sofifa = self._get_sofifa_reader(league)
        df = sofifa.read_leagues()

        records = []
        for league_name, row in df.iterrows():
            record = {
                'league': league_name,
                'data_source': 'sofifa',
                'league_id': row.get('league_id'),
            }
            records.append(record)

        return records

    def extract_versions(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract FIFA/EA Sports FC version information"""
        sofifa = self._get_sofifa_reader(league)

        try:
            df = sofifa.read_versions()

            records = []
            for idx, row in df.iterrows():
                record = {
                    'version_id': row.get('version_id'),
                    'data_source': 'sofifa',
                    'release_date': row.get('release_date'),
                    'version_name': row.get('version_name'),
                }
                records.append(record)

            return records
        except Exception as e:
            self.logger.logger.warning(
                f"No versions data available for {league}: {e}"
            )
            return []

    def extract_teams(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract team metadata"""
        sofifa = self._get_sofifa_reader(league)
        df = sofifa.read_teams()

        return self._dataframe_to_dicts(df, league)

    def extract_players(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract player metadata"""
        sofifa = self._get_sofifa_reader(league)

        try:
            df = sofifa.read_players()
            return self._dataframe_to_dicts(df, league)
        except Exception as e:
            self.logger.logger.warning(
                f"No players data available for {league}: {e}"
            )
            return []

    def extract_team_ratings(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract team ratings"""
        sofifa = self._get_sofifa_reader(league)

        try:
            df = sofifa.read_team_ratings()
            return self._dataframe_to_dicts(df, league)
        except Exception as e:
            self.logger.logger.warning(
                f"No team ratings data available for {league}: {e}"
            )
            return []

    def extract_player_ratings(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract player ratings"""
        sofifa = self._get_sofifa_reader(league)

        try:
            df = sofifa.read_player_ratings()
            return self._dataframe_to_dicts(df, league)
        except Exception as e:
            self.logger.logger.warning(
                f"No player ratings data available for {league}: {e}"
            )
            return []
