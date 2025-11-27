-- =============================================================================
-- Sofascore Tables (4 tables total)
-- =============================================================================
-- Description: All tables for Sofascore data source (sofascore.com)
-- Data: Schedules, league tables, basic match data
-- Tables: Metadata (2), League table (1), Schedule (1)
-- =============================================================================

\c football_stats

-- =============================================================================
-- LEAGUE & SEASON METADATA
-- =============================================================================

CREATE TABLE sofascore_leagues (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL UNIQUE,
    league_id INTEGER NOT NULL UNIQUE,
    region TEXT,
    data_source TEXT NOT NULL DEFAULT 'sofascore',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sofascore_leagues_league_id ON sofascore_leagues(league_id);
CREATE TRIGGER update_sofascore_leagues_updated_at BEFORE UPDATE ON sofascore_leagues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE sofascore_leagues IS 'Sofascore league information';

-- -----------------------------------------------------------------------------

CREATE TABLE sofascore_seasons (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    league_id INTEGER,
    season_id INTEGER,
    data_source TEXT NOT NULL DEFAULT 'sofascore',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(league, season)
);

CREATE INDEX idx_sofascore_seasons_league_season ON sofascore_seasons(league, season);
CREATE INDEX idx_sofascore_seasons_ids ON sofascore_seasons(league_id, season_id);
CREATE TRIGGER update_sofascore_seasons_updated_at BEFORE UPDATE ON sofascore_seasons
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE sofascore_seasons IS 'Sofascore season information';

-- =============================================================================
-- LEAGUE STANDINGS
-- =============================================================================

CREATE TABLE sofascore_league_table (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,

    -- Standing
    matches_played INTEGER,
    wins INTEGER,
    draws INTEGER,
    losses INTEGER,
    goals_for INTEGER,
    goals_against INTEGER,
    goal_difference INTEGER,
    points INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'sofascore',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team)
);

CREATE INDEX idx_sofascore_league_table_league_season ON sofascore_league_table(league, season);
CREATE INDEX idx_sofascore_league_table_team ON sofascore_league_table(team);
CREATE INDEX idx_sofascore_league_table_points ON sofascore_league_table(points DESC);
CREATE TRIGGER update_sofascore_league_table_updated_at BEFORE UPDATE ON sofascore_league_table
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE sofascore_league_table IS 'Sofascore league standings';

-- =============================================================================
-- MATCH SCHEDULE
-- =============================================================================

CREATE TABLE sofascore_schedule (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Information
    round INTEGER,
    week INTEGER,
    date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Teams
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,

    -- Score
    home_score INTEGER,
    away_score INTEGER,

    -- IDs
    game_id INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'sofascore',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, game)
);

CREATE INDEX idx_sofascore_schedule_league_season ON sofascore_schedule(league, season);
CREATE INDEX idx_sofascore_schedule_date ON sofascore_schedule(date);
CREATE INDEX idx_sofascore_schedule_home_team ON sofascore_schedule(home_team);
CREATE INDEX idx_sofascore_schedule_away_team ON sofascore_schedule(away_team);
CREATE INDEX idx_sofascore_schedule_game_id ON sofascore_schedule(game_id);
CREATE TRIGGER update_sofascore_schedule_updated_at BEFORE UPDATE ON sofascore_schedule
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE sofascore_schedule IS 'Sofascore match schedule';
