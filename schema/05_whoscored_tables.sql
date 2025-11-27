-- =============================================================================
-- WhoScored Tables (4 tables total)
-- =============================================================================
-- Description: All tables for WhoScored data source (whoscored.com)
-- Data: Detailed Opta event stream data (most granular event data available)
-- Tables: Metadata (2), Season stages (1), Events (1)
-- =============================================================================

\c football_stats

-- =============================================================================
-- LEAGUE & SEASON METADATA
-- =============================================================================

CREATE TABLE whoscored_leagues (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL UNIQUE,
    region_id INTEGER,
    league_id INTEGER,
    region TEXT,
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'whoscored',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_whoscored_leagues_ids ON whoscored_leagues(region_id, league_id);
CREATE TRIGGER update_whoscored_leagues_updated_at BEFORE UPDATE ON whoscored_leagues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE whoscored_leagues IS 'WhoScored league information';

-- -----------------------------------------------------------------------------

CREATE TABLE whoscored_seasons (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    region_id INTEGER,
    league_id INTEGER,
    season_id INTEGER,
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'whoscored',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(league, season)
);

CREATE INDEX idx_whoscored_seasons_league_season ON whoscored_seasons(league, season);
CREATE INDEX idx_whoscored_seasons_ids ON whoscored_seasons(region_id, league_id, season_id);
CREATE TRIGGER update_whoscored_seasons_updated_at BEFORE UPDATE ON whoscored_seasons
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE whoscored_seasons IS 'WhoScored season information';

-- =============================================================================
-- SEASON STAGES
-- =============================================================================

CREATE TABLE whoscored_season_stages (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    stage TEXT,
    region_id INTEGER,
    league_id INTEGER,
    season_id INTEGER,
    stage_id INTEGER,
    data_source TEXT NOT NULL DEFAULT 'whoscored',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(league, season, stage_id)
);

CREATE INDEX idx_whoscored_season_stages_league_season ON whoscored_season_stages(league, season);
CREATE INDEX idx_whoscored_season_stages_stage_id ON whoscored_season_stages(stage_id);
CREATE TRIGGER update_whoscored_season_stages_updated_at BEFORE UPDATE ON whoscored_season_stages
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE whoscored_season_stages IS 'WhoScored season stages (regular season, playoffs, etc.)';

-- =============================================================================
-- MATCH EVENTS (Detailed Opta Event Stream)
-- =============================================================================

CREATE TABLE whoscored_events (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    game TEXT NOT NULL,
    game_id TEXT,

    -- Event Timing
    period TEXT,  -- 'PreMatch', 'FirstHalf', 'SecondHalf', 'PostGame'
    minute INTEGER,
    second INTEGER,
    expanded_minute INTEGER,  -- Includes stoppage time

    -- Event Details
    event_type TEXT NOT NULL,
    outcome_type TEXT,  -- 'Successful', 'Unsuccessful'

    -- Team
    team_id TEXT,
    team TEXT,

    -- Player
    player_id TEXT,
    player TEXT,

    -- Location Coordinates
    x NUMERIC(5,2),
    y NUMERIC(5,2),
    end_x NUMERIC(5,2),
    end_y NUMERIC(5,2),

    -- Shot Details (if applicable)
    goal_mouth_y NUMERIC(5,2),
    goal_mouth_z NUMERIC(5,2),
    blocked_x NUMERIC(5,2),
    blocked_y NUMERIC(5,2),

    -- Event Qualifiers (JSONB for flexibility)
    qualifiers JSONB,

    -- Flags
    is_touch BOOLEAN,
    is_shot BOOLEAN,
    is_goal BOOLEAN,

    -- Card Details (if applicable)
    card_type TEXT,  -- 'Yellow', 'Red', 'SecondYellow'

    -- Related Events
    related_event_id TEXT,
    related_player_id TEXT,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'whoscored',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_whoscored_events_league_season ON whoscored_events(league, season);
CREATE INDEX idx_whoscored_events_game ON whoscored_events(game);
CREATE INDEX idx_whoscored_events_game_id ON whoscored_events(game_id);
CREATE INDEX idx_whoscored_events_team ON whoscored_events(team);
CREATE INDEX idx_whoscored_events_player ON whoscored_events(player);
CREATE INDEX idx_whoscored_events_type ON whoscored_events(event_type);
CREATE INDEX idx_whoscored_events_period ON whoscored_events(period);
CREATE INDEX idx_whoscored_events_qualifiers ON whoscored_events USING GIN (qualifiers);
CREATE TRIGGER update_whoscored_events_updated_at BEFORE UPDATE ON whoscored_events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE whoscored_events IS 'WhoScored detailed Opta event stream data (most granular event data)';
COMMENT ON COLUMN whoscored_events.qualifiers IS 'Event qualifiers in JSONB format (pass type, shot type, etc.)';
COMMENT ON COLUMN whoscored_events.x IS 'X coordinate of event location (0-100)';
COMMENT ON COLUMN whoscored_events.y IS 'Y coordinate of event location (0-100)';
