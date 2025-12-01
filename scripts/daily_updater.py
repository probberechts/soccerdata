"""
Daily Update Script
Updates football statistics data for the current season (structure only)
"""

import argparse
import sys
from datetime import datetime
from typing import List, Optional

from .orchestrator import Orchestrator


class DailyUpdater:
    """
    Updates data for the current season daily
    """

    def __init__(
        self,
        config_dir: str = "config",
        log_dir: str = "logs",
    ):
        """
        Initialize daily updater

        Args:
            config_dir: Path to configuration directory
            log_dir: Path to log directory
        """
        self.orchestrator = Orchestrator(
            config_dir=config_dir,
            log_dir=log_dir,
        )

    @staticmethod
    def get_current_season() -> str:
        """
        Get current season identifier based on today's date

        Returns:
            Season identifier (e.g., '2425' for 2024-2025 season)
        """
        now = datetime.now()
        year = now.year

        # Football seasons typically run from August to May
        # If we're in Jan-July, we're in the second half of the season
        if now.month < 8:
            # Season started last year
            start_year = year - 1
        else:
            # Season started this year
            start_year = year

        # Generate season ID (YYZZ format)
        year_str = str(start_year)[-2:]
        next_year_str = str(start_year + 1)[-2:]
        return f"{year_str}{next_year_str}"

    def run_daily_update(
        self,
        data_sources: Optional[List[str]] = None,
        leagues: Optional[List[str]] = None,
        season: Optional[str] = None,
    ):
        """
        Run daily update for current season

        Args:
            data_sources: List of data sources (None = all enabled)
            leagues: List of leagues (None = all configured)
            season: Season to update (None = auto-detect current season)

        Returns:
            Summary of extraction results
        """
        # Auto-detect season if not provided
        if season is None:
            season = self.get_current_season()

        self.orchestrator.logger.logger.info(
            f"Running daily update for season: {season}"
        )

        # Run extraction for current season
        # Note: skip_completed=False to ensure we get latest data
        return self.orchestrator.run_extraction(
            data_sources=data_sources,
            leagues=leagues,
            seasons=[season],
            skip_completed=False,  # Always re-fetch to get latest updates
        )


def main():
    """Main entry point for daily updater"""
    parser = argparse.ArgumentParser(
        description="Daily update of football statistics data"
    )

    parser.add_argument(
        '--season',
        help='Season to update (default: auto-detect current season)',
    )

    parser.add_argument(
        '--sources',
        nargs='+',
        help='Data sources to update (default: all enabled)',
    )

    parser.add_argument(
        '--leagues',
        nargs='+',
        help='Leagues to update (default: all configured)',
    )

    parser.add_argument(
        '--config-dir',
        default='config',
        help='Configuration directory (default: config)',
    )

    parser.add_argument(
        '--log-dir',
        default='logs',
        help='Log directory (default: logs)',
    )

    args = parser.parse_args()

    try:
        # Create updater
        updater = DailyUpdater(
            config_dir=args.config_dir,
            log_dir=args.log_dir,
        )

        # Run daily update
        summary = updater.run_daily_update(
            data_sources=args.sources,
            leagues=args.leagues,
            season=args.season,
        )

        # Exit with appropriate code
        if summary['total_failed'] > 0:
            print(f"\nWarning: {summary['total_failed']} tasks failed")
            sys.exit(1)
        else:
            print(f"\nSuccess: {summary['total_completed']} tasks completed")
            sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
