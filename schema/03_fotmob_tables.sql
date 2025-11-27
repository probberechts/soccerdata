-- =============================================================================
-- FotMob Tables (11 tables total)
-- =============================================================================
-- Description: All tables for FotMob data source (fotmob.com)
-- Data: Opta-based statistics, league tables, team match stats
-- Tables: Metadata (2), League table (1), Schedule (1), Team match stats (7)
-- =============================================================================

\c football_stats

-- =============================================================================
-- LEAGUE & SEASON METADATA
-- =============================================================================

CREATE TABLE fotmob_leagues (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL UNIQUE,
    league_id INTEGER,
    country TEXT,
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'fotmob',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_fotmob_leagues_league_id ON fotmob_leagues(league_id);
CREATE TRIGGER update_fotmob_leagues_updated_at BEFORE UPDATE ON fotmob_leagues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fotmob_leagues IS 'FotMob league information';

-- -----------------------------------------------------------------------------

CREATE TABLE fotmob_seasons (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    season_id INTEGER,
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'fotmob',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(league, season)
);

CREATE INDEX idx_fotmob_seasons_league_season ON fotmob_seasons(league, season);
CREATE TRIGGER update_fotmob_seasons_updated_at BEFORE UPDATE ON fotmob_seasons
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fotmob_seasons IS 'FotMob season information';

-- =============================================================================
-- LEAGUE STANDINGS
-- =============================================================================

CREATE TABLE fotmob_league_table (
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
    data_source TEXT NOT NULL DEFAULT 'fotmob',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team)
);

CREATE INDEX idx_fotmob_league_table_league_season ON fotmob_league_table(league, season);
CREATE INDEX idx_fotmob_league_table_team ON fotmob_league_table(team);
CREATE INDEX idx_fotmob_league_table_points ON fotmob_league_table(points DESC);
CREATE TRIGGER update_fotmob_league_table_updated_at BEFORE UPDATE ON fotmob_league_table
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fotmob_league_table IS 'FotMob league standings/tables';

-- =============================================================================
-- MATCH SCHEDULE
-- =============================================================================

CREATE TABLE fotmob_schedule (
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
    game_id TEXT,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fotmob',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, game)
);

CREATE INDEX idx_fotmob_schedule_league_season ON fotmob_schedule(league, season);
CREATE INDEX idx_fotmob_schedule_date ON fotmob_schedule(date);
CREATE INDEX idx_fotmob_schedule_home_team ON fotmob_schedule(home_team);
CREATE INDEX idx_fotmob_schedule_away_team ON fotmob_schedule(away_team);
CREATE INDEX idx_fotmob_schedule_game_id ON fotmob_schedule(game_id);
CREATE TRIGGER update_fotmob_schedule_updated_at BEFORE UPDATE ON fotmob_schedule
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fotmob_schedule IS 'FotMob match schedule';

-- =============================================================================
-- TEAM MATCH STATISTICS (7 tables by stat type)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Team Match Top Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fotmob_team_match_top_stats (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,

    -- Top Stats (varies by match, using JSONB for flexibility)
    stats JSONB,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fotmob',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, game)
);

CREATE INDEX idx_fotmob_team_match_top_stats_league_season ON fotmob_team_match_top_stats(league, season);
CREATE INDEX idx_fotmob_team_match_top_stats_team ON fotmob_team_match_top_stats(team);
CREATE INDEX idx_fotmob_team_match_top_stats_game ON fotmob_team_match_top_stats(game);
CREATE INDEX idx_fotmob_team_match_top_stats_stats ON fotmob_team_match_top_stats USING GIN (stats);
CREATE TRIGGER update_fotmob_team_match_top_stats_updated_at BEFORE UPDATE ON fotmob_team_match_top_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fotmob_team_match_top_stats IS 'FotMob team match top statistics';

-- -----------------------------------------------------------------------------
-- Team Match Shots Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fotmob_team_match_shots (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,

    -- Shots
    total_shots INTEGER,
    shots_on_target INTEGER,
    shots_off_target INTEGER,
    shots_blocked INTEGER,
    shots_inside_box INTEGER,
    shots_outside_box INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fotmob',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, game)
);

CREATE INDEX idx_fotmob_team_match_shots_league_season ON fotmob_team_match_shots(league, season);
CREATE INDEX idx_fotmob_team_match_shots_team ON fotmob_team_match_shots(team);
CREATE INDEX idx_fotmob_team_match_shots_game ON fotmob_team_match_shots(game);
CREATE TRIGGER update_fotmob_team_match_shots_updated_at BEFORE UPDATE ON fotmob_team_match_shots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fotmob_team_match_shots IS 'FotMob team match shots statistics';

