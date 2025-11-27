-- =============================================================================
-- Common Types and Enums
-- =============================================================================
-- Description: Custom types, enums, and domains used across all tables
-- Created: 2025-11-27
-- =============================================================================

\c football_stats

-- =============================================================================
-- Enum Types
-- =============================================================================

-- Standardized league names
CREATE TYPE league_name AS ENUM (
    'ENG-Premier League',
    'ESP-La Liga',
    'GER-Bundesliga',
    'ITA-Serie A',
    'FRA-Ligue 1'
);

-- Match result outcomes
CREATE TYPE match_result AS ENUM (
    'W',  -- Win
    'D',  -- Draw
    'L',  -- Loss
    'N'   -- Not played / Unknown
);

-- Match venue
CREATE TYPE match_venue AS ENUM (
    'Home',
    'Away',
    'Neutral'
);

-- Player positions (general categories)
CREATE TYPE player_position AS ENUM (
    'GK',  -- Goalkeeper
    'DF',  -- Defender
    'MF',  -- Midfielder
    'FW',  -- Forward
    'Unknown'
);

-- Card types
CREATE TYPE card_type AS ENUM (
    'Yellow',
    'Red',
    'SecondYellow'
);

-- Shot outcomes
CREATE TYPE shot_outcome AS ENUM (
    'Goal',
    'OwnGoal',
    'Saved',
    'Blocked',
    'Missed',
    'ShotOnPost'
);

-- Event types (for match events)
CREATE TYPE event_type AS ENUM (
    'Goal',
    'Assist',
    'YellowCard',
    'RedCard',
    'Substitution',
    'SubstitutionIn',
    'SubstitutionOut',
    'Shot',
    'Pass',
    'Tackle',
    'Foul',
    'Offside',
    'Corner',
    'Penalty',
    'Other'
);

-- =============================================================================
-- Domain Types (Constrained base types)
-- =============================================================================

-- Season format (e.g., '2021' for 2020-2021 season or '1617' for 2016-2017)
CREATE DOMAIN season_id AS TEXT
    CHECK (VALUE ~ '^\d{2}(\d{2})?$');

-- Percentage (0-100)
CREATE DOMAIN percentage AS NUMERIC(5,2)
    CHECK (VALUE >= 0 AND VALUE <= 100);

-- Expected goals (typically 0-5, but allow higher for edge cases)
CREATE DOMAIN xg_value AS NUMERIC(5,3)
    CHECK (VALUE >= 0);

-- Minutes played (0-120 to account for extra time)
CREATE DOMAIN minutes_played AS INTEGER
    CHECK (VALUE >= 0 AND VALUE <= 200);

-- =============================================================================
-- Composite Types (for complex data structures)
-- =============================================================================

-- Score structure
CREATE TYPE score_type AS (
    home INTEGER,
    away INTEGER
);

-- =============================================================================
-- Comments
-- =============================================================================

COMMENT ON TYPE league_name IS 'Standardized league names across all data sources';
COMMENT ON TYPE match_result IS 'Match outcome from team perspective (W/D/L)';
COMMENT ON TYPE match_venue IS 'Match location (Home/Away/Neutral)';
COMMENT ON TYPE player_position IS 'General player position categories';
COMMENT ON TYPE card_type IS 'Types of cards shown in matches';
COMMENT ON TYPE shot_outcome IS 'Outcome of a shot attempt';
COMMENT ON TYPE event_type IS 'Types of match events';
COMMENT ON DOMAIN season_id IS 'Season identifier in format YYYY or YYZZ';
COMMENT ON DOMAIN percentage IS 'Percentage value constrained between 0-100';
COMMENT ON DOMAIN xg_value IS 'Expected goals value (typically 0-5)';
COMMENT ON DOMAIN minutes_played IS 'Minutes played in a match (0-200 for extra time)';
