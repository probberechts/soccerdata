-- =============================================================================
-- Understat Tables (7 tables total)
-- =============================================================================
-- Description: All tables for Understat data source (understat.com)
-- Data: Advanced xG metrics, shot events with coordinates
-- Tables: Metadata (2), Match stats (2), Player stats (2), Shots (1)
-- =============================================================================

\c football_stats

-- =============================================================================
-- LEAGUE & SEASON METADATA
-- =============================================================================

CREATE TABLE understat_leagues (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL UNIQUE,
    league_id INTEGER NOT NULL UNIQUE,
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'understat',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_understat_leagues_league_id ON understat_leagues(league_id);
CREATE TRIGGER update_understat_leagues_updated_at BEFORE UPDATE ON understat_leagues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE understat_leagues IS 'Understat league information';

-- -----------------------------------------------------------------------------

CREATE TABLE understat_seasons (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    league_id INTEGER NOT NULL,
    season_id INTEGER NOT NULL,
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'understat',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(league, season)
);

CREATE INDEX idx_understat_seasons_league_season ON understat_seasons(league, season);
CREATE INDEX idx_understat_seasons_ids ON understat_seasons(league_id, season_id);
CREATE TRIGGER update_understat_seasons_updated_at BEFORE UPDATE ON understat_seasons
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE understat_seasons IS 'Understat season information';

-- =============================================================================
-- MATCH SCHEDULE
-- =============================================================================

CREATE TABLE understat_schedule (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    game TEXT NOT NULL,

    -- IDs
    league_id INTEGER NOT NULL,
    season_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL UNIQUE,

    -- Match Information
    date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Teams
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_team_id INTEGER,
    away_team_id INTEGER,
    home_team_code TEXT,
    away_team_code TEXT,

    -- Score
    home_goals INTEGER,
    away_goals INTEGER,

    -- Expected Goals
    home_xg NUMERIC(6,3),
    away_xg NUMERIC(6,3),

    -- Match Status
    is_result BOOLEAN,
    has_data BOOLEAN,

    -- URL
    url TEXT,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'understat',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, game)
);

CREATE INDEX idx_understat_schedule_league_season ON understat_schedule(league, season);
CREATE INDEX idx_understat_schedule_date ON understat_schedule(date);
CREATE INDEX idx_understat_schedule_game_id ON understat_schedule(game_id);
CREATE INDEX idx_understat_schedule_teams ON understat_schedule(home_team, away_team);
CREATE TRIGGER update_understat_schedule_updated_at BEFORE UPDATE ON understat_schedule
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE understat_schedule IS 'Understat match schedule with xG data';

-- =============================================================================
-- TEAM MATCH STATISTICS
-- =============================================================================

CREATE TABLE understat_team_match_stats (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    game TEXT NOT NULL,

    -- IDs
    league_id INTEGER NOT NULL,
    season_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,

    -- Match Information
    date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Teams
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_team_id INTEGER,
    away_team_id INTEGER,
    home_team_code TEXT,
    away_team_code TEXT,

    -- Home Team Stats
    home_points INTEGER,
    home_expected_points NUMERIC(5,3),
    home_goals INTEGER,
    home_xg NUMERIC(6,3),
    home_np_xg NUMERIC(6,3),              -- Non-penalty xG
    home_np_xg_difference NUMERIC(6,3),   -- npxG - npxG conceded
    home_ppda NUMERIC(6,3),                -- Passes per defensive action
    home_deep_completions INTEGER,         -- Passes completed within 20 yards of goal

    -- Away Team Stats
    away_points INTEGER,
    away_expected_points NUMERIC(5,3),
    away_goals INTEGER,
    away_xg NUMERIC(6,3),
    away_np_xg NUMERIC(6,3),
    away_np_xg_difference NUMERIC(6,3),
    away_ppda NUMERIC(6,3),
    away_deep_completions INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'understat',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, game)
);

CREATE INDEX idx_understat_team_match_stats_league_season ON understat_team_match_stats(league, season);
CREATE INDEX idx_understat_team_match_stats_game_id ON understat_team_match_stats(game_id);
CREATE INDEX idx_understat_team_match_stats_date ON understat_team_match_stats(date);
CREATE TRIGGER update_understat_team_match_stats_updated_at BEFORE UPDATE ON understat_team_match_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE understat_team_match_stats IS 'Understat team match statistics including xG, npxG, and PPDA';
COMMENT ON COLUMN understat_team_match_stats.home_ppda IS 'Passes allowed per defensive action (lower = more intense press)';
COMMENT ON COLUMN understat_team_match_stats.home_deep_completions IS 'Completed passes within 20 yards of opponent goal';

-- =============================================================================
-- PLAYER SEASON STATISTICS
-- =============================================================================

