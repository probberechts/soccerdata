#!/usr/bin/env python3
"""
Test script to verify each data source can extract data successfully.
Tests with a single league/season to minimize API calls and time.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_soccerdata_direct():
    """Test soccerdata library directly before testing our extractors"""
    print("="*80)
    print("PHASE 1: Testing soccerdata library directly")
    print("="*80)

    try:
        import soccerdata as sd
        print(f"\n✅ soccerdata v{sd.__version__} imported")
    except ImportError as e:
        print(f"\n❌ Failed to import soccerdata: {e}")
        return False

    # Test parameters
    test_league = "ENG-Premier League"
    test_season = "2324"

    sources = {
        'FBref': (sd.FBref, True),
        'FotMob': (sd.FotMob, True),
        'Understat': (sd.Understat, True),
        'Sofascore': (sd.Sofascore, True),
        'ESPN': (sd.ESPN, True),
        'WhoScored': (sd.WhoScored, True),
        'MatchHistory': (sd.MatchHistory, True),
        'ClubElo': (sd.ClubElo, False),  # ClubElo doesn't take league/season
        'SoFIFA': (sd.SoFIFA, True),
    }

    results = {}

    for name, (cls, needs_params) in sources.items():
        print(f"\n{name}:")
        print("-" * 40)

        try:
            # Instantiate
            if needs_params:
                scraper = cls(leagues=test_league, seasons=test_season)
            else:
                scraper = cls()

            print(f"  ✅ Instantiated successfully")

            # Try to read something (don't actually fetch data yet)
            methods = [m for m in dir(scraper) if m.startswith('read_')]
            print(f"  📚 Available methods: {len(methods)}")
            if methods:
                print(f"     Examples: {', '.join(methods[:3])}")

            results[name] = 'AVAILABLE'

        except Exception as e:
            print(f"  ❌ Failed: {type(e).__name__}: {str(e)[:100]}")
            results[name] = f'FAILED: {type(e).__name__}'

    # Summary
    print("\n" + "="*80)
    print("PHASE 1 SUMMARY")
    print("="*80)

    available = [k for k, v in results.items() if v == 'AVAILABLE']
    failed = [k for k, v in results.items() if v != 'AVAILABLE']

    print(f"\n✅ Available: {len(available)}/{len(sources)}")
    if available:
        for source in available:
            print(f"   • {source}")

    if failed:
        print(f"\n❌ Failed: {len(failed)}/{len(sources)}")
        for source in failed:
            print(f"   • {source}: {results[source]}")

    return len(failed) == 0


def test_our_extractors():
    """Test our custom extractor classes"""
    print("\n" + "="*80)
    print("PHASE 2: Testing our extractor classes")
    print("="*80)

    try:
        from scripts.utils import get_config_loader, DatabaseManager
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

        print("\n✅ All extractor imports successful")

    except ImportError as e:
        print(f"\n❌ Failed to import extractors: {e}")
        print("\n💡 This is expected if database dependencies (psycopg2) aren't installed")
        print("   The extractors require DatabaseManager which needs psycopg2")
        return False

    print("\n✅ Extractor classes are importable")
    print("   (Full testing requires database connection)")

    return True


def test_basic_extraction():
    """Test a simple data fetch without database"""
    print("\n" + "="*80)
    print("PHASE 3: Testing basic data extraction (no database)")
    print("="*80)

    try:
        import soccerdata as sd
        import pandas as pd

        print("\nAttempting to fetch FBref schedule for testing...")
        print("(This will make a real API call - may take 10-20 seconds)")

        # Use a recent season that should have data
        fbref = sd.FBref(leagues='ENG-Premier League', seasons='2324')

        print("  Fetching schedule...")
        df = fbref.read_schedule()

        print(f"  ✅ Successfully fetched {len(df)} matches")
        print(f"  📊 Columns: {list(df.columns)[:5]}...")

        if len(df) > 0:
            print(f"  📝 Sample match: {df.iloc[0]['home']} vs {df.iloc[0]['away']}")

        return True

    except Exception as e:
        print(f"  ❌ Failed: {type(e).__name__}: {e}")
        print("\n💡 This might be due to:")
        print("   • Network issues")
        print("   • Rate limiting")
        print("   • Website changes")
        print("   • Invalid league/season combination")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("SOCCERDATA EXTRACTION TEST SUITE")
    print("="*80)
    print("\nThis script will test:")
    print("  1. soccerdata library classes")
    print("  2. Our custom extractor imports")
    print("  3. Basic data extraction (1 API call)")

    input("\nPress Enter to continue...")

    # Phase 1: Test soccerdata directly
    phase1_ok = test_soccerdata_direct()

    # Phase 2: Test our extractors
    phase2_ok = test_our_extractors()

    # Phase 3: Test basic extraction (optional)
    print("\n" + "="*80)
    print("OPTIONAL: Test actual data fetching?")
    print("="*80)
    print("\nThis will make a real API call to FBref.")
    print("It's safe and respectful (uses caching), but may take 10-20 seconds.")

    response = input("\nRun extraction test? [y/N]: ").strip().lower()

    if response == 'y':
        phase3_ok = test_basic_extraction()
    else:
        print("\n⏭️  Skipping extraction test")
        phase3_ok = None

    # Final summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)

    print(f"\n{'✅' if phase1_ok else '❌'} Phase 1: soccerdata library classes")
    print(f"{'✅' if phase2_ok else '⚠️ '} Phase 2: Our extractor imports")
    if phase3_ok is not None:
        print(f"{'✅' if phase3_ok else '❌'} Phase 3: Basic data extraction")

    if phase1_ok and phase2_ok:
        print("\n" + "="*80)
        print("🎉 SUCCESS! Ready to run historical loader")
        print("="*80)
        print("\nNext steps:")
        print("  1. Configure your database in .env")
        print("  2. Run: python -m scripts.historical_loader")
        print("  3. Monitor logs in logs/ directory")
        return 0

    elif phase1_ok and not phase2_ok:
        print("\n" + "="*80)
        print("⚠️  PARTIAL SUCCESS")
        print("="*80)
        print("\nsoccerdata works, but extractor imports failed.")
        print("This is expected if psycopg2-binary is not installed.")
        print("\nTo fix:")
        print("  pip install -r requirements-database.txt")
        return 1

    else:
        print("\n" + "="*80)
        print("❌ ISSUES DETECTED")
        print("="*80)
        print("\nPlease share this output for diagnosis.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
