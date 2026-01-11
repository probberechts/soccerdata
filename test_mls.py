#!/usr/bin/env python3
"""Test script to check if MLS configuration is working."""

import soccerdata as sd

def test_mls_availability():
    """Test if MLS is available in the league list."""
    print("Testing MLS availability...")
    
    # Check if MLS is in available leagues
    available_leagues = sd.FBref.available_leagues()
    print(f"Available leagues: {available_leagues}")
    
    if "USA-Major League Soccer" in available_leagues:
        print("✅ MLS found in available leagues!")
        return True
    else:
        print("❌ MLS not found in available leagues")
        return False

def test_mls_data_access():
    """Test if we can create an FBref instance for MLS."""
    print("\nTesting MLS data access...")
    
    try:
        # Try to create FBref instance for MLS
        fbref = sd.FBref("USA-Major League Soccer", seasons=2024)
        print("✅ Successfully created FBref instance for MLS!")
        
        # Try to get some basic info
        print(f"League: {fbref.league}")
        print(f"Seasons: {fbref.seasons}")
        
        # Check if the league configuration is properly loaded
        from soccerdata._config import LEAGUE_DICT
        if "USA-Major League Soccer" in LEAGUE_DICT:
            mls_config = LEAGUE_DICT["USA-Major League Soccer"]
            print(f"MLS Configuration: {mls_config}")
        
        return True
    except Exception as e:
        print(f"❌ Error creating FBref instance: {e}")
        return False

if __name__ == "__main__":
    print("Testing MLS configuration in soccerdata...")
    print("=" * 50)
    
    # Test availability
    available = test_mls_availability()
    
    if available:
        # Test data access
        test_mls_data_access()
    
    print("\nTest completed!")