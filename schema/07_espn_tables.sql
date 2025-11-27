-- =============================================================================
-- ESPN Tables (3 tables total)
-- =============================================================================
-- Description: All tables for ESPN data source (site.api.espn.com)
-- Data: Match schedules, lineups, match sheets with statistics
-- Tables: Schedule (1), Matchsheet (1), Lineup (1)
-- =============================================================================

\c football_stats

-- =============================================================================
-- MATCH SCHEDULE
-- =============================================================================

CREATE TABLE espn_schedule (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Information
    date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Teams
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,

    -- IDs
    game_id INTEGER NOT NULL,
    league_id TEXT,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'espn',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, game)
);

CREATE INDEX idx_espn_schedule_league_season ON espn_schedule(league, season);
CREATE INDEX idx_espn_schedule_date ON espn_schedule(date);
CREATE INDEX idx_espn_schedule_home_team ON espn_schedule(home_team);
CREATE INDEX idx_espn_schedule_away_team ON espn_schedule(away_team);
CREATE INDEX idx_espn_schedule_game_id ON espn_schedule(game_id);
CREATE TRIGGER update_espn_schedule_updated_at BEFORE UPDATE ON espn_schedule
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE espn_schedule IS 'ESPN match schedule';

-- =============================================================================
-- MATCH SHEETS
-- =============================================================================

CREATE TABLE espn_matchsheet (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    game TEXT NOT NULL,
    team TEXT NOT NULL,

    -- Match Info
    is_home BOOLEAN,
    venue TEXT,
    attendance INTEGER,
    capacity INTEGER,

    -- Match Statistics (stored as JSONB for flexibility)
    statistics JSONB,

    -- Roster (stored as JSONB)
    roster JSONB,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'espn',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, game, team)
);

CREATE INDEX idx_espn_matchsheet_league_season ON espn_matchsheet(league, season);
CREATE INDEX idx_espn_matchsheet_game ON espn_matchsheet(game);
CREATE INDEX idx_espn_matchsheet_team ON espn_matchsheet(team);
CREATE INDEX idx_espn_matchsheet_statistics ON espn_matchsheet USING GIN (statistics);
CREATE INDEX idx_espn_matchsheet_roster ON espn_matchsheet USING GIN (roster);
CREATE TRIGGER update_espn_matchsheet_updated_at BEFORE UPDATE ON espn_matchsheet
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE espn_matchsheet IS 'ESPN match sheets with statistics and venue information';
COMMENT ON COLUMN espn_matchsheet.statistics IS 'Match statistics in JSONB format';
COMMENT ON COLUMN espn_matchsheet.roster IS 'Player roster in JSONB format';

-- =============================================================================
-- MATCH LINEUPS
-- =============================================================================

CREATE TABLE espn_lineup (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    game TEXT NOT NULL,
    team TEXT NOT NULL,
    player TEXT NOT NULL,

    -- Match Info
    is_home BOOLEAN,

    -- Player Info
    position TEXT,
    formation_place INTEGER,

    -- Substitution Info
    sub_in TEXT,  -- 'start' or minute substituted in
    sub_out TEXT, -- Minute substituted out or NULL if not subbed out

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'espn',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, game, team, player)
);

CREATE INDEX idx_espn_lineup_league_season ON espn_lineup(league, season);
CREATE INDEX idx_espn_lineup_game ON espn_lineup(game);
CREATE INDEX idx_espn_lineup_team ON espn_lineup(team);
CREATE INDEX idx_espn_lineup_player ON espn_lineup(player);
CREATE TRIGGER update_espn_lineup_updated_at BEFORE UPDATE ON espn_lineup
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE espn_lineup IS 'ESPN match lineups with formation and substitution data';
