"""
Sofascore Data Extractor
Extracts data from Sofascore into 4 database tables
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import soccerdata as sd

from .base_extractor import BaseExtractor
from ..utils import DatabaseManager, DataExtractionLogger, ConfigLoader


class SofascoreExtractor(BaseExtractor):
    """
    Extracts football statistics from Sofascore

    Handles 4 tables:
    - sofascore_leagues, sofascore_seasons
    - sofascore_league_table
    - sofascore_schedule
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        config_loader: ConfigLoader,
        logger: Optional[DataExtractionLogger] = None,
    ):
        """Initialize Sofascore extractor"""
        super().__init__(
            data_source='sofascore',
            db_manager=db_manager,
            config_loader=config_loader,
            logger=logger,
        )

    def get_table_configs(self) -> List[Dict[str, Any]]:
        """Get configuration for all 4 Sofascore tables"""
        return [
            {
                'table_name': 'sofascore_leagues',
                'extraction_method': 'extract_leagues',
                'conflict_columns': ['league'],
                'required_fields': ['league', 'data_source'],
            },
            {
                'table_name': 'sofascore_seasons',
                'extraction_method': 'extract_seasons',
                'conflict_columns': ['league', 'season'],
                'required_fields': ['league', 'season', 'data_source'],
            },
            {
                'table_name': 'sofascore_league_table',
                'extraction_method': 'extract_league_table',
                'conflict_columns': ['league', 'season', 'team'],
                'required_fields': ['league', 'season', 'team', 'data_source'],
            },
            {
                'table_name': 'sofascore_schedule',
                'extraction_method': 'extract_schedule',
                'conflict_columns': ['league', 'season', 'game'],
                'required_fields': ['league', 'season', 'game', 'data_source'],
            },
        ]

    def extract_data(
        self,
        table_config: Dict[str, Any],
        league: str,
        season: str,
    ) -> List[Dict[str, Any]]:
        """Extract data for a specific Sofascore table"""
        extraction_method = table_config['extraction_method']
        method = getattr(self, extraction_method)
        return method(league, season)

    def _get_sofascore_reader(self, league: str, season: str) -> sd.Sofascore:
        """Get configured Sofascore reader instance"""
        soccerdata_league = self.get_soccerdata_league_id(league)

        if not soccerdata_league:
            raise ValueError(f"No soccerdata ID found for league: {league}")

        return sd.Sofascore(leagues=soccerdata_league, seasons=season)

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
        df_reset.columns = [
            col.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
            for col in df_reset.columns
        ]

        df_reset['league'] = league
        df_reset['season'] = season
        df_reset['data_source'] = 'sofascore'

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
        sofascore = self._get_sofascore_reader(league, season)
        df = sofascore.read_leagues()

        records = []
        for league_name, row in df.iterrows():
            record = {
                'league': league_name,
                'data_source': 'sofascore',
                'league_id': row.get('league_id'),
            }
            records.append(record)

        return records

    def extract_seasons(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract season metadata"""
        sofascore = self._get_sofascore_reader(league, season)
        df = sofascore.read_seasons()

        records = []
        for (league_name, season_name), row in df.iterrows():
            record = {
                'league': league_name,
                'season': season_name,
                'data_source': 'sofascore',
                'season_id': row.get('season_id'),
            }
            records.append(record)

        return records

    def extract_league_table(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract league standings"""
        sofascore = self._get_sofascore_reader(league, season)
        df = sofascore.read_league_table()

        return self._dataframe_to_dicts(df, league, season)

    def extract_schedule(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract match schedule"""
        sofascore = self._get_sofascore_reader(league, season)
        df = sofascore.read_schedule()

        return self._dataframe_to_dicts(df, league, season)
