"""
Master Orchestrator
Coordinates data extraction from all sources
"""

import argparse
import sys
from typing import List, Optional, Dict, Any
from datetime import datetime

from scripts.utils import (
    DatabaseManager,
    ConfigLoader,
    DataExtractionLogger,
    get_config_loader,
)
from scripts.extractors import (
    FBrefExtractor,
    FotMobExtractor,
    UnderstatExtractor,
    WhoScoredExtractor,
    SofascoreExtractor,
    ESPNExtractor,
    ClubEloExtractor,
    MatchHistoryExtractor,
    SoFIFAExtractor,
)


class Orchestrator:
    """
    Orchestrates data extraction across all data sources
    """

    # Map data source names to extractor classes
    EXTRACTOR_MAP = {
        'fbref': FBrefExtractor,
        'fotmob': FotMobExtractor,
        'understat': UnderstatExtractor,
        'whoscored': WhoScoredExtractor,
        'sofascore': SofascoreExtractor,
        'espn': ESPNExtractor,
        'clubelo': ClubEloExtractor,
        'matchhistory': MatchHistoryExtractor,
        'sofifa': SoFIFAExtractor,
    }

    def __init__(
        self,
        config_dir: str = "config",
        log_dir: str = "logs",
    ):
        """
        Initialize orchestrator

        Args:
            config_dir: Path to configuration directory
            log_dir: Path to log directory
        """
        # Load configuration
        self.config_loader = get_config_loader(config_dir)
        logging_config = self.config_loader.get_logging_config()

        # Setup logging
        self.logger = DataExtractionLogger(
            "orchestrator",
            log_dir=logging_config.get('log_dir', log_dir),
        )

        # Setup database connection
        db_config = self.config_loader.get_database_config()
        self.db_manager = DatabaseManager(**db_config)

        # Test database connection
        if not self.db_manager.test_connection():
            raise ConnectionError("Failed to connect to database")

        self.logger.logger.info("Orchestrator initialized successfully")

    def get_extractor(self, data_source: str):
        """
        Get extractor instance for a data source

        Args:
            data_source: Name of data source

        Returns:
            Extractor instance
        """
        extractor_class = self.EXTRACTOR_MAP.get(data_source)

        if not extractor_class:
            raise ValueError(f"Unknown data source: {data_source}")

        return extractor_class(
            db_manager=self.db_manager,
            config_loader=self.config_loader,
            logger=self.logger,
        )

    def run_extraction(
        self,
        data_sources: Optional[List[str]] = None,
        leagues: Optional[List[str]] = None,
        seasons: Optional[List[str]] = None,
        skip_completed: bool = True,
    ) -> Dict[str, Any]:
        """
        Run data extraction

        Args:
            data_sources: List of data sources to extract (None = all enabled)
            leagues: List of leagues to extract (None = all configured)
            seasons: List of seasons to extract
            skip_completed: Whether to skip already-completed extractions

        Returns:
            Summary of extraction results
        """
        start_time = datetime.now()

        # Determine data sources to extract
        if data_sources is None:
            data_sources = self.config_loader.get_enabled_data_sources()

        # Determine leagues to extract
        if leagues is None:
            leagues = self.config_loader.get_all_leagues()

        if not seasons:
            raise ValueError("Seasons must be provided")

        self.logger.logger.info(
            f"Starting orchestrated extraction: "
            f"{len(data_sources)} sources, {len(leagues)} leagues, {len(seasons)} seasons"
        )

        # Track results
        all_results = {}
        source_summaries = {}

        # Extract from each data source
        for source_name in data_sources:
            self.logger.logger.info(f"=" * 80)
            self.logger.logger.info(f"Processing data source: {source_name}")
            self.logger.logger.info(f"=" * 80)

            try:
                # Get extractor for this source
                extractor = self.get_extractor(source_name)

                # Run extraction
                results = extractor.extract_all(
                    leagues=leagues,
                    seasons=seasons,
                    skip_completed=skip_completed,
                )

                # Store results
                all_results[source_name] = results

                # Calculate summary
                completed = sum(1 for r in results if r['status'] == 'completed')
                failed = sum(1 for r in results if r['status'] == 'failed')
                skipped = sum(1 for r in results if r['status'] == 'skipped')
                total_rows = sum(r.get('rows', 0) for r in results)

                source_summaries[source_name] = {
                    'total_tasks': len(results),
                    'completed': completed,
                    'failed': failed,
                    'skipped': skipped,
                    'total_rows': total_rows,
                }

                self.logger.logger.info(
                    f"Completed {source_name}: {completed} succeeded, "
                    f"{failed} failed, {skipped} skipped, {total_rows} rows"
                )

            except Exception as e:
                self.logger.logger.error(
                    f"Error processing {source_name}: {e}",
                    exc_info=True,
                )
                source_summaries[source_name] = {
                    'error': str(e),
                }

        # Overall summary
        duration = (datetime.now() - start_time).total_seconds()

        summary = {
            'start_time': start_time,
            'end_time': datetime.now(),
            'duration_seconds': duration,
            'data_sources': source_summaries,
            'total_completed': sum(
                s.get('completed', 0) for s in source_summaries.values()
            ),
            'total_failed': sum(
                s.get('failed', 0) for s in source_summaries.values()
            ),
            'total_skipped': sum(
                s.get('skipped', 0) for s in source_summaries.values()
            ),
            'total_rows': sum(
                s.get('total_rows', 0) for s in source_summaries.values()
            ),
        }

        self.logger.logger.info("=" * 80)
        self.logger.logger.info("EXTRACTION COMPLETE")
        self.logger.logger.info("=" * 80)
        self.logger.logger.info(f"Duration: {duration:.1f}s")
        self.logger.logger.info(f"Completed: {summary['total_completed']}")
        self.logger.logger.info(f"Failed: {summary['total_failed']}")
        self.logger.logger.info(f"Skipped: {summary['total_skipped']}")
        self.logger.logger.info(f"Total rows: {summary['total_rows']}")

        return summary


def main():
    """Main entry point for orchestrator"""
    parser = argparse.ArgumentParser(
        description="Orchestrate football statistics data extraction"
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
        '--seasons',
        nargs='+',
        required=True,
        help='Seasons to extract (e.g., 2021 2122 2223)',
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
        # Create orchestrator
        orchestrator = Orchestrator(
            config_dir=args.config_dir,
            log_dir=args.log_dir,
        )

        # Run extraction
        summary = orchestrator.run_extraction(
            data_sources=args.sources,
            leagues=args.leagues,
            seasons=args.seasons,
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
