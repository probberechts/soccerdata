"""
Configuration Loader Module
Loads configuration from YAML files and environment variables
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """
    Loads and manages configuration from YAML files and environment variables
    """

    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration loader

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self.config_cache: Dict[str, Any] = {}

        # Load environment variables from .env file
        load_dotenv()

    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file

        Args:
            filename: Name of the YAML file (with or without .yaml extension)

        Returns:
            Configuration dictionary
        """
        # Add .yaml extension if not present
        if not filename.endswith(('.yaml', '.yml')):
            filename = f"{filename}.yaml"

        # Check cache first
        if filename in self.config_cache:
            return self.config_cache[filename]

        # Load from file
        config_path = self.config_dir / filename

        if not config_path.exists():
            logger.warning(f"Configuration file not found: {config_path}")
            return {}

        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}

            # Cache the configuration
            self.config_cache[filename] = config
            logger.info(f"Loaded configuration from {config_path}")
            return config

        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            return {}

    def get_database_config(self) -> Dict[str, Any]:
        """
        Get database configuration from environment variables

        Returns:
            Database configuration dictionary
        """
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'football_stats'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
        }

    def get_data_sources_config(self) -> Dict[str, Any]:
        """
        Get data sources configuration

        Returns:
            Data sources configuration dictionary
        """
        return self.load_yaml('data_sources')

    def get_leagues_config(self) -> List[Dict[str, Any]]:
        """
        Get leagues configuration

        Returns:
            List of league configurations
        """
        config = self.load_yaml('leagues')
        return config.get('leagues', [])

    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration

        Returns:
            Logging configuration dictionary
        """
        config = self.load_yaml('logging')

        # Set defaults if not specified
        return {
            'log_level': config.get('log_level', 'INFO'),
            'log_dir': config.get('log_dir', 'logs'),
            'log_to_file': config.get('log_to_file', True),
            'log_to_console': config.get('log_to_console', True),
        }

    def get_extraction_config(self) -> Dict[str, Any]:
        """
        Get extraction configuration

        Returns:
            Extraction configuration dictionary
        """
        data_sources = self.get_data_sources_config()
        return data_sources.get('extraction', {})

    def get_retry_config(self) -> Dict[str, Any]:
        """
        Get retry configuration for API calls

        Returns:
            Retry configuration dictionary
        """
        extraction_config = self.get_extraction_config()
        return extraction_config.get('retry', {
            'max_attempts': 3,
            'initial_delay': 2,
            'max_delay': 60,
            'exponential_base': 2,
        })

    def get_rate_limit_config(self) -> Dict[str, Any]:
        """
        Get rate limiting configuration

        Returns:
            Rate limit configuration dictionary
        """
        extraction_config = self.get_extraction_config()
        return extraction_config.get('rate_limiting', {
            'enabled': True,
            'requests_per_minute': 20,
            'delay_between_requests': 3,
        })

    def get_historical_loader_config(self) -> Dict[str, Any]:
        """
        Get historical loader configuration

        Returns:
            Historical loader configuration dictionary
        """
        return {
            'start_season': os.getenv('START_SEASON', '2021'),
            'end_season': os.getenv('END_SEASON', '2425'),
            'batch_size': int(os.getenv('BATCH_SIZE', '100')),
            'parallel_workers': int(os.getenv('PARALLEL_WORKERS', '1')),
            'skip_completed': os.getenv('SKIP_COMPLETED', 'true').lower() == 'true',
        }

    def get_data_source_enabled(self, source_name: str) -> bool:
        """
        Check if a data source is enabled

        Args:
            source_name: Name of the data source (e.g., 'fbref', 'fotmob')

        Returns:
            True if enabled, False otherwise
        """
        data_sources = self.get_data_sources_config()
        sources = data_sources.get('sources', {})
        source_config = sources.get(source_name, {})
        return source_config.get('enabled', True)

    def get_data_source_priority(self, source_name: str) -> int:
        """
        Get priority order for a data source

        Args:
            source_name: Name of the data source

        Returns:
            Priority number (lower = higher priority)
        """
        data_sources = self.get_data_sources_config()
        sources = data_sources.get('sources', {})
        source_config = sources.get(source_name, {})
        return source_config.get('priority', 999)

    def get_enabled_data_sources(self) -> List[str]:
        """
        Get list of enabled data sources sorted by priority

        Returns:
            List of enabled data source names
        """
        data_sources = self.get_data_sources_config()
        sources = data_sources.get('sources', {})

        # Filter enabled sources and sort by priority
        enabled = [
            (name, config.get('priority', 999))
            for name, config in sources.items()
            if config.get('enabled', True)
        ]

        # Sort by priority and return names only
        enabled.sort(key=lambda x: x[1])
        return [name for name, _ in enabled]

    def get_league_soccerdata_id(self, league_name: str) -> Optional[str]:
        """
        Get soccerdata library league ID for a league

        Args:
            league_name: Standardized league name (e.g., 'ENG-Premier League')

        Returns:
            Soccerdata league ID or None
        """
        leagues = self.get_leagues_config()
        for league in leagues:
            if league.get('name') == league_name:
                return league.get('soccerdata_id')
        return None

    def get_all_leagues(self) -> List[str]:
        """
        Get list of all configured league names

        Returns:
            List of standardized league names
        """
        leagues = self.get_leagues_config()
        return [league.get('name') for league in leagues if league.get('enabled', True)]

    def reload_config(self, filename: Optional[str] = None):
        """
        Reload configuration from file(s)

        Args:
            filename: Specific file to reload, or None to reload all
        """
        if filename:
            # Remove from cache to force reload
            if filename in self.config_cache:
                del self.config_cache[filename]
        else:
            # Clear entire cache
            self.config_cache.clear()

        logger.info(f"Configuration cache cleared{' for ' + filename if filename else ''}")


# Global instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader(config_dir: str = "config") -> ConfigLoader:
    """
    Get global ConfigLoader instance (singleton pattern)

    Args:
        config_dir: Directory containing configuration files

    Returns:
        ConfigLoader instance
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(config_dir)
    return _config_loader
