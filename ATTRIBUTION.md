# Attribution

This project is a fork of [soccerdata](https://github.com/probberechts/soccerdata) by Pieter Robberechts and contributors.

## Original Project

- **Repository:** https://github.com/probberechts/soccerdata
- **License:** Apache License 2.0
- **Author:** Pieter Robberechts
- **Contributors:** See [original repository contributors](https://github.com/probberechts/soccerdata/graphs/contributors)

## About SoccerData

SoccerData is a collection of scrapers to gather soccer data from popular websites, including Club Elo, ESPN, FBref, FotMob, Sofascore, SoFIFA, Understat, and WhoScored. It provides Pandas DataFrames with sensible, matching column names and identifiers across datasets.

**Original project homepage:** https://soccerdata.readthedocs.io/

## Our Modifications

This fork has been extensively modified to focus on **PostgreSQL database storage** for football statistics. The original soccerdata library is now used as a **dependency** (installed via pip) rather than being bundled with this repository.

### What We Added

- **`/schema/`** - PostgreSQL database schemas (12 SQL files, 3,570 lines)
  - 82+ tables across 9 data sources
  - Comprehensive indexes and constraints
  - Custom types and domains
  - Automatic timestamp triggers

- **`/scripts/`** - Data extraction and loading framework (21 Python files, 4,664 lines)
  - `scripts/utils/` - Core utilities (db_manager, logger, config_loader, validators, retry_handler)
  - `scripts/extractors/` - 9 data source extractors
  - `scripts/orchestrator.py` - Master coordinator
  - `scripts/historical_loader.py` - Bulk historical data loading
  - `scripts/daily_updater.py` - Daily update automation

- **`/config/`** - YAML configuration files
  - Data sources configuration
  - League mappings
  - Logging configuration

- **`/docs/`** - Database-specific documentation
  - DATABASE_README.md - Main documentation
  - SETUP.md - Installation guide
  - EXTRACTION_GUIDE.md - Usage guide
  - DATA_SOURCES.md - Data source reference
  - TROUBLESHOOTING.md - Common issues

- **`.env.example`** - Database configuration template
- **`requirements-database.txt`** - Additional database dependencies

### What We Removed

To focus this repository on database implementation, we removed:

- Original soccerdata library source code (now installed via `pip install soccerdata`)
- Original library tests
- Original Sphinx documentation
- Original example notebooks
- Build and development tooling

### How This Fork Uses SoccerData

Our extractors import and use the soccerdata library to fetch data:

```python
import soccerdata as sd

# Create reader
fbref = sd.FBref(leagues='ENG-Premier League', seasons='2324')

# Fetch data
df = fbref.read_schedule()

# Store in PostgreSQL database
# (our custom code)
```

The soccerdata library handles all web scraping, caching, and data normalization. Our code handles database storage, orchestration, and data loading workflows.

## License

This project maintains the same **Apache License 2.0** as the original soccerdata project.

All modifications and additions are released under the Apache License 2.0.

## Copyright Notices

**Original Work:**
```
Copyright (c) 2021 Pieter Robberechts
Licensed under the Apache License, Version 2.0
```

**This Fork's Modifications:**
```
Copyright (c) 2024 [Your Name/Organization]
Licensed under the Apache License, Version 2.0
```

## Acknowledgments

We are deeply grateful to Pieter Robberechts and all contributors to the soccerdata project for creating and maintaining such a comprehensive and well-designed football data library. This database implementation would not be possible without their excellent work.

**Thank you to the soccerdata community!** ⚽

## Relationship to Original Project

This is a **complementary fork** that builds on top of soccerdata:

- **Original Project:** Focuses on data scraping and providing DataFrames
- **This Fork:** Focuses on database storage and data warehousing
- **Relationship:** We use their library as a dependency, not a replacement

We encourage users interested in data scraping to visit the original soccerdata project. We encourage users interested in database storage to use this fork alongside the original library.

## Links

- **Original SoccerData:** https://github.com/probberechts/soccerdata
- **Original Documentation:** https://soccerdata.readthedocs.io/
- **Original PyPI Package:** https://pypi.org/project/soccerdata/
- **This Fork:** https://github.com/makaraduman/soccerdata
