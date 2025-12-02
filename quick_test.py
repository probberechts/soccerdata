#!/usr/bin/env python3
"""Quick test to check soccerdata installation and available classes"""

print("Testing soccerdata installation...\n")

# Test 1: Import
try:
    import soccerdata as sd
    print("✅ soccerdata imported successfully")
except ImportError as e:
    print(f"❌ FAILED to import soccerdata: {e}")
    print("\n💡 Fix: pip install soccerdata>=1.8.7")
    exit(1)

# Test 2: Version
try:
    version = sd.__version__
    print(f"📦 Version: {version}")

    # Check if version is recent enough
    version_parts = version.split('.')
    major = int(version_parts[0])
    minor = int(version_parts[1]) if len(version_parts) > 1 else 0

    if major < 1 or (major == 1 and minor < 8):
        print(f"⚠️  WARNING: Version {version} is old. Recommend upgrading to 1.8.7+")
        print("   Run: pip install --upgrade soccerdata>=1.8.7")
except Exception as e:
    print(f"⚠️  Could not determine version: {e}")

# Test 3: Check for expected classes
print("\nTesting class availability:")

classes_to_test = {
    'FBref': '✅ FBref (Premier League stats)',
    'FotMob': '✅ FotMob (schedules, standings)',
    'Understat': '✅ Understat (xG data)',
    'WhoScored': '✅ WhoScored (Opta events)',
    'Sofascore': '✅ Sofascore (match data)',
    'ESPN': '✅ ESPN (general stats)',
    'ClubElo': '✅ ClubElo (ratings)',
    'MatchHistory': '✅ MatchHistory (betting odds)',
    'SoFIFA': '✅ SoFIFA (player ratings)',
}

available = []
missing = []

for class_name, description in classes_to_test.items():
    if hasattr(sd, class_name):
        print(f"  {description}")
        available.append(class_name)
    else:
        print(f"  ❌ {class_name} NOT FOUND")
        missing.append(class_name)

# Summary
print(f"\n{'='*60}")
print(f"SUMMARY: {len(available)}/{len(classes_to_test)} classes available")
print(f"{'='*60}")

if missing:
    print(f"\n⚠️  MISSING CLASSES: {', '.join(missing)}")
    print("\n💡 POSSIBLE FIXES:")
    print("   1. Upgrade: pip install --upgrade soccerdata>=1.8.7")
    print("   2. Reinstall: pip uninstall soccerdata && pip install soccerdata")
    print("   3. Run full diagnostic: python investigate_soccerdata.py")
    exit(1)
else:
    print("\n✅ All expected classes are available!")
    print("✅ You should be able to run the extractors now")
    print("\nNext step: python -m scripts.historical_loader")
    exit(0)
