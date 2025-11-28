"""
Logging Configuration Module
Provides structured logging with file and console handlers
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


def setup_logger(
    name: str,
    log_dir: str = "logs",
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_to_console: bool = True
) -> logging.Logger:
    """
    Set up a logger with file and console handlers

    Args:
        name: Logger name (typically __name__ of the module)
        log_dir: Directory to store log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_to_console: Whether to log to console

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Create log file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d')
        log_file = log_path / f"{name.replace('.', '_')}_{timestamp}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with default settings

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return setup_logger(name)


class DataExtractionLogger:
    """
    Specialized logger for data extraction operations
    Provides methods for common logging patterns
    """

    def __init__(self, name: str, log_dir: str = "logs"):
        self.logger = setup_logger(name, log_dir=log_dir)
        self.name = name

    def extraction_start(self, data_source: str, league: str, season: str):
        """Log start of extraction"""
        self.logger.info(
            f"Starting extraction - Source: {data_source}, League: {league}, Season: {season}"
        )

    def extraction_complete(
        self,
        data_source: str,
        league: str,
        season: str,
        records: int,
        duration: float
    ):
        """Log successful extraction completion"""
        self.logger.info(
            f"Extraction complete - Source: {data_source}, League: {league}, "
            f"Season: {season}, Records: {records}, Duration: {duration:.2f}s"
        )

    def extraction_error(
        self,
        data_source: str,
        league: str,
        season: str,
        error: Exception
    ):
        """Log extraction error"""
        self.logger.error(
            f"Extraction failed - Source: {data_source}, League: {league}, "
            f"Season: {season}, Error: {str(error)}",
            exc_info=True
        )

    def table_insert_start(self, table_name: str, record_count: int):
        """Log start of database insertion"""
        self.logger.info(f"Inserting {record_count} records into {table_name}")

    def table_insert_complete(self, table_name: str, rows_affected: int):
        """Log successful database insertion"""
        self.logger.info(f"Inserted/updated {rows_affected} rows in {table_name}")

    def table_insert_error(self, table_name: str, error: Exception):
        """Log database insertion error"""
        self.logger.error(
            f"Failed to insert into {table_name}: {str(error)}",
            exc_info=True
        )

    def retry_attempt(self, attempt: int, max_attempts: int, error: str):
        """Log retry attempt"""
        self.logger.warning(
            f"Retry attempt {attempt}/{max_attempts} - Error: {error}"
        )

    def api_rate_limit(self, wait_time: float):
        """Log rate limit handling"""
        self.logger.warning(f"Rate limit reached, waiting {wait_time:.1f}s")

    def skip_existing(self, data_source: str, league: str, season: str):
        """Log skipping already-processed data"""
        self.logger.info(
            f"Skipping - Source: {data_source}, League: {league}, "
            f"Season: {season} (already completed)"
        )

    def validation_error(self, field: str, value: any, reason: str):
        """Log data validation error"""
        self.logger.warning(
            f"Validation error - Field: {field}, Value: {value}, Reason: {reason}"
        )

    def progress_update(self, current: int, total: int, item_type: str):
        """Log progress update"""
        percentage = (current / total * 100) if total > 0 else 0
        self.logger.info(
            f"Progress: {current}/{total} {item_type} ({percentage:.1f}%)"
        )
