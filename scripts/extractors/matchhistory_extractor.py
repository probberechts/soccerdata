"""
MatchHistory Data Extractor
Extracts betting odds data from MatchHistory into 1 database table
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import soccerdata as sd

from .base_extractor import BaseExtractor
from scripts.utils import DatabaseManager, DataExtractionLogger, ConfigLoader


class MatchHistoryExtractor(BaseExtractor):
    """
    Extracts betting odds from MatchHistory

    Handles 1 table:
    - matchhistory_odds
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        config_loader: ConfigLoader,
        logger: Optional[DataExtractionLogger] = None,
    ):
        """Initialize MatchHistory extractor"""
        super().__init__(
            data_source='matchhistory',
            db_manager=db_manager,
            config_loader=config_loader,
            logger=logger,
        )

    def get_table_configs(self) -> List[Dict[str, Any]]:
        """Get configuration for the MatchHistory table"""
        return [
            {
                'table_name': 'matchhistory_odds',
                'extraction_method': 'extract_odds',
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
        """Extract data for MatchHistory table"""
        extraction_method = table_config['extraction_method']
        method = getattr(self, extraction_method)
        return method(league, season)

    def _get_matchhistory_reader(self, league: str, season: str) -> sd.MatchHistory:
        """Get configured MatchHistory reader instance"""
        soccerdata_league = self.get_soccerdata_league_id(league)

        if not soccerdata_league:
            raise ValueError(f"No soccerdata ID found for league: {league}")

        return sd.MatchHistory(leagues=soccerdata_league, seasons=season)

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
        df_reset['data_source'] = 'matchhistory'

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

    def extract_odds(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract betting odds data"""
        matchhistory = self._get_matchhistory_reader(league, season)

        try:
            df = matchhistory.read_games()
            return self._dataframe_to_dicts(df, league, season)
        except Exception as e:
            self.logger.logger.warning(
                f"No betting odds data available for {league} {season}: {e}"
            )
            return []
