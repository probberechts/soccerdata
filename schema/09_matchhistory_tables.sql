-- =============================================================================
-- MatchHistory Tables (1 table from Football-Data.co.uk)
-- =============================================================================
-- Description: Historical match results with betting odds and statistics
-- Data: Results, betting odds from multiple bookmakers, match statistics
-- Note: Level of detail varies by league
-- =============================================================================

\c football_stats

-- =============================================================================
-- MATCH GAMES WITH BETTING ODDS AND STATISTICS
-- =============================================================================

CREATE TABLE matchhistory_games (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Information
    date TIMESTAMP WITH TIME ZONE NOT NULL,
    time TEXT,

    -- Teams
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,

    -- Full Time Result
    ft_home_goals INTEGER,
    ft_away_goals INTEGER,
    ft_result TEXT,  -- 'H', 'D', 'A'

    -- Half Time Result
    ht_home_goals INTEGER,
    ht_away_goals INTEGER,
    ht_result TEXT,  -- 'H', 'D', 'A'

    -- Match Officials
    referee TEXT,

    -- Match Statistics
    home_shots INTEGER,
    away_shots INTEGER,
    home_shots_on_target INTEGER,
    away_shots_on_target INTEGER,
    home_fouls INTEGER,
    away_fouls INTEGER,
    home_corners INTEGER,
    away_corners INTEGER,
    home_yellow_cards INTEGER,
    away_yellow_cards INTEGER,
    home_red_cards INTEGER,
    away_red_cards INTEGER,

    -- Betting Odds - Bet365 (Full Time Result)
    b365_home NUMERIC(6,2),
    b365_draw NUMERIC(6,2),
    b365_away NUMERIC(6,2),

    -- Betting Odds - Blue Square (Full Time Result)
    bs_home NUMERIC(6,2),
    bs_draw NUMERIC(6,2),
    bs_away NUMERIC(6,2),

    -- Betting Odds - Bet&Win (Full Time Result)
    bw_home NUMERIC(6,2),
    bw_draw NUMERIC(6,2),
    bw_away NUMERIC(6,2),

    -- Betting Odds - Gamebookers (Full Time Result)
    gb_home NUMERIC(6,2),
    gb_draw NUMERIC(6,2),
    gb_away NUMERIC(6,2),

    -- Betting Odds - Interwetten (Full Time Result)
    iw_home NUMERIC(6,2),
    iw_draw NUMERIC(6,2),
    iw_away NUMERIC(6,2),

    -- Betting Odds - Ladbrokes (Full Time Result)
    lb_home NUMERIC(6,2),
    lb_draw NUMERIC(6,2),
    lb_away NUMERIC(6,2),

    -- Betting Odds - Pinnacle (Full Time Result)
    ps_home NUMERIC(6,2),
    ps_draw NUMERIC(6,2),
    ps_away NUMERIC(6,2),

    -- Betting Odds - Sporting Odds (Full Time Result)
    so_home NUMERIC(6,2),
    so_draw NUMERIC(6,2),
    so_away NUMERIC(6,2),

    -- Betting Odds - Sportingbet (Full Time Result)
    sb_home NUMERIC(6,2),
    sb_draw NUMERIC(6,2),
    sb_away NUMERIC(6,2),

    -- Betting Odds - Stan James (Full Time Result)
    sj_home NUMERIC(6,2),
    sj_draw NUMERIC(6,2),
    sj_away NUMERIC(6,2),

    -- Betting Odds - Stanleybet (Full Time Result)
    sy_home NUMERIC(6,2),
    sy_draw NUMERIC(6,2),
    sy_away NUMERIC(6,2),

    -- Betting Odds - VC Bet (Full Time Result)
    vc_home NUMERIC(6,2),
    vc_draw NUMERIC(6,2),
    vc_away NUMERIC(6,2),

    -- Betting Odds - William Hill (Full Time Result)
    wh_home NUMERIC(6,2),
    wh_draw NUMERIC(6,2),
    wh_away NUMERIC(6,2),

    -- Market Averages and Market Size
    avg_home NUMERIC(6,2),
    avg_draw NUMERIC(6,2),
    avg_away NUMERIC(6,2),
    market_size INTEGER,  -- Number of bookmakers in the market

    -- Betting Odds - Over/Under 2.5 Goals
    b365_over_2_5 NUMERIC(6,2),
    b365_under_2_5 NUMERIC(6,2),
    ps_over_2_5 NUMERIC(6,2),
    ps_under_2_5 NUMERIC(6,2),
    avg_over_2_5 NUMERIC(6,2),
    avg_under_2_5 NUMERIC(6,2),

    -- Betting Odds - Asian Handicap
    b365_ah NUMERIC(5,2),      -- Asian Handicap size
    b365_ah_home NUMERIC(6,2), -- Home team Asian Handicap odds
    b365_ah_away NUMERIC(6,2), -- Away team Asian Handicap odds
    ps_ah NUMERIC(5,2),
    ps_ah_home NUMERIC(6,2),
    ps_ah_away NUMERIC(6,2),
    avg_ah NUMERIC(5,2),
    avg_ah_home NUMERIC(6,2),
    avg_ah_away NUMERIC(6,2),

    -- Closing Odds (some bookmakers)
    ps_close_home NUMERIC(6,2),
    ps_close_draw NUMERIC(6,2),
    ps_close_away NUMERIC(6,2),

    -- Total Goals Betting
    total_goals_home INTEGER,
    total_goals_away INTEGER,

    -- Additional Dynamic Columns
    -- Note: This table may have additional columns depending on league and season
    -- Use JSONB for any additional data not captured in fixed columns
    additional_data JSONB,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'matchhistory',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, game)
);

CREATE INDEX idx_matchhistory_games_league_season ON matchhistory_games(league, season);
CREATE INDEX idx_matchhistory_games_date ON matchhistory_games(date);
CREATE INDEX idx_matchhistory_games_home_team ON matchhistory_games(home_team);
CREATE INDEX idx_matchhistory_games_away_team ON matchhistory_games(away_team);
CREATE INDEX idx_matchhistory_games_referee ON matchhistory_games(referee);
CREATE INDEX idx_matchhistory_games_ft_result ON matchhistory_games(ft_result);
CREATE INDEX idx_matchhistory_games_additional_data ON matchhistory_games USING GIN (additional_data);
CREATE TRIGGER update_matchhistory_games_updated_at BEFORE UPDATE ON matchhistory_games
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE matchhistory_games IS 'Historical match results with betting odds from multiple bookmakers (Football-Data.co.uk)';
COMMENT ON COLUMN matchhistory_games.ft_result IS 'Full Time result: H=Home win, D=Draw, A=Away win';
COMMENT ON COLUMN matchhistory_games.ht_result IS 'Half Time result: H=Home win, D=Draw, A=Away win';
COMMENT ON COLUMN matchhistory_games.b365_home IS 'Bet365 odds for home win';
COMMENT ON COLUMN matchhistory_games.avg_home IS 'Average market odds for home win';
COMMENT ON COLUMN matchhistory_games.market_size IS 'Number of bookmakers contributing to market averages';
COMMENT ON COLUMN matchhistory_games.b365_ah IS 'Bet365 Asian Handicap size (e.g., -0.5, 0.0, +0.5)';
COMMENT ON COLUMN matchhistory_games.additional_data IS 'JSONB field for league-specific columns not captured in fixed schema';
