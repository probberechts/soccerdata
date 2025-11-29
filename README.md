# Football Statistics Database

> **PostgreSQL database implementation for football statistics using the [soccerdata](https://github.com/probberechts/soccerdata) library**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-12+-blue.svg)](https://www.postgresql.org/)

## About This Project

This project provides a **comprehensive PostgreSQL database schema and extraction framework** for storing football (soccer) statistics from multiple data sources. It uses the excellent [soccerdata](https://github.com/probberechts/soccerdata) library to fetch data and stores it in a normalized, queryable database.

### 🏆 What's Included

- **82+ PostgreSQL tables** across 9 data sources
- **Python extraction framework** with automatic retry and error handling
- **Orchestration scripts** for bulk loading and daily updates
- **Comprehensive documentation** and setup guides
- **Production-ready** with UPSERT logic, indexing, and validation

### 📊 Data Coverage

| Source | Tables | Specialty |
|--------|--------|-----------|
| FBref | 44 | Comprehensive Opta statistics |
| FotMob | 11 | League tables, match stats |
| Understat | 7 | xG metrics, shot coordinates |
| WhoScored | 4 | Detailed event stream |
| Sofascore | 4 | Schedules, standings |
| ESPN | 3 | Lineups, matchsheets |
| ClubElo | 2 | ELO ratings |
| MatchHistory | 1 | Betting odds (13+ bookmakers) |
| SoFIFA | 6 | EA Sports FC ratings |

**Leagues:** Premier League, La Liga, Bundesliga, Serie A, Ligue 1
**Seasons:** 2020-2021 onwards
**Database Size:** ~3-5GB for 5 seasons

## Quick Start

### Prerequisites

- PostgreSQL 12+
- Python 3.9+
- 10GB+ disk space

### Installation

```bash
# 1. Clone this repository
git clone https://github.com/makaraduman/soccerdata.git
cd soccerdata

# 2. Install dependencies
pip install -r requirements.txt -r requirements-database.txt

# 3. Create PostgreSQL database
cat schema/*.sql | psql -U postgres football_stats

# 4. Configure database connection
cp .env.example .env
# Edit .env with your database credentials

# 5. Load historical data
python -m scripts.historical_loader
```

See [docs/SETUP.md](docs/SETUP.md) for detailed installation instructions.

## Usage

### Load Historical Data (2020-2025)

```bash
python -m scripts.historical_loader --start-year 2020 --end-year 2024
```

### Load Specific Season/League

```bash
python -m scripts.orchestrator \
    --sources fbref fotmob \
    --leagues "ENG-Premier League" \
    --seasons 2324
```

### Daily Updates

```bash
python -m scripts.daily_updater
```

## Example Queries

### Match Results with xG

```sql
SELECT
    date,
    home_team,
    away_team,
    home_score,
    away_score,
    home_xg,
    away_xg
FROM fbref_schedule
WHERE league = 'ENG-Premier League'
    AND season = '2324'
ORDER BY date DESC;
```

### Top Scorers

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
ORDER BY goals DESC
LIMIT 20;
```

### Shot Analysis with Coordinates

```sql
SELECT
    player,
    team,
    location_x,
    location_y,
    xg,
    result
FROM understat_shot_events
WHERE team = 'Arsenal'
    AND season = '2324'
ORDER BY xg DESC;
```

## Documentation

- **[Setup Guide](docs/SETUP.md)** - Complete installation and configuration
- **[Extraction Guide](docs/EXTRACTION_GUIDE.md)** - How to use the extraction scripts
- **[Data Sources](docs/DATA_SOURCES.md)** - Detailed information about each data source
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Database Overview](docs/DATABASE_README.md)** - Architecture and design

## Architecture

```
soccerdata/
├── schema/              # PostgreSQL DDL (12 files, 82+ tables)
├── scripts/
│   ├── utils/           # Core utilities (db, logging, config, validation)
│   ├── extractors/      # 9 data source extractors
│   ├── orchestrator.py  # Master coordinator
│   ├── historical_loader.py
│   └── daily_updater.py
├── config/              # YAML configuration
└── docs/                # Comprehensive documentation
```

## Attribution

**This project is a fork of [soccerdata](https://github.com/probberechts/soccerdata) by Pieter Robberechts.**

We use the soccerdata library as a dependency for data fetching. All database schema, extraction framework, and orchestration code is original to this fork.

See [ATTRIBUTION.md](ATTRIBUTION.md) for detailed attribution and license information.

### Original SoccerData Project

- **Repository:** https://github.com/probberechts/soccerdata
- **Documentation:** https://soccerdata.readthedocs.io/
- **PyPI:** https://pypi.org/project/soccerdata/

**Thank you to Pieter Robberechts and all soccerdata contributors!** ⚽

## License

Apache License 2.0 - Same as the original soccerdata project.

See [LICENSE.rst](LICENSE.rst) for details.

## Features

✅ **Comprehensive Data Model**
- 82+ tables across 9 data sources
- Normalized schema with proper relationships
- Custom types and domains for validation

✅ **Automated Extraction**
- Orchestrated extraction from all sources
- Automatic retry with exponential backoff
- Rate limiting to respect API limits
- Progress tracking and resume capability

✅ **Production Ready**
- UPSERT logic prevents duplicates
- Comprehensive indexes for performance
- Data validation at multiple levels
- Detailed logging and error handling

✅ **Easy to Use**
- Simple command-line interface
- YAML configuration
- Comprehensive documentation
- Example queries included

## Use Cases

- **Analytics Dashboards** - Query match and player statistics
- **xG Analysis** - Compare expected goals models
- **Player Scouting** - Analyze player performance metrics
- **Betting Analysis** - Study odds and market movements
- **Machine Learning** - Train models on historical data
- **Research** - Academic analysis of football statistics

## Contributing

This is a focused fork for database implementation. For contributing to the data scraping library, please visit the [original soccerdata project](https://github.com/probberechts/soccerdata).

## Support

- Check [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- Review [Setup Guide](docs/SETUP.md)
- See SQL schema files in `schema/`

## Acknowledgments

Special thanks to:
- **Pieter Robberechts** - Creator of soccerdata
- **All soccerdata contributors** - For maintaining an excellent data library
- **Data sources** - FBref, FotMob, Understat, WhoScored, and others

---

**Built with ❤️ on top of the amazing [soccerdata](https://github.com/probberechts/soccerdata) library**