-- -----------------------------------------------------------------------------
-- Team Match Expected Goals Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fotmob_team_match_xg (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,

    -- Expected Goals
    xg NUMERIC(5,3),
    xg_open_play NUMERIC(5,3),
    xg_set_play NUMERIC(5,3),

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fotmob',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, game)
);

CREATE INDEX idx_fotmob_team_match_xg_league_season ON fotmob_team_match_xg(league, season);
CREATE INDEX idx_fotmob_team_match_xg_team ON fotmob_team_match_xg(team);
CREATE INDEX idx_fotmob_team_match_xg_game ON fotmob_team_match_xg(game);
CREATE TRIGGER update_fotmob_team_match_xg_updated_at BEFORE UPDATE ON fotmob_team_match_xg
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fotmob_team_match_xg IS 'FotMob team match expected goals statistics';

-- -----------------------------------------------------------------------------
-- Team Match Passes Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fotmob_team_match_passes (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,

    -- Passes
    total_passes INTEGER,
    accurate_passes INTEGER,
    pass_accuracy_pct NUMERIC(5,2),
    key_passes INTEGER,
    final_third_passes INTEGER,
    long_balls INTEGER,
    crosses INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fotmob',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, game)
);

CREATE INDEX idx_fotmob_team_match_passes_league_season ON fotmob_team_match_passes(league, season);
CREATE INDEX idx_fotmob_team_match_passes_team ON fotmob_team_match_passes(team);
CREATE INDEX idx_fotmob_team_match_passes_game ON fotmob_team_match_passes(game);
CREATE TRIGGER update_fotmob_team_match_passes_updated_at BEFORE UPDATE ON fotmob_team_match_passes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fotmob_team_match_passes IS 'FotMob team match passing statistics';

-- -----------------------------------------------------------------------------
-- Team Match Defence Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fotmob_team_match_defence (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,

    -- Defence
    tackles INTEGER,
    interceptions INTEGER,
    clearances INTEGER,
    blocked_shots INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fotmob',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, game)
);

CREATE INDEX idx_fotmob_team_match_defence_league_season ON fotmob_team_match_defence(league, season);
CREATE INDEX idx_fotmob_team_match_defence_team ON fotmob_team_match_defence(team);
CREATE INDEX idx_fotmob_team_match_defence_game ON fotmob_team_match_defence(game);
CREATE TRIGGER update_fotmob_team_match_defence_updated_at BEFORE UPDATE ON fotmob_team_match_defence
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fotmob_team_match_defence IS 'FotMob team match defensive statistics';

-- -----------------------------------------------------------------------------
-- Team Match Duels Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fotmob_team_match_duels (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,

    -- Duels
    total_duels INTEGER,
    duels_won INTEGER,
    duels_won_pct NUMERIC(5,2),
    ground_duels INTEGER,
    ground_duels_won INTEGER,
    aerial_duels INTEGER,
    aerial_duels_won INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fotmob',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, game)
);

CREATE INDEX idx_fotmob_team_match_duels_league_season ON fotmob_team_match_duels(league, season);
CREATE INDEX idx_fotmob_team_match_duels_team ON fotmob_team_match_duels(team);
CREATE INDEX idx_fotmob_team_match_duels_game ON fotmob_team_match_duels(game);
CREATE TRIGGER update_fotmob_team_match_duels_updated_at BEFORE UPDATE ON fotmob_team_match_duels
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fotmob_team_match_duels IS 'FotMob team match duels statistics';

-- -----------------------------------------------------------------------------
-- Team Match Discipline Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fotmob_team_match_discipline (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,

    -- Discipline
    fouls_committed INTEGER,
    fouls_drawn INTEGER,
    yellow_cards INTEGER,
    red_cards INTEGER,
    offsides INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fotmob',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, game)
);

CREATE INDEX idx_fotmob_team_match_discipline_league_season ON fotmob_team_match_discipline(league, season);
CREATE INDEX idx_fotmob_team_match_discipline_team ON fotmob_team_match_discipline(team);
CREATE INDEX idx_fotmob_team_match_discipline_game ON fotmob_team_match_discipline(game);
CREATE TRIGGER update_fotmob_team_match_discipline_updated_at BEFORE UPDATE ON fotmob_team_match_discipline
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fotmob_team_match_discipline IS 'FotMob team match discipline statistics (cards, fouls)';
