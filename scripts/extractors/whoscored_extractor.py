"""
WhoScored Data Extractor
Extracts data from WhoScored into 4 database tables
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import soccerdata as sd

from .base_extractor import BaseExtractor
from ..utils import DatabaseManager, DataExtractionLogger, ConfigLoader


class WhoScoredExtractor(BaseExtractor):
    """
    Extracts detailed Opta event stream data from WhoScored

    Handles 4 tables:
    - whoscored_leagues, whoscored_seasons
    - whoscored_schedule
    - whoscored_events
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        config_loader: ConfigLoader,
        logger: Optional[DataExtractionLogger] = None,
    ):
        """Initialize WhoScored extractor"""
        super().__init__(
            data_source='whoscored',
            db_manager=db_manager,
            config_loader=config_loader,
            logger=logger,
        )

    def get_table_configs(self) -> List[Dict[str, Any]]:
        """
        Get configuration for all 4 WhoScored tables

        Returns:
            List of table configurations
        """
        return [
            {
                'table_name': 'whoscored_leagues',
                'extraction_method': 'extract_leagues',
                'conflict_columns': ['league'],
                'required_fields': ['league', 'data_source'],
            },
            {
                'table_name': 'whoscored_seasons',
                'extraction_method': 'extract_seasons',
                'conflict_columns': ['league', 'season'],
                'required_fields': ['league', 'season', 'data_source'],
            },
            {
                'table_name': 'whoscored_schedule',
                'extraction_method': 'extract_schedule',
                'conflict_columns': ['league', 'season', 'game'],
                'required_fields': ['league', 'season', 'game', 'data_source'],
            },
            {
                'table_name': 'whoscored_events',
                'extraction_method': 'extract_events',
                'conflict_columns': ['league', 'season', 'game', 'event_id'],
                'required_fields': ['league', 'season', 'game', 'event_id', 'data_source'],
            },
        ]

    def extract_data(
        self,
        table_config: Dict[str, Any],
        league: str,
        season: str,
    ) -> List[Dict[str, Any]]:
        """Extract data for a specific WhoScored table"""
        extraction_method = table_config['extraction_method']
        method = getattr(self, extraction_method)
        return method(league, season)

    def _get_whoscored_reader(self, league: str, season: str):
        """Get configured WhoScored reader instance"""
        soccerdata_league = self.get_soccerdata_league_id(league)

        if not soccerdata_league:
            raise ValueError(f"No soccerdata ID found for league: {league}")

        return sd.WhoScored(leagues=soccerdata_league, seasons=season)

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
        df_reset['data_source'] = 'whoscored'

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
        whoscored = self._get_whoscored_reader(league, season)
        df = whoscored.read_leagues()

        records = []
        for league_name, row in df.iterrows():
            record = {
                'league': league_name,
                'data_source': 'whoscored',
                'league_id': row.get('league_id'),
                'url': row.get('url'),
            }
            records.append(record)

        return records

    def extract_seasons(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract season metadata"""
        whoscored = self._get_whoscored_reader(league, season)
        df = whoscored.read_seasons()

        records = []
        for (league_name, season_name), row in df.iterrows():
            record = {
                'league': league_name,
                'season': season_name,
                'data_source': 'whoscored',
                'season_id': row.get('season_id'),
                'url': row.get('url'),
            }
            records.append(record)

        return records

    def extract_schedule(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract match schedule"""
        whoscored = self._get_whoscored_reader(league, season)
        df = whoscored.read_schedule()

        return self._dataframe_to_dicts(df, league, season)

    def extract_events(self, league: str, season: str) -> List[Dict[str, Any]]:
        """Extract detailed Opta event stream data"""
        whoscored = self._get_whoscored_reader(league, season)

        try:
            df = whoscored.read_events()
            return self._dataframe_to_dicts(df, league, season)
        except Exception as e:
            self.logger.logger.warning(
                f"No events data available for {league} {season}: {e}"
            )
            return []
