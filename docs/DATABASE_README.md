# Football Statistics PostgreSQL Database

Comprehensive PostgreSQL database for football statistics from 9 data sources covering 82+ tables.

## Quick Start

1. **Setup Database:**
   ```bash
   # Create database and tables
   cat schema/*.sql | psql -U postgres football_stats
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt -r requirements-database.txt
   ```

3. **Configure:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Load Data:**
   ```bash
   python -m scripts.historical_loader
   ```

## Documentation

- **[Setup Guide](SETUP.md)** - Complete installation and configuration
- **[Extraction Guide](EXTRACTION_GUIDE.md)** - How to extract data
- **[Data Sources](DATA_SOURCES.md)** - Information about each source
- **[Troubleshooting](TROUBLESHOOTING.md)** - Common issues and solutions

## Database Overview

### Schema

**82+ tables across 9 data sources:**

| Source | Tables | Focus |
|--------|--------|-------|
| FBref | 44 | Comprehensive Opta statistics |
| FotMob | 11 | League tables, match stats |
| Understat | 7 | xG metrics, shot coordinates |
| WhoScored | 4 | Detailed event stream |
| Sofascore | 4 | Schedules, standings |
| ESPN | 3 | Lineups, matchsheets |
| ClubElo | 2 | ELO ratings |
| MatchHistory | 1 | Betting odds (13+ bookmakers) |
| SoFIFA | 6 | EA Sports FC ratings |

### Coverage

- **Leagues:** Premier League, La Liga, Bundesliga, Serie A, Ligue 1
- **Seasons:** 2020-2021 onwards
- **Data Types:** Match stats, player stats, events, shots, lineups, odds, ratings

## Architecture

```
soccerdata/
├── schema/              # PostgreSQL DDL scripts (12 files)
│   ├── 00_database_setup.sql
│   ├── 01_common_types.sql
│   ├── 02_fbref_tables.sql
│   └── ...
├── scripts/
│   ├── utils/           # Core utilities
│   │   ├── db_manager.py
│   │   ├── logger.py
│   │   ├── config_loader.py
│   │   └── ...
│   ├── extractors/      # Data source extractors (9 extractors)
│   │   ├── fbref_extractor.py
│   │   ├── fotmob_extractor.py
│   │   └── ...
│   ├── orchestrator.py  # Master coordinator
│   ├── historical_loader.py
│   └── daily_updater.py
├── config/              # YAML configuration
│   ├── data_sources.yaml
│   ├── leagues.yaml
│   └── logging.yaml
└── docs/                # Documentation
    ├── SETUP.md
    ├── EXTRACTION_GUIDE.md
    └── DATA_SOURCES.md
```

## Key Features

### Comprehensive Data Model

- **All major statistics:** Goals, assists, xG, shots, passes, tackles, etc.
- **Event-level data:** Match events with coordinates
- **Advanced metrics:** PPDA, xG, progressive carries
- **Betting data:** Odds from 13+ bookmakers
- **EA Sports ratings:** Player potential and attributes

### Automated Extraction

- **Orchestrator:** Coordinates extraction from all sources
- **Historical Loader:** Bulk load multiple seasons
- **Daily Updater:** Keep current season up to date
- **Error Handling:** Automatic retry with exponential backoff
- **Progress Tracking:** Monitor extraction via `data_load_status` table

### Production Ready

- **UPSERT Logic:** Prevents duplicates, handles updates
- **Comprehensive Indexes:** Optimized for common queries
- **Data Validation:** Type checking and constraint validation
- **Logging:** Detailed logs for debugging
- **Configuration:** YAML-based, environment-specific

## Common Use Cases

### Analytics Dashboard

Query match statistics:
```sql
SELECT
    home_team,
    away_team,
    home_xg,
    away_xg,
    home_score,
    away_score
FROM fbref_schedule
WHERE league = 'ENG-Premier League'
    AND season = '2324'
ORDER BY date DESC;
```

### xG Analysis

Compare xG models:
```sql
SELECT
    f.game,
    f.home_team,
    f.away_team,
    f.home_xg as fbref_xg,
    u.home_xg as understat_xg,
    f.home_score
FROM fbref_schedule f
JOIN understat_schedule u
    ON f.league = u.league
    AND f.season = u.season
    AND f.game = u.game
WHERE f.league = 'ENG-Premier League'
    AND f.season = '2324';
```

### Player Performance

Top scorers:
```sql
SELECT
    player,
    team,
    goals_performance_gls as goals,
    goals_performance_ast as assists,
    goals_expected_xg as xg
FROM fbref_player_season_standard
WHERE league = 'ENG-Premier League'
    AND season = '2324'
ORDER BY goals_performance_gls DESC
LIMIT 20;
```

### Shot Analysis

Shot locations and xG:
```sql
SELECT
    player,
    team,
    location_x,
    location_y,
    xg,
    result
FROM understat_shot_events
WHERE league = 'ENG-Premier League'
    AND season = '2324'
    AND team = 'Arsenal'
ORDER BY xg DESC;
```

## Extraction Examples

### Load Historical Data

```bash
# All sources, all leagues, 2020-2024
python -m scripts.historical_loader

# Specific source and league
python -m scripts.orchestrator \
    --sources fbref \
    --leagues "ENG-Premier League" \
    --seasons 2021 2122 2223 2324
```

### Daily Updates

```bash
# Auto-detect current season
python -m scripts.daily_updater

# Specific season
python -m scripts.daily_updater --season 2425
```

### Monitoring

```sql
-- Check extraction status
SELECT
    data_source,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    SUM(rows_processed) as total_rows
FROM data_load_status
GROUP BY data_source
ORDER BY data_source;
```

## Performance

### Typical Load Times

- **Single season, single league, FBref:** ~30-60 minutes
- **All sources, single league, single season:** ~2-3 hours
- **Historical load (2020-2024, all leagues):** ~4-8 hours

### Database Size

- **Per season (all sources, all leagues):** ~500MB - 1GB
- **5 seasons (2020-2024):** ~3-5GB

## Next Steps

1. [Complete Setup Guide](SETUP.md)
2. [Read Extraction Guide](EXTRACTION_GUIDE.md)
3. [Explore Data Sources](DATA_SOURCES.md)
4. Run your first extraction
5. Start building analytics!

## Support

- **Issues:** Check [Troubleshooting Guide](TROUBLESHOOTING.md)
- **Schema:** Review SQL files in `schema/`
- **Examples:** See extraction examples above
