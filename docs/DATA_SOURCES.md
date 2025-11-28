# Data Sources Reference

Detailed information about each data source in the database.

## Overview

The database integrates data from 9 different sources, covering **82+ tables** with football statistics.

| Source | Tables | Specialty | Update Frequency |
|--------|--------|-----------|------------------|
| FBref | 44 | Comprehensive Opta statistics | Daily |
| FotMob | 11 | League tables, match stats | Live |
| Understat | 7 | Advanced xG metrics | Daily |
| WhoScored | 4 | Detailed event stream | Daily |
| Sofascore | 4 | Schedules, standings | Live |
| ESPN | 3 | Lineups, matchsheets | Daily |
| ClubElo | 2 | ELO ratings | Daily |
| MatchHistory | 1 | Betting odds (13+ bookmakers) | Daily |
| SoFIFA | 6 | EA Sports FC ratings | Per game release |

## FBref (Football Reference)

**Tables:** 44
**Provider:** Opta (via FBref)
**Coverage:** Top 5 European leagues + more

### Key Features

- Most comprehensive statistics available
- Official Opta data
- Team & player stats (season and match-level)
- Detailed events and shot coordinates
- Goalkeeper advanced metrics

### Table Categories

**Team Season Stats (11 tables):**
- `fbref_team_season_standard` - Goals, assists, xG
- `fbref_team_season_shooting` - Shot creation and conversion
- `fbref_team_season_passing` - Passing statistics
- `fbref_team_season_defense` - Defensive actions
- `fbref_team_season_possession` - Possession and touches
- `fbref_team_season_keeper` - Goalkeeper statistics
- `fbref_team_season_keeper_adv` - Advanced GK metrics
- And 4 more...

**Team Match Stats (9 tables):**
- Match-by-match versions of season stats
- `fbref_team_match_schedule` - Match results and xG

**Player Season Stats (11 tables):**
- Individual player statistics aggregated by season
- Same categories as team stats

**Player Match Stats (7 tables):**
- Player performance by match

**Events & Metadata:**
- `fbref_schedule` - Match schedules with attendance, venues
- `fbref_lineups` - Starting lineups and formations
- `fbref_events` - In-match events (goals, cards, subs)
- `fbref_shot_events` - Every shot with coordinates and xG
- `fbref_leagues`, `fbref_seasons` - Metadata

### Best For

- Academic research
- Advanced analytics
- Machine learning models
- Comprehensive match analysis

## FotMob

**Tables:** 11
**Provider:** FotMob
**Coverage:** Global leagues

### Key Features

- Fast, reliable data
- League tables with form
- Detailed match statistics broken down by category
- Live updates

### Tables

- `fotmob_league_table` - Standings with recent form
- `fotmob_schedule` - Match schedules and results
- `fotmob_team_match_top_stats` - Key match statistics
- `fotmob_team_match_shots` - Shot statistics
- `fotmob_team_match_expected_goals_xg` - xG data
- `fotmob_team_match_passes` - Passing statistics
- `fotmob_team_match_defence` - Defensive stats
- `fotmob_team_match_duels` - Duels won/lost
- `fotmob_team_match_discipline` - Cards and fouls

### Best For

- Quick dashboards
- League standings tracking
- Match summaries

## Understat

**Tables:** 7
**Provider:** Understat
**Coverage:** Top 5 European leagues

### Key Features

- Proprietary xG model
- Shot coordinates (X, Y positions)
- PPDA (Passes Per Defensive Action)
- Detailed shot situation analysis

### Tables

- `understat_schedule` - Matches with team xG
- `understat_team_match_stats` - Team xG, PPDA, deep progressions
- `understat_player_season_stats` - Player xG, xA, shots
- `understat_player_match_stats` - Player performance by match
- `understat_shot_events` - Every shot with:
  - xG value
  - (X, Y) coordinates on pitch
  - Body part (head, left foot, right foot)
  - Situation (open play, set piece, etc.)
  - Result (goal, saved, blocked, missed)

### Best For

- Expected goals (xG) analysis
- Shot quality evaluation
- Spatial analysis with coordinates
- Player finishing ability assessment

## WhoScored

**Tables:** 4
**Provider:** Opta (via WhoScored)
**Coverage:** Top European leagues

### Key Features

- Detailed Opta event stream
- Match ratings (proprietary algorithm)
- Event qualifiers (JSONB for detailed context)
- Position coordinates for events

### Tables

