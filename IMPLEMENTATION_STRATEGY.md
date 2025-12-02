# Implementation Strategy - Data Source Fixes

**Status:** Awaiting diagnostic results before proceeding
**Priority:** Determine root cause before implementing fixes

---

## Decision Tree

```
START: AttributeError when importing FotMob, Understat, Sofascore
  │
  ├─→ Run: python quick_test.py
  │
  ├─→ CASE 1: Version < 1.8.7
  │   └─→ ACTION: Upgrade soccerdata
  │       └─→ pip install --upgrade soccerdata>=1.8.7
  │       └─→ Test: python quick_test.py
  │       └─→ SUCCESS → Test extractors
  │       └─→ FAIL → Go to CASE 3
  │
  ├─→ CASE 2: Classes available but extractors fail
  │   └─→ ACTION: Debug extractor implementation
  │       └─→ Check league IDs mapping
  │       └─→ Check method signatures
  │       └─→ Check DataFrame schema expectations
  │       └─→ Fix API changes (headers, parameters, etc.)
  │
  ├─→ CASE 3: Classes NOT available even after upgrade
  │   └─→ ACTION: Use alternative import pattern
  │       └─→ Implement Strategy A (see below)
  │       └─→ Test: python quick_test.py
  │       └─→ SUCCESS → Update all extractors
  │       └─→ FAIL → Go to CASE 4
  │
  └─→ CASE 4: Classes completely unavailable/broken
      └─→ ACTION: Implement custom scrapers
          └─→ Implement Strategy B (see below)
          └─→ High effort, high maintenance
```

---

## Strategy A: Alternative Import Pattern

**When to use:** If classes exist in submodules but not exposed via `sd.ClassName`

### Changes Required

Update all 9 extractors to use direct imports from submodules.

#### Example: FotMob Extractor

**Current (scripts/extractors/fotmob_extractor.py):**
```python
import soccerdata as sd

class FotMobExtractor(BaseExtractor):
    def _get_fotmob_reader(self, league: str, season: str):
        return sd.FotMob(leagues=league, seasons=season)
```

**Updated:**
```python
from soccerdata.fotmob import FotMob

class FotMobExtractor(BaseExtractor):
    def _get_fotmob_reader(self, league: str, season: str):
        return FotMob(leagues=league, seasons=season)
```

#### Files to Update

1. **scripts/extractors/fbref_extractor.py**
   - `from soccerdata.fbref import FBref`

2. **scripts/extractors/fotmob_extractor.py**
   - `from soccerdata.fotmob import FotMob`

3. **scripts/extractors/understat_extractor.py**
   - `from soccerdata.understat import Understat`

4. **scripts/extractors/whoscored_extractor.py**
   - `from soccerdata.whoscored import WhoScored`

5. **scripts/extractors/sofascore_extractor.py**
   - `from soccerdata.sofascore import Sofascore`

6. **scripts/extractors/espn_extractor.py**
   - `from soccerdata.espn import ESPN`

7. **scripts/extractors/clubelo_extractor.py**
   - `from soccerdata.clubelo import ClubElo`

8. **scripts/extractors/matchhistory_extractor.py**
   - `from soccerdata.matchhistory import MatchHistory`

9. **scripts/extractors/sofifa_extractor.py**
   - `from soccerdata.sofifa import SoFIFA`

### Pros
- ✅ More explicit imports
- ✅ Faster import time (only load needed modules)
- ✅ Works even if `__init__.py` doesn't export classes

### Cons
- ❌ Different from official documentation
- ❌ Requires updating all 9 extractors

### Implementation Estimate
- Time: 30 minutes
- Risk: Low
- Effort: Low

---

## Strategy B: Custom Playwright Scrapers

**When to use:** ONLY if soccerdata classes are completely unavailable or permanently broken

### Prerequisites

```bash
pip install playwright pandas beautifulsoup4 httpx
playwright install chromium
```

### Architecture

Create custom scraper classes that mimic soccerdata API:

