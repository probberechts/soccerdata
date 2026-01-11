#!/usr/bin/env python3
"""Simple test to verify MLS configuration without network dependencies."""

import soccerdata as sd
from soccerdata._config import LEAGUE_DICT

def test_mls_configuration():
    """Test MLS configuration without network calls."""
    print("Testing MLS configuration...")
    print("=" * 50)
    
    # Check if MLS is in available leagues
    available_leagues = sd.FBref.available_leagues()
    print(f"Available leagues: {available_leagues}")
    
    if "USA-Major League Soccer" in available_leagues:
        print("✅ MLS found in available leagues!")
    else:
        print("❌ MLS not found in available leagues")
        return False
    
    # Check the configuration details
    if "USA-Major League Soccer" in LEAGUE_DICT:
        mls_config = LEAGUE_DICT["USA-Major League Soccer"]
        print(f"\n✅ MLS Configuration found:")
        for key, value in mls_config.items():
            print(f"  {key}: {value}")
    else:
        print("❌ MLS configuration not found in LEAGUE_DICT")
        return False
    
    # Test basic FBref class instantiation (without network calls)
    try:
        # This should work without network calls since it just sets up the class
        fbref_class = sd.FBref
        print(f"\n✅ FBref class accessible: {fbref_class}")
        
        # Check if the league is recognized by the class
        if hasattr(fbref_class, 'available_leagues'):
            leagues = fbref_class.available_leagues()
            if "USA-Major League Soccer" in leagues:
                print("✅ MLS recognized by FBref class")
            else:
                print("❌ MLS not recognized by FBref class")
                return False
    except Exception as e:
        print(f"❌ Error with FBref class: {e}")
        return False
    
    print("\n🎉 All MLS configuration tests passed!")
    return True

if __name__ == "__main__":
    test_mls_configuration()