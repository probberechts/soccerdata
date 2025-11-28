"""
ESPN Data Extractor
Extracts data from ESPN into 3 database tables
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import soccerdata as sd

from .base_extractor import BaseExtractor
from scripts.utils import DatabaseManager, DataExtractionLogger, ConfigLoader


class ESPNExtractor(BaseExtractor):
    """
    Extracts football statistics from ESPN

    Handles 3 tables:
    - espn_schedule
    - espn_matchsheet
    - espn_lineup
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        config_loader: ConfigLoader,
        logger: Optional[DataExtractionLogger] = None,
    ):
        """Initialize ESPN extractor"""
        super().__init__(
            data_source='espn',
            db_manager=db_manager,
            config_loader=config_loader,
            logger=logger,
        )

    def get_table_configs(self) -> List[Dict[str, Any]]:
        """Get configuration for all 3 ESPN tables"""
        return [
            {
                'table_name': 'espn_schedule',
                'extraction_method': 'extract_schedule',
                'conflict_columns': ['league', 'season', 'game'],
                'required_fields': ['league', 'season', 'game', 'data_source'],
            },
            {
                'table_name': 'espn_matchsheet',
                'extraction_method': 'extract_matchsheet',
                'conflict_columns': ['league', 'season', 'game', 'team'],
                'required_fields': ['league', 'season', 'game', 'team', 'data_source'],
            },
            {
                'table_name': 'espn_lineup',
                'extraction_method': 'extract_lineup',
                'conflict_columns': ['league', 'season', 'game', 'team', 'player'],
                'required_fields': ['league', 'season', 'game', 'team', 'player', 'data_source'],
            },
        ]

    def extract_data(
        self,
        table_config: Dict[str, Any],
        league: str,
        season: str,
    ) -> List[Dict[str, Any]]:
        """Extract data for a specific ESPN table"""
        extraction_method = table_config['extraction_method']
        method = getattr(self, extraction_method)
        return method(league, season)

    def _get_espn_reader(self, league: str, season: str) -> sd.ESPN:
        """Get configured ESPN reader instance"""
        soccerdata_league = self.get_soccerdata_league_id(league)

        if not soccerdata_league:
            raise ValueError(f"No soccerdata ID found for league: {league}")

        return sd.ESPN(leagues=soccerdata_league, seasons=season)

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
        df_reset['data_source'] = 'espn'

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

    def extract_schedule(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract match schedule"""
        espn = self._get_espn_reader(league, season)
        df = espn.read_schedule()

        return self._dataframe_to_dicts(df, league, season)

    def extract_matchsheet(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract match statistics"""
        espn = self._get_espn_reader(league, season)

        try:
            df = espn.read_matchsheet()
            return self._dataframe_to_dicts(df, league, season)
        except Exception as e:
            self.logger.logger.warning(
                f"No matchsheet data available for {league} {season}: {e}"
            )
            return []

    def extract_lineup(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract match lineups"""
        espn = self._get_espn_reader(league, season)

        try:
            df = espn.read_lineup()
            return self._dataframe_to_dicts(df, league, season)
        except Exception as e:
            self.logger.logger.warning(
                f"No lineup data available for {league} {season}: {e}"
            )
            return []
