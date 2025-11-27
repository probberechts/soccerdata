-- =============================================================================
-- SoFIFA Tables (6 tables total)
-- =============================================================================
-- Description: All tables for SoFIFA data source (sofifa.com)
-- Data: EA Sports FC player ratings and abilities
-- Tables: Metadata (2), Teams (1), Players (1), Ratings (2)
-- =============================================================================

\c football_stats

-- =============================================================================
-- LEAGUE & VERSION METADATA
-- =============================================================================

CREATE TABLE sofifa_leagues (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL UNIQUE,
    league_id INTEGER NOT NULL,
    data_source TEXT NOT NULL DEFAULT 'sofifa',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sofifa_leagues_league_id ON sofifa_leagues(league_id);
CREATE TRIGGER update_sofifa_leagues_updated_at BEFORE UPDATE ON sofifa_leagues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE sofifa_leagues IS 'SoFIFA league information';

-- -----------------------------------------------------------------------------

CREATE TABLE sofifa_versions (
    id SERIAL PRIMARY KEY,
    version_id INTEGER NOT NULL UNIQUE,
    fifa_edition TEXT NOT NULL,
    update_name TEXT NOT NULL,
    data_source TEXT NOT NULL DEFAULT 'sofifa',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_sofifa_versions_version_id ON sofifa_versions(version_id);
CREATE INDEX idx_sofifa_versions_fifa_edition ON sofifa_versions(fifa_edition);
CREATE TRIGGER update_sofifa_versions_updated_at BEFORE UPDATE ON sofifa_versions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE sofifa_versions IS 'FIFA game versions and rating updates';

-- =============================================================================
-- TEAMS
-- =============================================================================

CREATE TABLE sofifa_teams (
    id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL,
    team TEXT NOT NULL,
    league TEXT NOT NULL,
    version_id INTEGER NOT NULL,
    fifa_edition TEXT,
    update_name TEXT,
    data_source TEXT NOT NULL DEFAULT 'sofifa',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(team_id, version_id)
);

CREATE INDEX idx_sofifa_teams_team_id ON sofifa_teams(team_id);
CREATE INDEX idx_sofifa_teams_team ON sofifa_teams(team);
CREATE INDEX idx_sofifa_teams_league ON sofifa_teams(league);
CREATE INDEX idx_sofifa_teams_version_id ON sofifa_teams(version_id);
CREATE TRIGGER update_sofifa_teams_updated_at BEFORE UPDATE ON sofifa_teams
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE sofifa_teams IS 'SoFIFA team information';

-- =============================================================================
-- PLAYERS
-- =============================================================================

CREATE TABLE sofifa_players (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL,
    player TEXT NOT NULL,
    team TEXT NOT NULL,
    league TEXT NOT NULL,
    version_id INTEGER NOT NULL,
    fifa_edition TEXT,
    update_name TEXT,
    data_source TEXT NOT NULL DEFAULT 'sofifa',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(player_id, version_id)
);

CREATE INDEX idx_sofifa_players_player_id ON sofifa_players(player_id);
CREATE INDEX idx_sofifa_players_player ON sofifa_players(player);
CREATE INDEX idx_sofifa_players_team ON sofifa_players(team);
CREATE INDEX idx_sofifa_players_league ON sofifa_players(league);
CREATE INDEX idx_sofifa_players_version_id ON sofifa_players(version_id);
CREATE TRIGGER update_sofifa_players_updated_at BEFORE UPDATE ON sofifa_players
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE sofifa_players IS 'SoFIFA player information';

-- =============================================================================
-- TEAM RATINGS
-- =============================================================================

CREATE TABLE sofifa_team_ratings (
    id SERIAL PRIMARY KEY,
    team TEXT NOT NULL,
    team_id INTEGER NOT NULL,
    league TEXT NOT NULL,
    version_id INTEGER NOT NULL,
    fifa_edition TEXT,

    -- Ratings
    overall_rating INTEGER,
    attack_rating INTEGER,
    midfield_rating INTEGER,
    defense_rating INTEGER,
    transfer_budget NUMERIC(15,2),

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'sofifa',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(team_id, version_id)
);

CREATE INDEX idx_sofifa_team_ratings_team ON sofifa_team_ratings(team);
CREATE INDEX idx_sofifa_team_ratings_league ON sofifa_team_ratings(league);
CREATE INDEX idx_sofifa_team_ratings_version_id ON sofifa_team_ratings(version_id);
CREATE INDEX idx_sofifa_team_ratings_overall ON sofifa_team_ratings(overall_rating DESC);
CREATE TRIGGER update_sofifa_team_ratings_updated_at BEFORE UPDATE ON sofifa_team_ratings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE sofifa_team_ratings IS 'SoFIFA team ratings (overall, attack, midfield, defense, transfer budget)';

-- =============================================================================
-- PLAYER RATINGS
-- =============================================================================

CREATE TABLE sofifa_player_ratings (
    id SERIAL PRIMARY KEY,
    player TEXT NOT NULL,
    player_id INTEGER NOT NULL,
    team TEXT NOT NULL,
    league TEXT NOT NULL,
    version_id INTEGER NOT NULL,
    fifa_edition TEXT,

    -- Basic Info
    position TEXT,
    age INTEGER,
    nationality TEXT,

    -- Overall Ratings
    overall_rating INTEGER,
    potential_rating INTEGER,

    -- Attributes (storing as JSONB for flexibility - EA changes these frequently)
    attributes JSONB,

    -- Physical
    height_cm INTEGER,
    weight_kg INTEGER,

    -- Value
    value_eur NUMERIC(15,2),
    wage_eur NUMERIC(15,2),
    release_clause_eur NUMERIC(15,2),

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'sofifa',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(player_id, version_id)
);

CREATE INDEX idx_sofifa_player_ratings_player ON sofifa_player_ratings(player);
CREATE INDEX idx_sofifa_player_ratings_team ON sofifa_player_ratings(team);
CREATE INDEX idx_sofifa_player_ratings_league ON sofifa_player_ratings(league);
CREATE INDEX idx_sofifa_player_ratings_version_id ON sofifa_player_ratings(version_id);
CREATE INDEX idx_sofifa_player_ratings_overall ON sofifa_player_ratings(overall_rating DESC);
CREATE INDEX idx_sofifa_player_ratings_position ON sofifa_player_ratings(position);
CREATE INDEX idx_sofifa_player_ratings_attributes ON sofifa_player_ratings USING GIN (attributes);
CREATE TRIGGER update_sofifa_player_ratings_updated_at BEFORE UPDATE ON sofifa_player_ratings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE sofifa_player_ratings IS 'SoFIFA player ratings and abilities from EA Sports FC';
COMMENT ON COLUMN sofifa_player_ratings.attributes IS 'Player attributes in JSONB format (pace, shooting, passing, dribbling, defending, physical, etc.)';
