-- =============================================================================
-- FBref Tables (44 tables total)
-- =============================================================================
-- Description: All tables for FBref data source (fbref.com)
-- Data: Opta-based statistics, most comprehensive source
-- Tables: Team stats (22), Player stats (18), Match data (4)
-- =============================================================================

\c football_stats

-- =============================================================================
-- LEAGUE & SEASON METADATA
-- =============================================================================

CREATE TABLE fbref_leagues (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL UNIQUE,
    league_standardized TEXT NOT NULL,
    country TEXT,
    first_season TEXT,
    last_season TEXT,
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_fbref_leagues_standardized ON fbref_leagues(league_standardized);
CREATE TRIGGER update_fbref_leagues_updated_at BEFORE UPDATE ON fbref_leagues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_leagues IS 'FBref league information and metadata';

-- -----------------------------------------------------------------------------

CREATE TABLE fbref_seasons (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    format TEXT CHECK (format IN ('round-robin', 'elimination')),
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(league, season)
);

CREATE INDEX idx_fbref_seasons_league ON fbref_seasons(league);
CREATE INDEX idx_fbref_seasons_season ON fbref_seasons(season);
CREATE TRIGGER update_fbref_seasons_updated_at BEFORE UPDATE ON fbref_seasons
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_seasons IS 'FBref season information per league';

-- =============================================================================
-- TEAM SEASON STATISTICS (11 tables - one per stat type)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Standard Team Season Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_season_standard (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,

    -- Playing Time
    players_used INTEGER,
    age_avg NUMERIC(4,1),
    possession NUMERIC(5,2),
    games_played INTEGER,
    games_started INTEGER,
    minutes INTEGER,
    minutes_per_90 NUMERIC(5,1),

    -- Performance - Goals
    goals INTEGER,
    assists INTEGER,
    goals_plus_assists INTEGER,
    goals_non_penalty INTEGER,
    penalty_kicks INTEGER,
    penalty_kicks_attempted INTEGER,
    yellow_cards INTEGER,
    red_cards INTEGER,

    -- Expected
    xg NUMERIC(6,2),
    npxg NUMERIC(6,2),
    xag NUMERIC(6,2),
    npxg_plus_xag NUMERIC(6,2),

    -- Progression
    progressive_carries INTEGER,
    progressive_passes INTEGER,
    progressive_receptions INTEGER,

    -- Per 90 Minutes
    goals_per_90 NUMERIC(4,2),
    assists_per_90 NUMERIC(4,2),
    goals_plus_assists_per_90 NUMERIC(4,2),
    goals_non_penalty_per_90 NUMERIC(4,2),
    goals_plus_assists_non_penalty_per_90 NUMERIC(4,2),
    xg_per_90 NUMERIC(4,2),
    xag_per_90 NUMERIC(4,2),
    xg_plus_xag_per_90 NUMERIC(4,2),
    npxg_per_90 NUMERIC(4,2),
    npxg_plus_xag_per_90 NUMERIC(4,2),

    -- Metadata
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team)
);

CREATE INDEX idx_fbref_team_season_standard_league_season ON fbref_team_season_standard(league, season);
CREATE INDEX idx_fbref_team_season_standard_team ON fbref_team_season_standard(team);
CREATE TRIGGER update_fbref_team_season_standard_updated_at BEFORE UPDATE ON fbref_team_season_standard
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_season_standard IS 'FBref team season standard statistics (goals, assists, xG, cards)';

-- -----------------------------------------------------------------------------
-- Team Season Passing Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_season_passing (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,

    -- Playing Time
    players_used INTEGER,
    minutes_per_90 NUMERIC(5,1),

    -- Total Passing
    passes_completed INTEGER,
    passes_attempted INTEGER,
    pass_completion_pct NUMERIC(5,2),
    total_pass_distance INTEGER,
    progressive_pass_distance INTEGER,

    -- Short Passing (5-15 yards)
    short_passes_completed INTEGER,
    short_passes_attempted INTEGER,
    short_pass_completion_pct NUMERIC(5,2),

    -- Medium Passing (15-30 yards)
    medium_passes_completed INTEGER,
    medium_passes_attempted INTEGER,
    medium_pass_completion_pct NUMERIC(5,2),

    -- Long Passing (30+ yards)
    long_passes_completed INTEGER,
    long_passes_attempted INTEGER,
    long_pass_completion_pct NUMERIC(5,2),

    -- Assist Stats
    assists INTEGER,
    xag NUMERIC(6,2),
    expected_assists NUMERIC(6,2),
    assists_minus_expected NUMERIC(6,2),
    key_passes INTEGER,
    passes_into_final_third INTEGER,
    passes_into_penalty_area INTEGER,
    crosses_into_penalty_area INTEGER,
    progressive_passes INTEGER,

    -- Metadata
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team)
);

CREATE INDEX idx_fbref_team_season_passing_league_season ON fbref_team_season_passing(league, season);
CREATE INDEX idx_fbref_team_season_passing_team ON fbref_team_season_passing(team);
CREATE TRIGGER update_fbref_team_season_passing_updated_at BEFORE UPDATE ON fbref_team_season_passing
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_season_passing IS 'FBref team season passing statistics';

-- =============================================================================
-- MATCH SCHEDULES & FIXTURES
-- =============================================================================

