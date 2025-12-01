"""
ClubElo Data Extractor
Extracts data from ClubElo into 2 database tables
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import soccerdata as sd

from .base_extractor import BaseExtractor
from ..utils import DatabaseManager, DataExtractionLogger, ConfigLoader


class ClubEloExtractor(BaseExtractor):
    """
    Extracts ELO ratings from ClubElo

    Handles 2 tables:
    - clubelo_ratings_by_date
    - clubelo_team_history
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        config_loader: ConfigLoader,
        logger: Optional[DataExtractionLogger] = None,
    ):
        """Initialize ClubElo extractor"""
        super().__init__(
            data_source='clubelo',
            db_manager=db_manager,
            config_loader=config_loader,
            logger=logger,
        )

    def get_table_configs(self) -> List[Dict[str, Any]]:
        """Get configuration for all 2 ClubElo tables"""
        return [
            {
                'table_name': 'clubelo_ratings_by_date',
                'extraction_method': 'extract_ratings_by_date',
                'conflict_columns': ['team', 'date'],
                'required_fields': ['team', 'date', 'data_source'],
            },
            {
                'table_name': 'clubelo_team_history',
                'extraction_method': 'extract_team_history',
                'conflict_columns': ['team', 'date'],
                'required_fields': ['team', 'date', 'data_source'],
            },
        ]

    def extract_data(
        self,
        table_config: Dict[str, Any],
        league: str,
        season: str,
    ) -> List[Dict[str, Any]]:
        """Extract data for a specific ClubElo table"""
        extraction_method = table_config['extraction_method']
        method = getattr(self, extraction_method)
        return method(league, season)

    def _get_clubelo_reader(self) -> sd.ClubElo:
        """Get configured ClubElo reader instance"""
        return sd.ClubElo()

    def _dataframe_to_dicts(
        self,
        df: pd.DataFrame,
    ) -> List[Dict[str, Any]]:
        """Convert pandas DataFrame to list of dictionaries"""
        if df.empty:
            return []

        df_reset = df.reset_index()
        df_reset.columns = [
            col.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
            for col in df_reset.columns
        ]

        df_reset['data_source'] = 'clubelo'

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

    def extract_ratings_by_date(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract ELO ratings by date"""
        clubelo = self._get_clubelo_reader()

        # ClubElo doesn't filter by league/season in the same way
        # We extract all data and can filter later if needed
        df = clubelo.read_by_date()

        return self._dataframe_to_dicts(df)

    def extract_team_history(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract team ELO history"""
        # This method extracts team-specific history
        # For now, we'll extract a limited dataset
        # In practice, you may want to specify teams from config
        self.logger.logger.info(
            "ClubElo team_history requires specific team names. "
            "Returning empty for bulk extraction."
        )
        return []
