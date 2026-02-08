#!/usr/bin/env python3
"""Test to get GCA data for MLS."""

import soccerdata as sd

def test_mls_gca():
    """Test getting GCA data for MLS."""
    print("Testing MLS GCA data retrieval...")
    print("=" * 50)
    
    try:
        # Create FBref instance for MLS
        print("Creating FBref instance for MLS...")
        fbref = sd.FBref("USA-Major League Soccer", seasons=2024)
        print(f"✅ Successfully created FBref instance")
        print(f"League: {fbref.league}")
        print(f"Seasons: {fbref.seasons}")
        
        # Try to get GCA data
        print("\nAttempting to retrieve GCA data...")
        gca_data = fbref.read_player_season_stats(stat_type="gca")
        
        print(f"✅ Successfully retrieved GCA data!")
        print(f"Data shape: {gca_data.shape}")
        print(f"Columns: {list(gca_data.columns)}")
        
        # Show first few rows
        if not gca_data.empty:
            print(f"\nFirst 5 rows:")
            print(gca_data.head())
        else:
            print("⚠️  Data is empty")
        
        return True
        
    except Exception as e:
        print(f"❌ Error retrieving GCA data: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    test_mls_gca()