```python
from playwright.async_api import async_playwright
import pandas as pd
import asyncio
import random
import time

class CustomFotMobScraper:
    """
    Custom FotMob scraper using Playwright
    Mimics soccerdata.FotMob API
    """

    def __init__(self, leagues: str, seasons: str, proxy=None, no_cache=False):
        self.leagues = leagues
        self.seasons = seasons
        self.proxy = proxy
        self.no_cache = no_cache
        self.base_url = "https://www.fotmob.com"

        # Anti-detection measures
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
            # Add more user agents
        ]

    async def read_league_table(self) -> pd.DataFrame:
        """Extract league table data"""
        async with async_playwright() as p:
            browser = await self._launch_browser(p)
            page = await browser.new_page()

            # Random delay to avoid detection
            await asyncio.sleep(random.uniform(1, 3))

            # Navigate to league page
            league_url = f"{self.base_url}/leagues/{self._get_league_id()}"
            await page.goto(league_url, wait_until='networkidle')

            # Extract data (implementation specific to FotMob structure)
            data = await page.evaluate('''() => {
                // JavaScript to extract table data
                const rows = document.querySelectorAll('.league-table-row');
                return Array.from(rows).map(row => ({
                    team: row.querySelector('.team-name').textContent,
                    played: row.querySelector('.played').textContent,
                    // ... extract all fields
                }));
            }''')

            await browser.close()

            # Convert to DataFrame
            df = pd.DataFrame(data)
            return df

    async def _launch_browser(self, p):
        """Launch browser with anti-detection measures"""
        return await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )

    def _get_random_user_agent(self):
        return random.choice(self.user_agents)

    def _get_league_id(self):
        """Map league name to FotMob league ID"""
        mapping = {
            'ESP-La Liga': '87',
            'ENG-Premier League': '47',
            # ... add all leagues
        }
        return mapping.get(self.leagues, '')
```

### Anti-Detection Measures

1. **User Agent Rotation**
   ```python
   USER_AGENTS = [
       'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
       'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
       'Mozilla/5.0 (X11; Linux x86_64)...',
   ]
   ```

2. **Rate Limiting**
   ```python
   class RateLimiter:
       def __init__(self, requests_per_minute=20):
           self.rpm = requests_per_minute
           self.requests = []

       async def wait_if_needed(self):
           now = time.time()
           # Remove old requests
           self.requests = [t for t in self.requests if now - t < 60]

           if len(self.requests) >= self.rpm:
               sleep_time = 60 - (now - self.requests[0])
               if sleep_time > 0:
                   await asyncio.sleep(sleep_time)

           self.requests.append(now)
   ```

3. **Random Delays**
   ```python
   await asyncio.sleep(random.uniform(1, 5))  # 1-5 second random delay
   ```

4. **Stealth Mode**
   ```python
   # Use playwright-stealth or custom scripts
   await page.add_init_script('''
       Object.defineProperty(navigator, 'webdriver', {
           get: () => undefined
       });
   ''')
   ```

5. **Proxy Support (Optional)**
   ```python
   browser = await p.chromium.launch(
       proxy={'server': 'http://proxy:port'}
   )
   ```

### Implementation Priority

If Strategy B is needed, implement in this order:

1. **HIGH PRIORITY**
   - ✅ FBref (test first - likely works)
   - 🔧 Understat (xG data - very valuable)
   - 🔧 FotMob (standings, schedules)

2. **MEDIUM PRIORITY**
   - ESPN
   - ClubElo (simpler, likely works)
   - MatchHistory (betting odds)
   - WhoScored (complex - uses Selenium)

3. **LOW PRIORITY**
   - Sofascore
   - SoFIFA (player ratings)

### Pros
- ✅ Full control over scraping logic
- ✅ Can adapt to site changes quickly
- ✅ Can implement custom anti-detection

### Cons
- ❌ High implementation effort (weeks)
- ❌ High maintenance burden
- ❌ Fragile (breaks when sites change)
- ❌ May violate terms of service
- ❌ Risk of IP bans

### Implementation Estimate
- Time: 2-4 weeks (all 9 sources)
- Risk: High
- Effort: Very High
- Maintenance: Ongoing

---

## Strategy C: Hybrid Approach

**Recommended:** Use soccerdata where it works, implement custom scrapers only where needed

### Assessment Process

1. **Test each data source individually:**
   ```bash
   python -c "import soccerdata as sd; fbref = sd.FBref('ENG-Premier League', '2324'); print(fbref.read_schedule())"
   ```

2. **Categorize results:**
   - ✅ **WORKING:** Use soccerdata as-is
   - ⚠️  **FIXABLE:** Minor API changes needed
   - ❌ **BROKEN:** Implement custom scraper

