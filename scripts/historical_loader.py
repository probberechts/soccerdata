"""
Historical Data Loader
Loads historical football statistics data for multiple seasons
"""

import argparse
import sys
from typing import List, Optional
from datetime import datetime

from scripts.orchestrator import Orchestrator


class HistoricalLoader:
    """
    Loads historical data across multiple seasons
    """

    def __init__(
        self,
        config_dir: str = "config",
        log_dir: str = "logs",
    ):
        """
        Initialize historical loader

        Args:
            config_dir: Path to configuration directory
            log_dir: Path to log directory
        """
        self.orchestrator = Orchestrator(
            config_dir=config_dir,
            log_dir=log_dir,
        )

    @staticmethod
    def generate_season_range(start_year: int, end_year: int) -> List[str]:
        """
        Generate list of season identifiers

        Args:
            start_year: Start year (e.g., 2020 for 2020-2021 season)
            end_year: End year (e.g., 2024 for 2024-2025 season)

        Returns:
            List of season identifiers (e.g., ['2021', '2122', '2223', '2324', '2425'])
        """
        seasons = []

        for year in range(start_year, end_year + 1):
            # Use 4-digit format for first year, 2-digit format for subsequent
            if year == start_year:
                # First season uses 4-digit year
                seasons.append(str(year + 1))
            else:
                # Subsequent seasons use 2-digit format (YYZZ)
                year_str = str(year)[-2:]
                next_year_str = str(year + 1)[-2:]
                seasons.append(f"{year_str}{next_year_str}")

        return seasons

    def load_historical_data(
        self,
        start_year: int = 2020,
        end_year: int = 2024,
        data_sources: Optional[List[str]] = None,
        leagues: Optional[List[str]] = None,
        skip_completed: bool = True,
    ):
        """
        Load historical data for a range of seasons

        Args:
            start_year: Start year (default: 2020 for 2020-2021 season)
            end_year: End year (default: 2024 for 2024-2025 season)
            data_sources: List of data sources (None = all enabled)
            leagues: List of leagues (None = all configured)
            skip_completed: Whether to skip already-completed data

        Returns:
            Summary of extraction results
        """
        # Generate season list
        seasons = self.generate_season_range(start_year, end_year)

        self.orchestrator.logger.logger.info(
            f"Loading historical data for seasons: {seasons}"
        )

        # Run extraction using orchestrator
        return self.orchestrator.run_extraction(
            data_sources=data_sources,
            leagues=leagues,
            seasons=seasons,
            skip_completed=skip_completed,
        )


def main():
    """Main entry point for historical loader"""
    parser = argparse.ArgumentParser(
        description="Load historical football statistics data"
    )

    parser.add_argument(
        '--start-year',
        type=int,
        default=2020,
        help='Start year (default: 2020 for 2020-2021 season)',
    )

    parser.add_argument(
        '--end-year',
        type=int,
        default=2024,
        help='End year (default: 2024 for 2024-2025 season)',
    )

    parser.add_argument(
        '--sources',
        nargs='+',
        help='Data sources to extract (default: all enabled)',
    )

    parser.add_argument(
        '--leagues',
        nargs='+',
        help='Leagues to extract (default: all configured)',
    )

    parser.add_argument(
        '--no-skip-completed',
        action='store_true',
        help='Re-extract already completed data',
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
        # Create loader
        loader = HistoricalLoader(
            config_dir=args.config_dir,
            log_dir=args.log_dir,
        )

        # Load historical data
        summary = loader.load_historical_data(
            start_year=args.start_year,
            end_year=args.end_year,
            data_sources=args.sources,
            leagues=args.leagues,
            skip_completed=not args.no_skip_completed,
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