- `whoscored_schedule` - Match schedules
- `whoscored_events` - Full event stream with:
  - Event type (pass, shot, tackle, etc.)
  - Qualifiers (additional context as JSONB)
  - (X, Y) coordinates
  - Player involved
  - Outcome

### Best For

- Event-level analysis
- Building custom metrics from events
- Touch maps and heat maps
- Sequence analysis

## Sofascore

**Tables:** 4
**Provider:** Sofascore
**Coverage:** Global leagues

### Key Features

- Clean, reliable data
- Fast updates
- Good for schedules

### Tables

- `sofascore_league_table` - League standings
- `sofascore_schedule` - Match schedules
- `sofascore_leagues`, `sofascore_seasons` - Metadata

### Best For

- Backup/validation of schedules
- Cross-source verification

## ESPN

**Tables:** 3
**Provider:** ESPN
**Coverage:** Global leagues

### Key Features

- Detailed lineups
- Match statistics in JSONB format

### Tables

- `espn_schedule` - Match schedules
- `espn_matchsheet` - Team match statistics (JSONB)
- `espn_lineup` - Starting lineups and formations

### Best For

- Lineup analysis
- Formation studies
- Player positioning

## ClubElo

**Tables:** 2
**Provider:** ClubElo
**Coverage:** Global clubs

### Key Features

- Historical ELO ratings
- Club strength tracking over time
- Pre-match win probability

### Tables

- `clubelo_ratings_by_date` - Daily ELO ratings for all clubs
- `clubelo_team_history` - Historical ELO for specific teams

### Best For

- Team strength comparisons
- Predictive modeling
- Historical analysis

## MatchHistory

**Tables:** 1
**Provider:** MatchHistory.com
**Coverage:** Top European leagues

### Key Features

- Betting odds from 13+ bookmakers:
  - Bet365, Pinnacle, William Hill
  - 1xBet, Betfair, and more
- Asian Handicap lines
- Over/Under 2.5 goals
- Match statistics

### Table

- `matchhistory_odds` - Comprehensive betting data

### Best For

- Betting analysis
- Market efficiency studies
- Implied probability calculations
- Arbitrage detection

## SoFIFA

**Tables:** 6
**Provider:** SoFIFA
**Coverage:** EA Sports FC (FIFA) database

### Key Features

- Official EA Sports FC ratings
- Player attributes (JSONB)
- Team ratings
- Multiple game versions

### Tables

- `sofifa_teams` - Team information
- `sofifa_players` - Player metadata
- `sofifa_team_ratings` - Team overall ratings
- `sofifa_player_ratings` - Player ratings and attributes (JSONB)
- `sofifa_leagues`, `sofifa_versions` - Metadata

### Best For

- Player potential analysis
- Video game analytics
- Youth player scouting
- Rating vs. performance studies

## Data Comparison

### Overlapping Data

Many sources provide similar data types. Key differences:

| Metric | FBref | FotMob | Understat |
|--------|-------|--------|-----------|
| xG Model | Opta | Proprietary | Proprietary |
| Shot Coords | ✓ | ✗ | ✓ |
| Events | ✓ | ✗ | ✗ |
| Update Speed | Daily | Live | Daily |
| Historical | 2017+ | 2019+ | 2014+ |

### Recommended Primary Sources

- **General statistics:** FBref (most comprehensive)
- **xG analysis:** Understat (detailed shot data)
- **Live standings:** FotMob (fastest updates)
- **Event analysis:** WhoScored (full event stream)
- **Betting:** MatchHistory (most bookmakers)

## Data Quality Notes

### Known Limitations

1. **FBref:** Some older seasons may have incomplete data
2. **Understat:** Limited to top 5 leagues only
3. **WhoScored:** May have regional access restrictions
4. **ClubElo:** Historical ratings change as model improves
5. **SoFIFA:** Updated only with game releases (3-4x per year)

### Data Freshness

- **Real-time:** FotMob
- **Daily:** FBref, Understat, WhoScored, Sofascore, ESPN, MatchHistory, ClubElo
- **Per game release:** SoFIFA

## Source Selection Guide

### For Different Use Cases

**Academic Research:**
- Primary: FBref
- Secondary: Understat, WhoScored

**Web Application:**
- Primary: FotMob (fast)
- Secondary: FBref (comprehensive)

**Betting Analysis:**
- Primary: MatchHistory
- Secondary: FBref (team stats), Understat (xG)

**xG Modeling:**
- Primary: Understat (shot coordinates)
- Secondary: FBref (additional context)

**Player Scouting:**
- Primary: FBref (detailed metrics)
- Secondary: SoFIFA (potential ratings)