3. **Implement fixes only where needed**

### Expected Results (Based on Research)

| Data Source | Status | Action |
|-------------|--------|--------|
| FBref | ✅ Likely working | Test, use as-is |
| FotMob | ⚠️  Fixed in v1.8.4 | Upgrade soccerdata |
| Understat | ✅ Enhanced in v1.8.2 | Test, use as-is |
| Sofascore | ✅ Active in v1.8.3 | Test, use as-is |
| WhoScored | ⚠️  Selenium issues | May need custom impl |
| ESPN | ✅ Likely working | Test, use as-is |
| ClubElo | ✅ Likely working | Test, use as-is |
| MatchHistory | ✅ Fixed in v1.8.5 | Test, use as-is |
| SoFIFA | ⚠️  Fixed in v1.8.7 | Upgrade soccerdata |

---

## Recommended Action Plan

### Step 1: Diagnostic (5 minutes)
```bash
# Pull latest changes
git pull origin claude/football-stats-database-01DhdDWj8RkC4XFifkttt7oi

# Run quick test
python quick_test.py
```

### Step 2: Fix Installation (10 minutes)
```bash
# Upgrade soccerdata
pip install --upgrade soccerdata==1.8.7

# Verify fix
python quick_test.py
```

### Step 3: Test Extractors (30 minutes)

Create a simple test script:
```python
# test_extractors.py
import soccerdata as sd

test_league = "ENG-Premier League"
test_season = "2324"

# Test each source
sources = {
    'FBref': sd.FBref,
    'FotMob': sd.FotMob,
    'Understat': sd.Understat,
    'Sofascore': sd.Sofascore,
    'ESPN': sd.ESPN,
    'ClubElo': sd.ClubElo,
    'MatchHistory': sd.MatchHistory,
    'WhoScored': sd.WhoScored,
}

for name, cls in sources.items():
    try:
        if name == 'ClubElo':
            scraper = cls()
        else:
            scraper = cls(leagues=test_league, seasons=test_season)
        print(f"✅ {name}: instantiated successfully")

        # Try to read something
        if hasattr(scraper, 'read_schedule'):
            df = scraper.read_schedule()
            print(f"   → read_schedule(): {len(df)} rows")
    except Exception as e:
        print(f"❌ {name}: {type(e).__name__}: {e}")
```

### Step 4: Decide Next Steps (Based on Test Results)

- **All working:** ✅ Proceed with historical loader
- **Some broken:** Fix individually using Strategy A or B
- **All broken:** Investigate further (unlikely)

---

## Deliverables Checklist

### Phase 1: Investigation ✅
- [x] Research PyPI and documentation
- [x] Check version history and breaking changes
- [x] Create investigation script
- [x] Create quick test script
- [x] Document findings in INVESTIGATION_REPORT.md
- [x] Create implementation strategy

### Phase 2: Diagnostic (Pending User Action)
- [ ] User runs quick_test.py
- [ ] User shares diagnostic output
- [ ] Identify root cause
- [ ] Choose implementation strategy

### Phase 3: Implementation (Pending Phase 2)
- [ ] Implement chosen strategy (A, B, or C)
- [ ] Update all affected extractors
- [ ] Add anti-detection measures (if needed)
- [ ] Create comprehensive test suite
- [ ] Update documentation

### Phase 4: Testing (Pending Phase 3)
- [ ] Test individual extractors
- [ ] Test orchestrator
- [ ] Test historical loader with small dataset
- [ ] Verify data quality and schema
- [ ] Performance testing

### Phase 5: Documentation (Pending Phase 4)
- [ ] Update DATA_SOURCES.md
- [ ] Update requirements-database.txt
- [ ] Update README.md with known issues
- [ ] Document rate limits and restrictions
- [ ] Create troubleshooting guide

---

## Next Steps - REQUIRED FROM USER

**🔴 BLOCKING: Need diagnostic results to proceed**

Please run:
```bash
python quick_test.py
```

Share the complete output, then I can:
1. Identify exact root cause
2. Choose appropriate strategy
3. Implement fixes
4. Test and verify

**Estimated time after diagnostic:**
- Strategy A: 1 hour implementation + 1 hour testing
- Strategy B: 2-4 weeks implementation + ongoing maintenance
- Strategy C: Variable (most likely scenario)

---

*Strategy document complete. Awaiting user diagnostic results.*