CREATE TABLE fbref_schedule (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    game TEXT NOT NULL,  -- Composite game identifier

    -- Match Information
    week INTEGER,
    day TEXT,
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    time TEXT,

    -- Teams
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,

    -- Score
    score TEXT,
    home_goals INTEGER,
    away_goals INTEGER,

    -- Expected Goals
    home_xg NUMERIC(5,2),
    away_xg NUMERIC(5,2),

    -- Match Details
    attendance INTEGER,
    venue TEXT,
    referee TEXT,
    match_report TEXT,  -- URL to match report
    notes TEXT,
    game_id TEXT,  -- FBref internal game ID

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, game)
);

CREATE INDEX idx_fbref_schedule_league_season ON fbref_schedule(league, season);
CREATE INDEX idx_fbref_schedule_date ON fbref_schedule(date);
CREATE INDEX idx_fbref_schedule_home_team ON fbref_schedule(home_team);
CREATE INDEX idx_fbref_schedule_away_team ON fbref_schedule(away_team);
CREATE INDEX idx_fbref_schedule_game_id ON fbref_schedule(game_id);
CREATE TRIGGER update_fbref_schedule_updated_at BEFORE UPDATE ON fbref_schedule
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_schedule IS 'FBref match schedule with results and xG';

-- =============================================================================
-- MATCH LINEUPS
-- =============================================================================

CREATE TABLE fbref_lineups (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    game TEXT NOT NULL,
    team TEXT NOT NULL,

    -- Player Information
    player TEXT NOT NULL,
    jersey_number INTEGER,
    position TEXT,

    -- Match Participation
    is_starter BOOLEAN NOT NULL,
    minutes_played INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, game, team, player)
);

CREATE INDEX idx_fbref_lineups_league_season ON fbref_lineups(league, season);
CREATE INDEX idx_fbref_lineups_game ON fbref_lineups(game);
CREATE INDEX idx_fbref_lineups_player ON fbref_lineups(player);
CREATE INDEX idx_fbref_lineups_team ON fbref_lineups(team);
CREATE TRIGGER update_fbref_lineups_updated_at BEFORE UPDATE ON fbref_lineups
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_lineups IS 'FBref match lineups (starters and substitutes)';

-- =============================================================================
-- MATCH EVENTS
-- =============================================================================

CREATE TABLE fbref_events (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Event Details
    team TEXT NOT NULL,
    minute TEXT NOT NULL,  -- Can include stoppage time like "45+2"
    score TEXT,

    -- Players Involved
    player1 TEXT NOT NULL,  -- Primary player (scorer, recipient of card, etc.)
    player2 TEXT,           -- Secondary player (assister, substituted player, etc.)

    -- Event Type
    event_type TEXT NOT NULL,  -- 'goal', 'yellow_card', 'red_card', 'substitute_in', etc.

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_fbref_events_league_season ON fbref_events(league, season);
CREATE INDEX idx_fbref_events_game ON fbref_events(game);
CREATE INDEX idx_fbref_events_team ON fbref_events(team);
CREATE INDEX idx_fbref_events_player1 ON fbref_events(player1);
CREATE INDEX idx_fbref_events_event_type ON fbref_events(event_type);
CREATE TRIGGER update_fbref_events_updated_at BEFORE UPDATE ON fbref_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_events IS 'FBref match events (goals, cards, substitutions)';

-- =============================================================================
-- SHOT EVENTS
-- =============================================================================

CREATE TABLE fbref_shot_events (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Shot Details
    minute INTEGER,
    player TEXT NOT NULL,
    team TEXT NOT NULL,

    -- Expected Goals
    xg NUMERIC(5,3),
    psxg NUMERIC(5,3),  -- Post-shot xG

    -- Outcome
    outcome TEXT,  -- 'Goal', 'Saved', 'Blocked', 'Missed', 'Shot On Post'
    distance INTEGER,  -- Distance from goal in yards
    body_part TEXT,    -- 'Right Foot', 'Left Foot', 'Head', 'Other'
    notes TEXT,        -- Additional notes (e.g., 'Volley', 'Free Kick')

    -- Shot Creation Actions (SCA)
    sca1_player TEXT,
    sca1_event TEXT,
    sca2_player TEXT,
    sca2_event TEXT,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_fbref_shot_events_league_season ON fbref_shot_events(league, season);
CREATE INDEX idx_fbref_shot_events_game ON fbref_shot_events(game);
CREATE INDEX idx_fbref_shot_events_player ON fbref_shot_events(player);
CREATE INDEX idx_fbref_shot_events_team ON fbref_shot_events(team);
CREATE INDEX idx_fbref_shot_events_outcome ON fbref_shot_events(outcome);
CREATE TRIGGER update_fbref_shot_events_updated_at BEFORE UPDATE ON fbref_shot_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_shot_events IS 'FBref shot-level data with xG and shot creation actions';

-- =============================================================================
-- NOTE: This file shows examples of 8 FBref tables
-- The complete file will include all 44 tables covering:
-- - 11 team season stat tables (standard, keeper, shooting, passing, etc.)
-- - 9 team match stat tables
-- - 11 player season stat tables
-- - 7 player match stat tables
-- - 4 match data tables (schedule, lineups, events, shots)
-- - 2 metadata tables (leagues, seasons)
-- =============================================================================
