# Football Statistics Database - Setup Guide

Complete setup guide for the PostgreSQL database and data extraction framework.

## Prerequisites

- PostgreSQL 12 or higher
- Python 3.9 or higher
- 10GB+ disk space (for historical data)

## 1. Database Setup

### Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql@14
brew services start postgresql@14
```

### Create Database

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Run the database setup script
\i schema/00_database_setup.sql

# Create all tables (run each schema file in order)
\i schema/01_common_types.sql
\i schema/02_fbref_tables.sql
\i schema/03_fotmob_tables.sql
\i schema/04_understat_tables.sql
\i schema/05_whoscored_tables.sql
\i schema/06_sofascore_tables.sql
\i schema/07_espn_tables.sql
\i schema/08_clubelo_tables.sql
\i schema/09_matchhistory_tables.sql
\i schema/10_sofifa_tables.sql
\i schema/99_indexes_constraints.sql  # Optional performance indexes

# Exit PostgreSQL
\q
```

**Or run all at once:**
```bash
cat schema/*.sql | sudo -u postgres psql football_stats
```

## 2. Python Environment Setup

### Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
```

### Install Dependencies

```bash
# Install main dependencies
pip install -r requirements.txt

# Install database-specific dependencies
pip install -r requirements-database.txt
```

## 3. Configuration

### Database Configuration

Copy the environment template and configure database credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=football_stats
DB_USER=postgres
DB_PASSWORD=your_password_here
```

### Data Sources Configuration

The `config/data_sources.yaml` file controls:
- Which data sources are enabled
- Extraction priority order
- Retry and rate limiting settings

Default settings should work for most use cases.

### Leagues Configuration

Edit `config/leagues.yaml` to enable/disable specific leagues:

```yaml
leagues:
  - name: "ENG-Premier League"
    enabled: true  # Set to false to disable
```

## 4. Verify Setup

### Test Database Connection

```python
from scripts.utils import DatabaseManager, get_config_loader

config = get_config_loader()
db_config = config.get_database_config()
db = DatabaseManager(**db_config)

if db.test_connection():
    print("✓ Database connection successful")
else:
    print("✗ Database connection failed")
```

### Check Table Creation

```bash
sudo -u postgres psql football_stats -c "\dt"
```

You should see 82+ tables listed.

## 5. Initial Data Load

### Load Historical Data (2020-2025)

```bash
python -m scripts.historical_loader \
    --start-year 2020 \
    --end-year 2024
```

This will:
- Extract data from all enabled sources
- For all enabled leagues
- For seasons 2020-2021 through 2024-2025
- Skip already-completed extractions

**Estimated time:** 4-8 hours (depending on network speed)

### Load Single Season

```bash
python -m scripts.orchestrator \
    --seasons 2324 \
    --leagues "ENG-Premier League"
```

### Load Specific Data Source

```bash
python -m scripts.orchestrator \
    --sources fbref \
    --seasons 2324 \
    --leagues "ENG-Premier League"
```

## 6. Monitoring Progress

### Check Logs

```bash
tail -f logs/orchestrator_*.log
```

### Check Database Status

```sql
-- View extraction status
SELECT
    data_source,
    table_name,
    league,
    season,
    status,
    rows_processed,
    completed_at
FROM data_load_status
ORDER BY completed_at DESC
LIMIT 20;

-- Count completed extractions by source
SELECT
    data_source,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
    SUM(rows_processed) as total_rows
FROM data_load_status
GROUP BY data_source
ORDER BY data_source;
```

## 7. Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues and solutions.

## 8. Daily Updates

Set up a cron job for daily updates:

```bash
# Edit crontab
crontab -e

# Add daily update at 3 AM
0 3 * * * cd /path/to/soccerdata && /path/to/venv/bin/python -m scripts.daily_updater
```

## Next Steps

- [Extraction Guide](EXTRACTION_GUIDE.md) - Detailed usage instructions
- [Data Sources](DATA_SOURCES.md) - Information about each data source
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and solutions
