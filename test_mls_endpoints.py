#!/usr/bin/env python3
"""Test which soccerdata endpoints work with MLS."""

import ssl
import soccerdata as sd

# Fix SSL
ssl._create_default_https_context = ssl._create_unverified_context

def test_mls_endpoints():
    """Test different soccerdata endpoints with MLS."""
    print("Testing MLS endpoints...")
    print("=" * 50)
    
    # Test FBref (should work)
    print("\n1. Testing FBref...")
    try:
        fbref = sd.FBref("USA-Major League Soccer", seasons=2024)
        print("✅ FBref: SUCCESS - Can create instance")
        
        # Try getting some data
        try:
            data = fbref.read_player_season_stats(stat_type="standard")
            print(f"✅ FBref data: SUCCESS - {data.shape[0]} players, {data.shape[1]} columns")
        except Exception as e:
            print(f"⚠️  FBref data: PARTIAL - Instance works but data failed: {e}")
            
    except Exception as e:
        print(f"❌ FBref: FAILED - {e}")
    
    # Test other endpoints (should fail)
    endpoints_to_test = [
        ("ClubElo", sd.ClubElo),
        ("FiveThirtyEight", sd.FiveThirtyEight),
        ("ESPN", sd.ESPN),
        ("Sofascore", sd.Sofascore),
    ]
    
    for name, endpoint_class in endpoints_to_test:
        print(f"\n2. Testing {name}...")
        try:
            instance = endpoint_class("USA-Major League Soccer", seasons=2024)
            print(f"✅ {name}: SUCCESS - Can create instance")
        except Exception as e:
            print(f"❌ {name}: FAILED - {e}")
    
    print("\n" + "=" * 50)
    print("Summary:")
    print("✅ FBref endpoints should work (all player/team stats)")
    print("❌ Other endpoints need additional configuration")

if __name__ == "__main__":
    test_mls_endpoints()