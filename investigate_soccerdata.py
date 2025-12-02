#!/usr/bin/env python3
"""
Investigation script to check what's available in the installed soccerdata package.
Run this in your .venv to diagnose the import issues.
"""

def investigate_soccerdata():
    """Comprehensive investigation of soccerdata package"""

    print("=" * 80)
    print("SOCCERDATA PACKAGE INVESTIGATION")
    print("=" * 80)

    # Step 1: Check if soccerdata is installed
    try:
        import soccerdata as sd
        print("\n✅ soccerdata package is installed")
    except ImportError as e:
        print(f"\n❌ soccerdata package is NOT installed: {e}")
        print("\nInstall with: pip install soccerdata>=1.7.0")
        return

    # Step 2: Check version
    try:
        version = sd.__version__
        print(f"📦 Version: {version}")
    except AttributeError:
        print("⚠️  Warning: Could not determine version (no __version__ attribute)")
        version = "unknown"

    # Step 3: Check package location
    try:
        import os
        package_path = os.path.dirname(sd.__file__)
        print(f"📁 Package location: {package_path}")
    except:
        print("⚠️  Warning: Could not determine package location")

    # Step 4: List all available attributes
    print("\n" + "=" * 80)
    print("AVAILABLE ATTRIBUTES (via dir(soccerdata))")
    print("=" * 80)

    all_attrs = dir(sd)
    public_attrs = [attr for attr in all_attrs if not attr.startswith('_')]

    print(f"\nTotal attributes: {len(all_attrs)}")
    print(f"Public attributes: {len(public_attrs)}\n")

    # Categorize attributes
    classes = []
    functions = []
    modules = []
    other = []

    for attr in public_attrs:
        try:
            obj = getattr(sd, attr)
            obj_type = type(obj).__name__

            if obj_type == 'type':
                classes.append(attr)
            elif obj_type in ('function', 'builtin_function_or_method'):
                functions.append(attr)
            elif obj_type == 'module':
                modules.append(attr)
            else:
                other.append((attr, obj_type))
        except Exception as e:
            other.append((attr, f"Error: {e}"))

    # Print classes (most important)
    print("CLASSES (Data Source Scrapers):")
    print("-" * 80)
    if classes:
        for cls in sorted(classes):
            print(f"  ✓ {cls}")
    else:
        print("  ⚠️  No classes found!")

    # Print other categories
    if functions:
        print(f"\nFUNCTIONS ({len(functions)}):")
        print("-" * 80)
        for func in sorted(functions):
            print(f"  • {func}")

    if modules:
        print(f"\nMODULES ({len(modules)}):")
        print("-" * 80)
        for mod in sorted(modules):
            print(f"  • {mod}")

    if other:
        print(f"\nOTHER ({len(other)}):")
        print("-" * 80)
        for name, obj_type in other:
            print(f"  • {name}: {obj_type}")

    # Step 5: Check for expected classes
    print("\n" + "=" * 80)
    print("EXPECTED DATA SOURCE CLASSES")
    print("=" * 80)

    expected_classes = [
        'FBref',
        'FotMob',
        'Understat',
        'WhoScored',
        'Sofascore',
        'ESPN',
        'ClubElo',
        'MatchHistory',
        'SoFIFA',
    ]

    print(f"\nChecking for {len(expected_classes)} expected scraper classes:\n")

    available = []
    missing = []

    for cls_name in expected_classes:
        try:
            cls = getattr(sd, cls_name, None)
            if cls is None:
                status = "❌ MISSING"
                missing.append(cls_name)
            else:
                status = "✅ AVAILABLE"
                available.append(cls_name)
                # Try to get class info
                try:
                    cls_file = cls.__module__
                    status += f" (from {cls_file})"
                except:
                    pass
        except AttributeError:
            status = "❌ MISSING (AttributeError)"
            missing.append(cls_name)

        print(f"  {cls_name:20s} {status}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Available: {len(available)}/{len(expected_classes)}")
    print(f"❌ Missing:   {len(missing)}/{len(expected_classes)}")

    if missing:
        print("\n⚠️  MISSING CLASSES:")
        for cls in missing:
            print(f"  • {cls}")

        print("\n🔧 POSSIBLE CAUSES:")
        print("  1. Outdated soccerdata version (current: {})".format(version))
        print("  2. Classes moved to submodules (need different import)")
        print("  3. Classes renamed in newer versions")
        print("  4. Installation corrupted")

        print("\n💡 SUGGESTED FIXES:")
        print("  1. Upgrade soccerdata: pip install --upgrade soccerdata")
        print("  2. Reinstall fresh: pip uninstall soccerdata && pip install soccerdata>=1.8.0")
        print("  3. Check if classes need submodule imports:")
        print("     from soccerdata.fotmob import FotMob")
        print("     from soccerdata.understat import Understat")
        print("     etc.")

    # Step 6: Try alternative import patterns
    print("\n" + "=" * 80)
    print("TESTING ALTERNATIVE IMPORT PATTERNS")
    print("=" * 80)

    test_imports = [
        ("from soccerdata import FotMob", "FotMob"),
        ("from soccerdata.fotmob import FotMob", "FotMob"),
        ("from soccerdata import Understat", "Understat"),
        ("from soccerdata.understat import Understat", "Understat"),
        ("from soccerdata import Sofascore", "Sofascore"),
        ("from soccerdata.sofascore import Sofascore", "Sofascore"),
    ]

    print("\nTrying different import patterns:\n")

    for import_stmt, class_name in test_imports:
        try:
            # Try to execute the import
            exec(import_stmt)
            print(f"  ✅ {import_stmt}")
        except ImportError as e:
            print(f"  ❌ {import_stmt}")
            print(f"     Error: {e}")
        except Exception as e:
            print(f"  ⚠️  {import_stmt}")
            print(f"     Unexpected error: {e}")

    print("\n" + "=" * 80)
    print("INVESTIGATION COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review the findings above")
    print("2. If classes are missing, try upgrading soccerdata")
    print("3. If alternative imports work, update extractor files")
    print("4. Share this output with the development team")
    print()


if __name__ == "__main__":
    investigate_soccerdata()
