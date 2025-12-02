# SoccerData Import Issues - Investigation Report
**Date:** December 2, 2025
**Status:** Investigation Complete - Strategy Pending User Testing

---

## Executive Summary

You're experiencing `AttributeError` when trying to import classes from the soccerdata package:
- ❌ `AttributeError: module 'soccerdata' has no attribute 'FotMob'`
- ❌ `AttributeError: module 'soccerdata' has no attribute 'Understat'`
- ❌ `AttributeError: module 'soccerdata' has no attribute 'Sofascore'`
- ⚠️  `KeyError` with SoFIFA: "None of ['version_id'] are in the columns"

**Investigation Findings:**
- ✅ All three classes (FotMob, Understat, Sofascore) **ARE** included in soccerdata 1.8.7 (latest)
- ✅ These classes have been actively maintained throughout 2024-2025
- ✅ Documentation confirms they should work with `import soccerdata as sd; sd.FotMob(...)`
- ⚠️  **Root Cause: Likely version mismatch or import configuration issue**

---

## Web Research Findings

### 1. Package Information
**Source:** [PyPI - soccerdata](https://pypi.org/project/soccerdata/)

- **Latest Version:** 1.8.7 (released February 9, 2025)
- **Python Requirements:** 3.9 - 3.12
- **License:** Apache 2.0 / MIT

**Confirmed Available Classes:**
- ✅ ClubElo
- ✅ ESPN
- ✅ FBref
- ✅ FiveThirtyEight
- ✅ Football-Data.co.uk
- ✅ **FotMob**
- ✅ MatchHistory
- ✅ **Sofascore**
- ✅ SoFIFA
- ✅ **Understat**
- ✅ WhoScored

### 2. Official Documentation Import Pattern
**Source:** [soccerdata documentation](https://soccerdata.readthedocs.io/)

```python
import soccerdata as sd

# Instantiate scrapers
fotmob = sd.FotMob(leagues="ESP-La Liga", seasons="2022/2023")
understat = sd.Understat(leagues="ENG-Premier League", seasons="2324")
sofascore = sd.Sofascore(leagues="GER-Bundesliga", seasons="2324")

# Read data
league_table = fotmob.read_league_table()
schedule = fotmob.read_schedule()
match_stats = fotmob.read_team_match_stats()
```

### 3. Recent Version History & Breaking Changes
**Source:** [GitHub Releases](https://github.com/probberechts/soccerdata/releases)

#### Version Timeline (2024-2025)

| Version | Date | Key Changes |
|---------|------|-------------|
| **1.8.7** | Feb 9, 2025 | Bug fix for SoFIFA player ratings |
| **1.8.6** | Jan 21, 2025 | SoFIFA parsing updates |
| **1.8.5** | Jan 16, 2025 | MatchHistory encoding fixes |
| **1.8.4** | Nov 4, 2024 | **FotMob anti-scraping header patch** 🔧 |
| **1.8.3** | Oct 30, 2024 | Sofascore 2nd tier leagues, SoFIFA FIFA version fix |
| **1.8.2** | Aug 15, 2024 | **Understat enhancements** (assists, cards, etc.) |
| **1.8.1** | Jun 28, 2024 | WhoScored JavaScript fix |
| **1.8.0** | Jun 16, 2024 | European Championship support |

**Critical Finding:**
- ❌ **NO CLASSES WERE REMOVED** in any version
- ✅ FotMob, Understat, and Sofascore are actively maintained
- ⚠️  FotMob had API changes in Oct/Nov 2024 (Issue [#742](https://github.com/probberechts/soccerdata/issues/742))

### 4. Known Issues

**FotMob API Changes (October 2024)**
**Source:** [GitHub Issue #742](https://github.com/probberechts/soccerdata/issues/742)

- FotMob now requires `'x-fm-req'` header
- Fixed in v1.8.4 (November 4, 2024)
- **Impact:** If you have v1.8.3 or earlier, FotMob may fail with 401 Unauthorized

**General Warning from Documentation:**
> "As soccerdata relies on web scraping, any changes to the scraped websites will break the package. Hence, do not expect that all code will work all the time."

---

## Your Repository Context

### Current Setup
From your `requirements-database.txt`:
```txt
soccerdata>=1.7.0
```

**Minimum version:** 1.7.0
**Recommended:** >=1.8.4 (for FotMob fix)
**Latest:** 1.8.7

### Repository History
From git log, your repository was cleaned up on **November 29, 2025**:
- Removed original soccerdata source code (~70 files)
- Now uses soccerdata as a pip dependency
- Created 9 custom extractors that wrap soccerdata classes

---

## Possible Root Causes

### 1. ❌ **Outdated soccerdata Version** (Most Likely)
**Symptoms:** AttributeError when importing classes
**Cause:** Installed version < 1.7.0 or missing classes in old version
**Test:**
```bash
python -c "import soccerdata as sd; print(sd.__version__)"
```
**Fix:**
```bash
pip install --upgrade soccerdata>=1.8.4
```

### 2. ❌ **Virtual Environment Not Activated**
**Symptoms:** Package not found or wrong version
**Cause:** Running from system Python instead of .venv
**Test:**
```bash
which python
# Should show: /path/to/.venv/bin/python
```
**Fix:**
```bash
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows
```

### 3. ❌ **Corrupted Installation**
**Symptoms:** Package installed but classes missing
**Cause:** Interrupted installation or cache corruption
**Fix:**
```bash
pip uninstall soccerdata
pip cache purge
pip install soccerdata>=1.8.7
```

### 4. ❌ **Import Path Issues**
**Symptoms:** Wrong module being imported
**Cause:** Name collision or PYTHONPATH issues
**Test:**
```python
import soccerdata as sd
print(sd.__file__)
# Should show: .venv/lib/.../site-packages/soccerdata/__init__.py
```
**Fix:** Check for local `soccerdata/` directory that might shadow the package

### 5. ⚠️  **Submodule Import Required** (Less Likely)
**Symptoms:** `sd.FotMob` fails but direct import works
**Cause:** Classes not exported in `__init__.py`
**Test:**
```python
from soccerdata.fotmob import FotMob  # Alternative import
```

---

## SoFIFA KeyError Issue

**Error:** `KeyError: "None of ['version_id'] are in the columns"`

**Analysis:**
- Fixed in v1.8.7 (February 9, 2025): "Bug fix for SoFIFA player ratings"
- Also addressed in v1.8.3 (October 30, 2024): "Fixed SoFIFA FIFA version handling"

**Solution:** Upgrade to v1.8.7

---

## Action Plan

### Phase 1: Diagnostic (RUN FIRST)

Run the investigation script I created:

```bash
python investigate_soccerdata.py
```

This script will:
- ✅ Check if soccerdata is installed
- ✅ Display the installed version
- ✅ List all available classes
- ✅ Test for expected classes (FotMob, Understat, etc.)
- ✅ Try alternative import patterns
- ✅ Provide specific recommendations

**Expected Output:** A complete report showing what's available and what's missing.

### Phase 2: Fix Installation (Based on Diagnostic Results)

#### Option A: Upgrade soccerdata
```bash
pip install --upgrade soccerdata>=1.8.7
```

#### Option B: Clean Reinstall
```bash
pip uninstall soccerdata -y
pip cache purge
pip install soccerdata==1.8.7
```

#### Option C: Install from GitHub (Latest)
```bash
pip install git+https://github.com/probberechts/soccerdata.git
```

### Phase 3: Verify Fix

```bash
python -c "import soccerdata as sd; print('Version:', sd.__version__); print('FotMob:', hasattr(sd, 'FotMob')); print('Understat:', hasattr(sd, 'Understat')); print('Sofascore:', hasattr(sd, 'Sofascore'))"
```

**Expected Output:**
```
Version: 1.8.7
FotMob: True
Understat: True
Sofascore: True
```

### Phase 4: Test Extractors

```bash
python -m scripts.historical_loader
```

---

## If Classes Are Still Missing After Upgrade

If upgrading doesn't work, we have **two implementation paths**:

### Path A: Use Alternative Import Pattern

Update all extractors to use direct imports:

```python
# Instead of:
import soccerdata as sd
fotmob = sd.FotMob(...)

# Use:
from soccerdata.fotmob import FotMob
fotmob = FotMob(...)
```

**Pros:**
- ✅ Works if classes are in submodules
- ✅ More explicit
- ✅ Faster import time

**Cons:**
- ❌ Requires updating all 9 extractors
- ❌ Less consistent with documentation

### Path B: Implement Custom Scrapers with Playwright

If soccerdata classes are genuinely unavailable or broken, implement direct scraping:

**Required:**
```bash
pip install playwright pandas
playwright install chromium
```

**Implementation:** Create custom scraper classes that:
1. Use Playwright for browser automation
2. Extract data from websites directly
3. Return pandas DataFrames matching the expected schema
4. Include anti-detection measures (user agents, delays, stealth mode)

**Priority:**
1. FBref (likely works - test first)
2. Understat (valuable xG data)
3. FotMob (good for standings/schedules)
4. Others as needed

**Note:** Only pursue this if Path A fails. Direct scraping is more fragile and maintenance-heavy.

---

## Recommended Next Steps

1. **RUN DIAGNOSTIC SCRIPT**
   ```bash
   python investigate_soccerdata.py
   ```

2. **SHARE OUTPUT** - Send me the complete output so I can diagnose the exact issue

3. **TRY UPGRADE** - Based on diagnostic, upgrade soccerdata

4. **TEST IMPORT** - Verify classes are now available

5. **DECIDE PATH** - Based on results, choose:
   - ✅ Classes available → Test extractors
   - ⚠️  Still missing → Try alternative imports (Path A)
   - ❌ Completely broken → Implement custom scrapers (Path B)

---

## Sources

- [soccerdata on PyPI](https://pypi.org/project/soccerdata/)
- [soccerdata Documentation](https://soccerdata.readthedocs.io/)
- [soccerdata GitHub Repository](https://github.com/probberechts/soccerdata)
- [GitHub Releases](https://github.com/probberechts/soccerdata/releases)
- [FotMob API Issue #742](https://github.com/probberechts/soccerdata/issues/742)
- [FotMob Documentation](https://soccerdata.readthedocs.io/en/latest/datasources/FotMob.html)

---

## Summary

**Most Likely Issue:** Outdated or corrupted soccerdata installation

**Quick Fix:**
```bash
pip install --upgrade soccerdata==1.8.7
python investigate_soccerdata.py
```

**Next Steps:** Run diagnostic, share output, then proceed based on findings.

---

*Investigation completed. Awaiting user diagnostic results before proceeding with implementation strategy.*
