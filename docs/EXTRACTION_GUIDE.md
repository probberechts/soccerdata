# Data Extraction Guide

Comprehensive guide to using the data extraction scripts.

## Overview

The extraction framework consists of three main scripts:

1. **orchestrator.py** - Flexible extraction for any combination of sources/leagues/seasons
2. **historical_loader.py** - Bulk historical data loading (2020-2025)
3. **daily_updater.py** - Daily updates for current season

## Orchestrator Usage

### Basic Usage

Extract all data for a specific season:

```bash
python -m scripts.orchestrator --seasons 2324
```

### Advanced Options

```bash
python -m scripts.orchestrator \
    --sources fbref fotmob understat \
    --leagues "ENG-Premier League" "ESP-La Liga" \
    --seasons 2324 2425 \
    --no-skip-completed  # Re-extract even if already completed
```

### Options Reference

| Option | Description | Default |
|--------|-------------|---------|
| `--sources` | Data sources to extract | All enabled |
| `--leagues` | Leagues to extract | All configured |
| `--seasons` | Seasons to extract (required) | None |
| `--no-skip-completed` | Re-extract completed data | Skip completed |
| `--config-dir` | Configuration directory | `config` |
| `--log-dir` | Log directory | `logs` |

### Season Format

Seasons use a 2 or 4-digit format:
- `2021` = 2020-2021 season (first season)
- `2122` = 2021-2022 season
- `2324` = 2023-2024 season
- `2425` = 2024-2025 season

## Historical Loader Usage

### Basic Usage

Load all historical data from 2020-2021 to 2024-2025:

```bash
python -m scripts.historical_loader
```

### Custom Date Range

```bash
python -m scripts.historical_loader \
    --start-year 2021 \
    --end-year 2023
```

### Selective Loading

```bash
python -m scripts.historical_loader \
    --start-year 2020 \
    --end-year 2024 \
    --sources fbref understat \
    --leagues "ENG-Premier League"
```

### Options Reference

| Option | Description | Default |
|--------|-------------|---------|
| `--start-year` | Start year (YYYY) | 2020 |
| `--end-year` | End year (YYYY) | 2024 |
| `--sources` | Data sources to extract | All enabled |
| `--leagues` | Leagues to extract | All configured |
| `--no-skip-completed` | Re-extract completed data | Skip completed |

## Daily Updater Usage

### Basic Usage

Update current season (auto-detected):

```bash
python -m scripts.daily_updater
```

### Specific Season

```bash
python -m scripts.daily_updater --season 2425
```

### Selective Updates

```bash
python -m scripts.daily_updater \
    --sources fbref fotmob \
    --leagues "ENG-Premier League"
```

### Cron Job Setup

```bash
# Edit crontab
crontab -e

# Daily update at 3 AM
0 3 * * * cd /path/to/soccerdata && /path/to/venv/bin/python -m scripts.daily_updater >> /path/to/logs/daily_update.log 2>&1
```

## Data Source Selection

Available data sources (in priority order):

1. **fbref** - Most comprehensive (44 tables)
2. **fotmob** - Fast, reliable (11 tables)
3. **understat** - xG specialist (7 tables)
4. **whoscored** - Event stream (4 tables)
5. **sofascore** - Schedules (4 tables)
6. **espn** - Lineups (3 tables)
7. **clubelo** - ELO ratings (2 tables)
8. **matchhistory** - Betting odds (1 table)
9. **sofifa** - FIFA ratings (6 tables)

### Recommended Combinations

**Minimal (fast):**
```bash
--sources fbref fotmob
```

**Comprehensive (slow):**
```bash
# Use all sources (default)
```

**Match-focused:**
```bash
--sources fbref understat whoscored
```

## Monitoring Extraction

### Real-time Logs

```bash
# Follow orchestrator log
tail -f logs/orchestrator_$(date +%Y%m%d).log

# Follow specific extractor
tail -f logs/extractor_fbref_$(date +%Y%m%d).log
```

### Database Queries

```sql
-- Check recent activity
SELECT
    data_source,
    table_name,
    league,
    season,
    status,
    rows_processed,
    started_at,
    completed_at,
    EXTRACT(EPOCH FROM (completed_at - started_at)) as duration_seconds
FROM data_load_status
WHERE started_at > NOW() - INTERVAL '1 day'
ORDER BY started_at DESC;

-- Find failed extractions
SELECT
    data_source,
    table_name,
    league,
    season,
    error_message,
    last_updated
FROM data_load_status
WHERE status = 'failed'
ORDER BY last_updated DESC;

-- Calculate completion percentage
SELECT
    data_source,
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'completed') / COUNT(*), 1) as completion_pct
FROM data_load_status
GROUP BY data_source
ORDER BY data_source;
```

## Performance Optimization

### Parallel Execution

Currently runs sequentially. Future enhancement: parallel workers.

### Selective Extraction

Only extract what you need:

```bash
# Just current season Premier League from FBref
python -m scripts.orchestrator \
    --sources fbref \
    --leagues "ENG-Premier League" \
    --seasons 2425
```

### Skip Completed Data

Always use `skip_completed=True` (default) for incremental updates:

```bash
# This is the default behavior
python -m scripts.orchestrator --seasons 2425
```

## Retry and Error Handling

### Automatic Retry

Failed extractions are automatically retried with exponential backoff:
- Max attempts: 3
- Initial delay: 2s
- Max delay: 60s
- Exponential base: 2

Configuration in `config/data_sources.yaml`.

### Manual Retry

To retry failed extractions:

```sql
-- Reset failed status to pending
UPDATE data_load_status
SET status = 'pending',
    error_message = NULL
WHERE status = 'failed';
```

Then re-run the extraction.

## Best Practices

1. **Start Small** - Test with one source/league/season first
2. **Monitor Logs** - Watch for errors during extraction
3. **Check Progress** - Query `data_load_status` table regularly
4. **Use Skip-Completed** - Avoid re-extracting existing data
5. **Schedule Wisely** - Run daily updates during off-peak hours
6. **Backup Database** - Before large extractions

## Troubleshooting

For common issues and solutions, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
