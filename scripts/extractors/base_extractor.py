"""
Base Extractor Abstract Class
Defines common interface and shared functionality for all data source extractors
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import time
import traceback

from ..utils import (
    DatabaseManager,
    DataExtractionLogger,
    ConfigLoader,
    DataValidator,
    retry_with_rate_limit,
)


class BaseExtractor(ABC):
    """
    Abstract base class for all data source extractors

    Provides:
    - Common initialization and configuration
    - Database connection management
    - Progress tracking via data_load_status table
    - Error handling and logging
    - Template methods for extraction workflow
    """

    def __init__(
        self,
        data_source: str,
        db_manager: DatabaseManager,
        config_loader: ConfigLoader,
        logger: Optional[DataExtractionLogger] = None,
    ):
        """
        Initialize base extractor

        Args:
            data_source: Data source identifier (e.g., 'fbref', 'fotmob')
            db_manager: Database manager instance
            config_loader: Configuration loader instance
            logger: Logger instance (creates new if not provided)
        """
        self.data_source = data_source
        self.db_manager = db_manager
        self.config_loader = config_loader
        self.logger = logger or DataExtractionLogger(f"extractor.{data_source}")

        # Load retry and rate limit configuration
        retry_config = config_loader.get_retry_config()
        rate_limit_config = config_loader.get_rate_limit_config()

        self.retry_config = retry_config
        self.rate_limit_config = rate_limit_config

        # Validator instance
        self.validator = DataValidator()

    @abstractmethod
    def get_table_configs(self) -> List[Dict[str, Any]]:
        """
        Get configuration for all tables this extractor handles

        Returns:
            List of table configurations with structure:
            [
                {
                    'table_name': 'fbref_schedule',
                    'extraction_method': 'read_schedule',
                    'conflict_columns': ['league', 'season', 'game'],
                    'required_fields': ['league', 'season', 'game', 'date'],
                },
                ...
            ]
        """
        pass

    @abstractmethod
    def extract_data(
        self,
        table_config: Dict[str, Any],
        league: str,
        season: str,
    ) -> List[Dict[str, Any]]:
        """
        Extract data for a specific table, league, and season

        Args:
            table_config: Table configuration from get_table_configs()
            league: League name (e.g., 'ENG-Premier League')
            season: Season identifier (e.g., '2021')

        Returns:
            List of data dictionaries ready for database insertion
        """
        pass

    def get_soccerdata_league_id(self, league: str) -> Optional[str]:
        """
        Convert standardized league name to soccerdata library ID

        Args:
            league: Standardized league name (e.g., 'ENG-Premier League')

        Returns:
            Soccerdata league ID or None
        """
        return self.config_loader.get_league_soccerdata_id(league)

    def should_skip(self, table_name: str, league: str, season: str) -> bool:
        """
        Check if extraction should be skipped (already completed)

        Args:
            table_name: Name of the table
            league: League name
            season: Season identifier

        Returns:
            True if should skip, False otherwise
        """
        status = self.db_manager.get_load_status(
            data_source=self.data_source,
            table_name=table_name,
            league=league,
            season=season,
        )

        if status and status.get('status') == 'completed':
            self.logger.skip_existing(self.data_source, league, season)
            return True

        return False

    def mark_in_progress(self, table_name: str, league: str, season: str):
        """
        Mark extraction as in progress

        Args:
            table_name: Name of the table
            league: League name
            season: Season identifier
        """
        self.db_manager.update_load_status(
            data_source=self.data_source,
            table_name=table_name,
            league=league,
            season=season,
            status='in_progress',
            started_at=datetime.now(),
        )

    def mark_completed(
        self,
        table_name: str,
        league: str,
        season: str,
        rows_processed: int,
    ):
        """
        Mark extraction as completed

        Args:
            table_name: Name of the table
            league: League name
            season: Season identifier
            rows_processed: Number of rows processed
        """
        self.db_manager.update_load_status(
            data_source=self.data_source,
            table_name=table_name,
            league=league,
            season=season,
            status='completed',
            rows_processed=rows_processed,
            completed_at=datetime.now(),
        )

    def mark_failed(
        self,
        table_name: str,
        league: str,
        season: str,
        error_message: str,
    ):
        """
        Mark extraction as failed

        Args:
            table_name: Name of the table
            league: League name
            season: Season identifier
            error_message: Error message
        """
        self.db_manager.update_load_status(
            data_source=self.data_source,
            table_name=table_name,
            league=league,
            season=season,
            status='failed',
            error_message=error_message,
        )

    def validate_data(
        self,
        data: List[Dict[str, Any]],
        table_config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Validate extracted data

        Args:
            data: List of data dictionaries
            table_config: Table configuration

        Returns:
            List of valid data dictionaries
        """
        if not data:
            return []

        required_fields = table_config.get('required_fields', [])

        valid_data, invalid_data = self.validator.validate_batch(
            data=data,
            required_fields=required_fields,
        )

        if invalid_data:
            self.logger.logger.warning(
                f"Filtered out {len(invalid_data)} invalid records from {len(data)} total"
            )

        return valid_data

    def insert_data(
        self,
        table_name: str,
        data: List[Dict[str, Any]],
        conflict_columns: List[str],
    ) -> int:
        """
        Insert data into database with UPSERT logic

        Args:
            table_name: Name of the table
            data: List of data dictionaries
            conflict_columns: Columns that define uniqueness for UPSERT

        Returns:
            Number of rows affected
        """
        if not data:
            self.logger.logger.info(f"No data to insert for {table_name}")
            return 0

        self.logger.table_insert_start(table_name, len(data))

        try:
            # Get all columns from first record
            columns = list(data[0].keys())

            # Update columns are all columns except conflict columns and created_at
            update_columns = [
                col for col in columns
                if col not in conflict_columns and col != 'created_at'
            ]

            rows_affected = self.db_manager.bulk_insert(
                table_name=table_name,
                columns=columns,
                data=data,
                conflict_columns=conflict_columns,
                update_columns=update_columns,
            )

            self.logger.table_insert_complete(table_name, rows_affected)
            return rows_affected

        except Exception as e:
            self.logger.table_insert_error(table_name, e)
            raise

    def extract_and_load(
        self,
        table_config: Dict[str, Any],
        league: str,
        season: str,
        skip_completed: bool = True,
    ) -> Dict[str, Any]:
        """
        Complete extraction and loading workflow for one table/league/season

        Args:
            table_config: Table configuration
            league: League name
            season: Season identifier
            skip_completed: Whether to skip already-completed extractions

        Returns:
            Dictionary with extraction results
        """
        table_name = table_config['table_name']

        # Check if should skip
        if skip_completed and self.should_skip(table_name, league, season):
            return {
                'table': table_name,
                'league': league,
                'season': season,
                'status': 'skipped',
                'rows': 0,
            }

        # Mark as in progress
        self.mark_in_progress(table_name, league, season)
        self.logger.extraction_start(self.data_source, league, season)

        start_time = time.time()

        try:
            # Extract data
            data = self.extract_data(table_config, league, season)

            # Validate data
            valid_data = self.validate_data(data, table_config)

            # Insert into database
            rows_affected = self.insert_data(
                table_name=table_name,
                data=valid_data,
                conflict_columns=table_config.get('conflict_columns', []),
            )

            # Mark as completed
            duration = time.time() - start_time
            self.mark_completed(table_name, league, season, rows_affected)
            self.logger.extraction_complete(
                self.data_source, league, season, rows_affected, duration
            )

            return {
                'table': table_name,
                'league': league,
                'season': season,
                'status': 'completed',
                'rows': rows_affected,
                'duration': duration,
            }

        except Exception as e:
            duration = time.time() - start_time
            error_message = f"{str(e)}\n{traceback.format_exc()}"

            self.mark_failed(table_name, league, season, error_message)
            self.logger.extraction_error(self.data_source, league, season, e)

            return {
                'table': table_name,
                'league': league,
                'season': season,
                'status': 'failed',
                'error': str(e),
                'duration': duration,
            }

    def extract_all(
        self,
        leagues: Optional[List[str]] = None,
        seasons: Optional[List[str]] = None,
        skip_completed: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Extract all tables for all leagues and seasons

        Args:
            leagues: List of leagues to extract (None = all configured leagues)
            seasons: List of seasons to extract (None = must be provided)
            skip_completed: Whether to skip already-completed extractions

        Returns:
            List of extraction result dictionaries
        """
        # Get leagues from config if not provided
        if leagues is None:
            leagues = self.config_loader.get_all_leagues()

        if seasons is None:
            raise ValueError("Seasons must be provided")

        # Get table configurations
        table_configs = self.get_table_configs()

        results = []
        total_tasks = len(table_configs) * len(leagues) * len(seasons)
        current_task = 0

        self.logger.logger.info(
            f"Starting extraction for {self.data_source}: "
            f"{len(table_configs)} tables, {len(leagues)} leagues, "
            f"{len(seasons)} seasons ({total_tasks} total tasks)"
        )

        # Iterate through all combinations
        for table_config in table_configs:
            for league in leagues:
                for season in seasons:
                    current_task += 1
                    self.logger.progress_update(
                        current_task, total_tasks, "tasks"
                    )

                    result = self.extract_and_load(
                        table_config=table_config,
                        league=league,
                        season=season,
                        skip_completed=skip_completed,
                    )
                    results.append(result)

        # Summary
        completed = sum(1 for r in results if r['status'] == 'completed')
        failed = sum(1 for r in results if r['status'] == 'failed')
        skipped = sum(1 for r in results if r['status'] == 'skipped')
        total_rows = sum(r.get('rows', 0) for r in results)

        self.logger.logger.info(
            f"Extraction complete for {self.data_source}: "
            f"{completed} completed, {failed} failed, {skipped} skipped, "
            f"{total_rows} total rows"
        )

        return results

    def test_connection(self) -> bool:
        """
        Test database connection

        Returns:
            True if connection successful
        """
        return self.db_manager.test_connection()

    def get_extraction_status(
        self,
        league: Optional[str] = None,
        season: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get extraction status for this data source

        Args:
            league: Filter by league (None = all leagues)
            season: Filter by season (None = all seasons)

        Returns:
            List of status records
        """
        return self.db_manager.get_load_status(
            data_source=self.data_source,
            league=league,
            season=season,
        )