CREATE TABLE understat_player_season_stats (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    player TEXT NOT NULL,

    -- IDs
    league_id INTEGER NOT NULL,
    season_id INTEGER NOT NULL,
    team_id INTEGER,
    player_id INTEGER,

    -- Basic Info
    position TEXT,

    -- Playing Time
    matches INTEGER,
    minutes INTEGER,

    -- Goals
    goals INTEGER,
    xg NUMERIC(6,3),
    np_goals INTEGER,              -- Non-penalty goals
    np_xg NUMERIC(6,3),            -- Non-penalty xG

    -- Assists
    assists INTEGER,
    xa NUMERIC(6,3),               -- Expected assists

    -- Shots
    shots INTEGER,
    key_passes INTEGER,

    -- Discipline
    yellow_cards INTEGER,
    red_cards INTEGER,

    -- Advanced Metrics
    xg_chain NUMERIC(7,3),         -- xG from all possessions player involved in
    xg_buildup NUMERIC(7,3),       -- xG from possessions player involved in (excluding shots and assists)

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'understat',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, player)
);

CREATE INDEX idx_understat_player_season_stats_league_season ON understat_player_season_stats(league, season);
CREATE INDEX idx_understat_player_season_stats_player ON understat_player_season_stats(player);
CREATE INDEX idx_understat_player_season_stats_team ON understat_player_season_stats(team);
CREATE INDEX idx_understat_player_season_stats_xg ON understat_player_season_stats(xg);
CREATE TRIGGER update_understat_player_season_stats_updated_at BEFORE UPDATE ON understat_player_season_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE understat_player_season_stats IS 'Understat player season statistics with advanced xG metrics';
COMMENT ON COLUMN understat_player_season_stats.xg_chain IS 'Total xG of possessions player was involved in';
COMMENT ON COLUMN understat_player_season_stats.xg_buildup IS 'xG buildup (excludes final shot and assist)';
COMMENT ON COLUMN understat_player_season_stats.xa IS 'Expected assists (xA)';

-- =============================================================================
-- PLAYER MATCH STATISTICS
-- =============================================================================

CREATE TABLE understat_player_match_stats (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    game TEXT NOT NULL,
    team TEXT NOT NULL,
    player TEXT NOT NULL,

    -- IDs
    league_id INTEGER NOT NULL,
    season_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    team_id INTEGER,
    player_id INTEGER,

    -- Basic Info
    position TEXT,
    position_id INTEGER,

    -- Playing Time
    minutes INTEGER,

    -- Goals
    goals INTEGER,
    own_goals INTEGER,
    xg NUMERIC(6,3),

    -- Assists
    assists INTEGER,
    xa NUMERIC(6,3),

    -- Shots
    shots INTEGER,
    key_passes INTEGER,

    -- Discipline
    yellow_cards INTEGER,
    red_cards INTEGER,

    -- Advanced Metrics
    xg_chain NUMERIC(7,3),
    xg_buildup NUMERIC(7,3),

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'understat',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, game, team, player)
);

CREATE INDEX idx_understat_player_match_stats_league_season ON understat_player_match_stats(league, season);
CREATE INDEX idx_understat_player_match_stats_game ON understat_player_match_stats(game);
CREATE INDEX idx_understat_player_match_stats_player ON understat_player_match_stats(player);
CREATE TRIGGER update_understat_player_match_stats_updated_at BEFORE UPDATE ON understat_player_match_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE understat_player_match_stats IS 'Understat player match statistics';

-- =============================================================================
-- SHOT EVENTS
-- =============================================================================

CREATE TABLE understat_shot_events (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    game TEXT NOT NULL,
    team TEXT NOT NULL,
    player TEXT NOT NULL,

    -- IDs
    league_id INTEGER NOT NULL,
    season_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    shot_id INTEGER NOT NULL,
    team_id INTEGER,
    player_id INTEGER,

    -- Shot Timing
    date TIMESTAMP WITH TIME ZONE,
    minute INTEGER,

    -- Shot Details
    xg NUMERIC(6,3),
    location_x NUMERIC(5,2),  -- X coordinate (0-100)
    location_y NUMERIC(5,2),  -- Y coordinate (0-100)

    -- Shot Characteristics
    body_part TEXT,  -- 'Right Foot', 'Left Foot', 'Other'
    situation TEXT,  -- 'Open Play', 'From Corner', 'Set Piece', 'Direct Freekick'
    result TEXT,     -- 'Goal', 'Own Goal', 'Blocked Shot', 'Saved Shot', 'Missed Shot', 'Shot On Post'

    -- Assist Information
    assist_player TEXT,
    assist_player_id INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'understat',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(shot_id, game_id)
);

CREATE INDEX idx_understat_shot_events_league_season ON understat_shot_events(league, season);
CREATE INDEX idx_understat_shot_events_game ON understat_shot_events(game);
CREATE INDEX idx_understat_shot_events_player ON understat_shot_events(player);
CREATE INDEX idx_understat_shot_events_team ON understat_shot_events(team);
CREATE INDEX idx_understat_shot_events_xg ON understat_shot_events(xg);
CREATE INDEX idx_understat_shot_events_result ON understat_shot_events(result);
CREATE INDEX idx_understat_shot_events_location ON understat_shot_events(location_x, location_y);
CREATE TRIGGER update_understat_shot_events_updated_at BEFORE UPDATE ON understat_shot_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE understat_shot_events IS 'Understat shot events with xG values and coordinates';
COMMENT ON COLUMN understat_shot_events.location_x IS 'X coordinate of shot (0-100, 0=own goal, 100=opponent goal)';
COMMENT ON COLUMN understat_shot_events.location_y IS 'Y coordinate of shot (0-100, from left to right)';
