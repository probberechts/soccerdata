-- =============================================================================
-- ClubElo Tables (2 tables total)
-- =============================================================================
-- Description: All tables for ClubElo data source (clubelo.com)
-- Data: Team strength ratings using ELO system
-- Tables: Ratings by date (1), Team history (1)
-- =============================================================================

\c football_stats

-- =============================================================================
-- ELO RATINGS BY DATE
-- =============================================================================

CREATE TABLE clubelo_ratings_daily (
    id SERIAL PRIMARY KEY,
    team TEXT NOT NULL,
    date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- League
    league TEXT,
    country TEXT,
    level INTEGER,

    -- ELO Ratings
    rank NUMERIC(10,2),
    elo NUMERIC(10,2),

    -- Date Range
    from_date TIMESTAMP WITH TIME ZONE,
    to_date TIMESTAMP WITH TIME ZONE,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'clubelo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(team, date)
);

CREATE INDEX idx_clubelo_ratings_daily_team ON clubelo_ratings_daily(team);
CREATE INDEX idx_clubelo_ratings_daily_date ON clubelo_ratings_daily(date);
CREATE INDEX idx_clubelo_ratings_daily_league ON clubelo_ratings_daily(league);
CREATE INDEX idx_clubelo_ratings_daily_elo ON clubelo_ratings_daily(elo DESC);
CREATE INDEX idx_clubelo_ratings_daily_rank ON clubelo_ratings_daily(rank);
CREATE TRIGGER update_clubelo_ratings_daily_updated_at BEFORE UPDATE ON clubelo_ratings_daily
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE clubelo_ratings_daily IS 'ClubElo ratings by date (snapshot approach)';
COMMENT ON COLUMN clubelo_ratings_daily.elo IS 'ELO rating (higher is better)';
COMMENT ON COLUMN clubelo_ratings_daily.rank IS 'Global rank based on ELO';

-- =============================================================================
-- TEAM ELO HISTORY
-- =============================================================================

CREATE TABLE clubelo_team_history (
    id SERIAL PRIMARY KEY,
    team TEXT NOT NULL,
    from_date TIMESTAMP WITH TIME ZONE NOT NULL,

    -- ELO Rating
    elo NUMERIC(10,2),
    rank NUMERIC(10,2),

    -- League
    country TEXT,
    level INTEGER,

    -- Date Range
    to_date TIMESTAMP WITH TIME ZONE,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'clubelo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(team, from_date)
);

CREATE INDEX idx_clubelo_team_history_team ON clubelo_team_history(team);
CREATE INDEX idx_clubelo_team_history_from_date ON clubelo_team_history(from_date);
CREATE INDEX idx_clubelo_team_history_elo ON clubelo_team_history(elo DESC);
CREATE TRIGGER update_clubelo_team_history_updated_at BEFORE UPDATE ON clubelo_team_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE clubelo_team_history IS 'Complete historical ELO ratings per team';
COMMENT ON COLUMN clubelo_team_history.from_date IS 'Start date for this ELO rating period';
COMMENT ON COLUMN clubelo_team_history.to_date IS 'End date for this ELO rating period';
