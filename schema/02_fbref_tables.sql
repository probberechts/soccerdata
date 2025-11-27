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

-- =============================================================================
-- TEAM SEASON STATISTICS - Remaining Tables
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Team Season Shooting Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_season_shooting (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,

    -- Playing Time
    players_used INTEGER,
    minutes_per_90 NUMERIC(5,1),

    -- Standard Shooting
    goals INTEGER,
    shots INTEGER,
    shots_on_target INTEGER,
    shots_on_target_pct NUMERIC(5,2),
    shots_per_90 NUMERIC(4,2),
    shots_on_target_per_90 NUMERIC(4,2),
    goals_per_shot NUMERIC(4,3),
    goals_per_shot_on_target NUMERIC(4,3),
    
    -- Distance
    average_shot_distance NUMERIC(5,2),
    
    -- Free Kicks
    shots_free_kicks INTEGER,
    
    -- Penalty Kicks
    penalty_kicks INTEGER,
    penalty_kicks_attempted INTEGER,
    
    -- Expected Goals
    xg NUMERIC(6,2),
    npxg NUMERIC(6,2),
    npxg_per_shot NUMERIC(4,3),
    goals_minus_xg NUMERIC(6,2),
    non_penalty_goals_minus_npxg NUMERIC(6,2),

    -- Metadata
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team)
);

CREATE INDEX idx_fbref_team_season_shooting_league_season ON fbref_team_season_shooting(league, season);
CREATE INDEX idx_fbref_team_season_shooting_team ON fbref_team_season_shooting(team);
CREATE TRIGGER update_fbref_team_season_shooting_updated_at BEFORE UPDATE ON fbref_team_season_shooting
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_season_shooting IS 'FBref team season shooting statistics';

-- -----------------------------------------------------------------------------
-- Team Season Passing Types Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_season_passing_types (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,

    -- Playing Time
    players_used INTEGER,
    minutes_per_90 NUMERIC(5,1),

    -- Pass Types
    passes_attempted INTEGER,
    passes_live INTEGER,
    passes_dead INTEGER,
    passes_free_kicks INTEGER,
    through_balls INTEGER,
    switches INTEGER,
    crosses INTEGER,
    throw_ins INTEGER,
    corner_kicks INTEGER,
    
    -- Corner Kicks
    corner_kicks_in INTEGER,
    corner_kicks_out INTEGER,
    corner_kicks_straight INTEGER,
    
    -- Outcomes
    passes_completed INTEGER,
    passes_offside INTEGER,
    passes_blocked INTEGER,

    -- Metadata
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team)
);

CREATE INDEX idx_fbref_team_season_passing_types_league_season ON fbref_team_season_passing_types(league, season);
CREATE INDEX idx_fbref_team_season_passing_types_team ON fbref_team_season_passing_types(team);
CREATE TRIGGER update_fbref_team_season_passing_types_updated_at BEFORE UPDATE ON fbref_team_season_passing_types
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_season_passing_types IS 'FBref team season passing types statistics';

-- -----------------------------------------------------------------------------
-- Team Season Goal and Shot Creation Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_season_goal_shot_creation (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,

    -- Playing Time
    players_used INTEGER,
    minutes_per_90 NUMERIC(5,1),

    -- Shot Creating Actions (SCA)
    sca INTEGER,
    sca_per_90 NUMERIC(4,2),
    sca_passes_live INTEGER,
    sca_passes_dead INTEGER,
    sca_take_ons INTEGER,
    sca_shots INTEGER,
    sca_fouled INTEGER,
    sca_defense INTEGER,
    
    -- Goal Creating Actions (GCA)
    gca INTEGER,
    gca_per_90 NUMERIC(4,2),
    gca_passes_live INTEGER,
    gca_passes_dead INTEGER,
    gca_take_ons INTEGER,
    gca_shots INTEGER,
    gca_fouled INTEGER,
    gca_defense INTEGER,

    -- Metadata
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team)
);

CREATE INDEX idx_fbref_team_season_gsc_league_season ON fbref_team_season_goal_shot_creation(league, season);
CREATE INDEX idx_fbref_team_season_gsc_team ON fbref_team_season_goal_shot_creation(team);
CREATE TRIGGER update_fbref_team_season_gsc_updated_at BEFORE UPDATE ON fbref_team_season_goal_shot_creation
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_season_goal_shot_creation IS 'FBref team season goal and shot creation statistics';

-- -----------------------------------------------------------------------------
-- Team Season Defense Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_season_defense (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,

    -- Playing Time
    players_used INTEGER,
    minutes_per_90 NUMERIC(5,1),

    -- Tackles
    tackles INTEGER,
    tackles_won INTEGER,
    tackles_def_3rd INTEGER,
    tackles_mid_3rd INTEGER,
    tackles_att_3rd INTEGER,
    
    -- Challenges
    challenge_tackles INTEGER,
    challenges INTEGER,
    challenge_tackles_pct NUMERIC(5,2),
    challenges_lost INTEGER,
    
    -- Blocks
    blocks INTEGER,
    blocked_shots INTEGER,
    blocked_passes INTEGER,
    
    -- Interceptions
    interceptions INTEGER,
    tackles_plus_interceptions INTEGER,
    
    -- Clearances and Errors
    clearances INTEGER,
    errors INTEGER,

    -- Metadata
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team)
);

CREATE INDEX idx_fbref_team_season_defense_league_season ON fbref_team_season_defense(league, season);
CREATE INDEX idx_fbref_team_season_defense_team ON fbref_team_season_defense(team);
CREATE TRIGGER update_fbref_team_season_defense_updated_at BEFORE UPDATE ON fbref_team_season_defense
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_season_defense IS 'FBref team season defensive statistics';

-- -----------------------------------------------------------------------------
-- Team Season Possession Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_season_possession (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,

    -- Playing Time
    players_used INTEGER,
    minutes_per_90 NUMERIC(5,1),

    -- Touches
    touches INTEGER,
    touches_def_pen_area INTEGER,
    touches_def_3rd INTEGER,
    touches_mid_3rd INTEGER,
    touches_att_3rd INTEGER,
    touches_att_pen_area INTEGER,
    touches_live_ball INTEGER,
    
    -- Take-Ons
    take_ons_attempted INTEGER,
    take_ons_successful INTEGER,
    take_ons_success_pct NUMERIC(5,2),
    take_ons_tackled INTEGER,
    take_ons_tackled_pct NUMERIC(5,2),
    
    -- Carries
    carries INTEGER,
    carry_distance INTEGER,
    carry_progressive_distance INTEGER,
    progressive_carries INTEGER,
    carries_into_final_third INTEGER,
    carries_into_penalty_area INTEGER,
    
    -- Miscontrols and Dispossessions
    miscontrols INTEGER,
    dispossessed INTEGER,
    
    -- Receiving
    passes_received INTEGER,
    progressive_passes_received INTEGER,

    -- Metadata
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team)
);

CREATE INDEX idx_fbref_team_season_possession_league_season ON fbref_team_season_possession(league, season);
CREATE INDEX idx_fbref_team_season_possession_team ON fbref_team_season_possession(team);
CREATE TRIGGER update_fbref_team_season_possession_updated_at BEFORE UPDATE ON fbref_team_season_possession
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_season_possession IS 'FBref team season possession statistics';


-- -----------------------------------------------------------------------------
-- Team Season Playing Time Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_season_playing_time (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,

    -- Playing Time
    players_used INTEGER,
    age_avg NUMERIC(4,1),
    minutes INTEGER,
    minutes_per_90 NUMERIC(5,1),
    
    -- Performance
    games_played INTEGER,
    minutes_played INTEGER,
    minutes_per_game NUMERIC(5,1),
    minutes_pct NUMERIC(5,2),
    minutes_per_90_played NUMERIC(5,1),
    
    -- Starts
    games_started INTEGER,
    minutes_per_start NUMERIC(5,1),
    games_complete INTEGER,
    
    -- Subs
    games_subs INTEGER,
    minutes_per_sub NUMERIC(5,1),
    unused_sub INTEGER,
    
    -- Team Success
    points_per_match NUMERIC(4,2),
    on_goals_for INTEGER,
    on_goals_against INTEGER,
    plus_minus INTEGER,
    plus_minus_per_90 NUMERIC(4,2),
    
    -- Expected Team Success
    on_xg_for NUMERIC(6,2),
    on_xg_against NUMERIC(6,2),
    xg_plus_minus NUMERIC(6,2),
    xg_plus_minus_per_90 NUMERIC(4,2),

    -- Metadata
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team)
);

CREATE INDEX idx_fbref_team_season_playing_time_league_season ON fbref_team_season_playing_time(league, season);
CREATE INDEX idx_fbref_team_season_playing_time_team ON fbref_team_season_playing_time(team);
CREATE TRIGGER update_fbref_team_season_playing_time_updated_at BEFORE UPDATE ON fbref_team_season_playing_time
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_season_playing_time IS 'FBref team season playing time statistics';

-- -----------------------------------------------------------------------------
-- Team Season Miscellaneous Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_season_misc (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,

    -- Playing Time
    players_used INTEGER,
    minutes_per_90 NUMERIC(5,1),

    -- Performance
    cards_yellow INTEGER,
    cards_red INTEGER,
    cards_yellow_red INTEGER,
    fouls INTEGER,
    fouled INTEGER,
    offsides INTEGER,
    crosses INTEGER,
    interceptions INTEGER,
    tackles_won INTEGER,
    penalty_kicks_won INTEGER,
    penalty_kicks_conceded INTEGER,
    own_goals INTEGER,
    
    -- Ball Recoveries
    ball_recoveries INTEGER,
    
    -- Aerial Duels
    aerials_won INTEGER,
    aerials_lost INTEGER,
    aerials_won_pct NUMERIC(5,2),

    -- Metadata
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team)
);

CREATE INDEX idx_fbref_team_season_misc_league_season ON fbref_team_season_misc(league, season);
CREATE INDEX idx_fbref_team_season_misc_team ON fbref_team_season_misc(team);
CREATE TRIGGER update_fbref_team_season_misc_updated_at BEFORE UPDATE ON fbref_team_season_misc
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_season_misc IS 'FBref team season miscellaneous statistics';

-- -----------------------------------------------------------------------------
-- Team Season Goalkeeper Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_season_keeper (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,

    -- Playing Time
    players_used INTEGER,
    minutes_per_90 NUMERIC(5,1),
    
    -- Performance
    goals_against INTEGER,
    goals_against_per_90 NUMERIC(4,2),
    shots_on_target_against INTEGER,
    saves INTEGER,
    save_pct NUMERIC(5,2),
    wins INTEGER,
    draws INTEGER,
    losses INTEGER,
    clean_sheets INTEGER,
    clean_sheet_pct NUMERIC(5,2),
    
    -- Penalty Kicks
    penalty_kicks_attempted INTEGER,
    penalty_kicks_allowed INTEGER,
    penalty_kicks_saved INTEGER,
    penalty_kicks_missed INTEGER,
    penalty_kick_save_pct NUMERIC(5,2),

    -- Metadata
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team)
);

CREATE INDEX idx_fbref_team_season_keeper_league_season ON fbref_team_season_keeper(league, season);
CREATE INDEX idx_fbref_team_season_keeper_team ON fbref_team_season_keeper(team);
CREATE TRIGGER update_fbref_team_season_keeper_updated_at BEFORE UPDATE ON fbref_team_season_keeper
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_season_keeper IS 'FBref team season goalkeeper statistics';

-- -----------------------------------------------------------------------------
-- Team Season Advanced Goalkeeper Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_season_keeper_adv (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,

    -- Playing Time
    players_used INTEGER,
    minutes_per_90 NUMERIC(5,1),
    
    -- Goals Against
    goals_against INTEGER,
    penalty_kicks_allowed INTEGER,
    free_kick_goals_against INTEGER,
    corner_kick_goals_against INTEGER,
    own_goals_against INTEGER,
    
    -- Expected
    post_shot_xg NUMERIC(6,2),
    post_shot_xg_per_shot_on_target NUMERIC(4,3),
    post_shot_xg_minus_goals_allowed NUMERIC(6,2),
    
    -- Launched
    passes_completed_launched INTEGER,
    passes_launched INTEGER,
    passes_completed_launched_pct NUMERIC(5,2),
    
    -- Passes
    passes_attempted INTEGER,
    throws_attempted INTEGER,
    launch_pct NUMERIC(5,2),
    avg_pass_length NUMERIC(5,2),
    
    -- Goal Kicks
    goal_kicks_attempted INTEGER,
    goal_kick_launch_pct NUMERIC(5,2),
    avg_goal_kick_length NUMERIC(5,2),
    
    -- Crosses
    crosses_faced INTEGER,
    crosses_stopped INTEGER,
    crosses_stopped_pct NUMERIC(5,2),
    
    -- Sweeper
    def_actions_outside_pen_area INTEGER,
    def_actions_outside_pen_area_per_90 NUMERIC(4,2),
    avg_distance_def_actions NUMERIC(5,2),

    -- Metadata
    url TEXT,
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team)
);

CREATE INDEX idx_fbref_team_season_keeper_adv_league_season ON fbref_team_season_keeper_adv(league, season);
CREATE INDEX idx_fbref_team_season_keeper_adv_team ON fbref_team_season_keeper_adv(team);
CREATE TRIGGER update_fbref_team_season_keeper_adv_updated_at BEFORE UPDATE ON fbref_team_season_keeper_adv
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_season_keeper_adv IS 'FBref team season advanced goalkeeper statistics';


-- =============================================================================
-- TEAM MATCH STATISTICS (9 tables - match-level data per team)
-- =============================================================================

-- Note: fbref_team_match_schedule already created as fbref_schedule

-- -----------------------------------------------------------------------------
-- Team Match Keeper Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_match_keeper (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,
    venue TEXT,
    result TEXT,
    
    -- Performance
    goals_against INTEGER,
    shots_on_target_against INTEGER,
    saves INTEGER,
    save_pct NUMERIC(5,2),
    post_shot_xg NUMERIC(5,3),
    post_shot_xg_minus_goals_allowed NUMERIC(5,3),
    
    -- Launched Passes
    passes_completed_launched INTEGER,
    passes_launched INTEGER,
    passes_completed_launched_pct NUMERIC(5,2),
    
    -- Passes
    passes_attempted INTEGER,
    throws_attempted INTEGER,
    launch_pct NUMERIC(5,2),
    avg_pass_length NUMERIC(5,2),
    
    -- Goal Kicks
    goal_kicks_attempted INTEGER,
    goal_kick_launch_pct NUMERIC(5,2),
    avg_goal_kick_length NUMERIC(5,2),
    
    -- Crosses
    crosses_faced INTEGER,
    crosses_stopped INTEGER,
    crosses_stopped_pct NUMERIC(5,2),
    
    -- Sweeper
    def_actions_outside_pen_area INTEGER,
    avg_distance_def_actions NUMERIC(5,2),

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, game)
);

CREATE INDEX idx_fbref_team_match_keeper_league_season ON fbref_team_match_keeper(league, season);
CREATE INDEX idx_fbref_team_match_keeper_team ON fbref_team_match_keeper(team);
CREATE INDEX idx_fbref_team_match_keeper_game ON fbref_team_match_keeper(game);
CREATE TRIGGER update_fbref_team_match_keeper_updated_at BEFORE UPDATE ON fbref_team_match_keeper
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_match_keeper IS 'FBref team match goalkeeper statistics';

-- -----------------------------------------------------------------------------
-- Team Match Shooting Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_match_shooting (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,
    venue TEXT,
    result TEXT,
    
    -- Standard Shooting
    goals INTEGER,
    shots INTEGER,
    shots_on_target INTEGER,
    shots_on_target_pct NUMERIC(5,2),
    goals_per_shot NUMERIC(4,3),
    goals_per_shot_on_target NUMERIC(4,3),
    average_shot_distance NUMERIC(5,2),
    shots_free_kicks INTEGER,
    
    -- Penalty Kicks
    penalty_kicks INTEGER,
    penalty_kicks_attempted INTEGER,
    
    -- Expected Goals
    xg NUMERIC(5,3),
    npxg NUMERIC(5,3),
    npxg_per_shot NUMERIC(4,3),
    goals_minus_xg NUMERIC(5,3),
    non_penalty_goals_minus_npxg NUMERIC(5,3),

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, game)
);

CREATE INDEX idx_fbref_team_match_shooting_league_season ON fbref_team_match_shooting(league, season);
CREATE INDEX idx_fbref_team_match_shooting_team ON fbref_team_match_shooting(team);
CREATE INDEX idx_fbref_team_match_shooting_game ON fbref_team_match_shooting(game);
CREATE TRIGGER update_fbref_team_match_shooting_updated_at BEFORE UPDATE ON fbref_team_match_shooting
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_match_shooting IS 'FBref team match shooting statistics';

-- -----------------------------------------------------------------------------
-- Team Match Passing Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_match_passing (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,
    venue TEXT,
    result TEXT,
    
    -- Total Passing
    passes_completed INTEGER,
    passes_attempted INTEGER,
    pass_completion_pct NUMERIC(5,2),
    total_pass_distance INTEGER,
    progressive_pass_distance INTEGER,
    
    -- Short/Medium/Long Passing
    short_passes_completed INTEGER,
    short_passes_attempted INTEGER,
    short_pass_completion_pct NUMERIC(5,2),
    medium_passes_completed INTEGER,
    medium_passes_attempted INTEGER,
    medium_pass_completion_pct NUMERIC(5,2),
    long_passes_completed INTEGER,
    long_passes_attempted INTEGER,
    long_pass_completion_pct NUMERIC(5,2),
    
    -- Expected
    assists INTEGER,
    xag NUMERIC(5,3),
    expected_assists NUMERIC(5,3),
    assists_minus_expected NUMERIC(5,3),
    
    -- Key Passes
    key_passes INTEGER,
    passes_into_final_third INTEGER,
    passes_into_penalty_area INTEGER,
    crosses_into_penalty_area INTEGER,
    progressive_passes INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, game)
);

CREATE INDEX idx_fbref_team_match_passing_league_season ON fbref_team_match_passing(league, season);
CREATE INDEX idx_fbref_team_match_passing_team ON fbref_team_match_passing(team);
CREATE INDEX idx_fbref_team_match_passing_game ON fbref_team_match_passing(game);
CREATE TRIGGER update_fbref_team_match_passing_updated_at BEFORE UPDATE ON fbref_team_match_passing
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_match_passing IS 'FBref team match passing statistics';


-- -----------------------------------------------------------------------------
-- Team Match Passing Types Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_match_passing_types (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,
    venue TEXT,
    result TEXT,
    
    -- Pass Types
    passes_attempted INTEGER,
    passes_live INTEGER,
    passes_dead INTEGER,
    passes_free_kicks INTEGER,
    through_balls INTEGER,
    switches INTEGER,
    crosses INTEGER,
    throw_ins INTEGER,
    corner_kicks INTEGER,
    corner_kicks_in INTEGER,
    corner_kicks_out INTEGER,
    corner_kicks_straight INTEGER,
    
    -- Outcomes
    passes_offside INTEGER,
    passes_blocked INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, game)
);

CREATE INDEX idx_fbref_team_match_passing_types_league_season ON fbref_team_match_passing_types(league, season);
CREATE INDEX idx_fbref_team_match_passing_types_team ON fbref_team_match_passing_types(team);
CREATE INDEX idx_fbref_team_match_passing_types_game ON fbref_team_match_passing_types(game);
CREATE TRIGGER update_fbref_team_match_passing_types_updated_at BEFORE UPDATE ON fbref_team_match_passing_types
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_match_passing_types IS 'FBref team match passing types statistics';

-- -----------------------------------------------------------------------------
-- Team Match Goal and Shot Creation Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_match_goal_shot_creation (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,
    venue TEXT,
    result TEXT,
    
    -- Shot Creating Actions
    sca INTEGER,
    sca_passes_live INTEGER,
    sca_passes_dead INTEGER,
    sca_take_ons INTEGER,
    sca_shots INTEGER,
    sca_fouled INTEGER,
    sca_defense INTEGER,
    
    -- Goal Creating Actions
    gca INTEGER,
    gca_passes_live INTEGER,
    gca_passes_dead INTEGER,
    gca_take_ons INTEGER,
    gca_shots INTEGER,
    gca_fouled INTEGER,
    gca_defense INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, game)
);

CREATE INDEX idx_fbref_team_match_gsc_league_season ON fbref_team_match_goal_shot_creation(league, season);
CREATE INDEX idx_fbref_team_match_gsc_team ON fbref_team_match_goal_shot_creation(team);
CREATE INDEX idx_fbref_team_match_gsc_game ON fbref_team_match_goal_shot_creation(game);
CREATE TRIGGER update_fbref_team_match_gsc_updated_at BEFORE UPDATE ON fbref_team_match_goal_shot_creation
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_match_goal_shot_creation IS 'FBref team match goal and shot creation statistics';

-- -----------------------------------------------------------------------------
-- Team Match Defense Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_match_defense (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,
    venue TEXT,
    result TEXT,
    
    -- Tackles
    tackles INTEGER,
    tackles_won INTEGER,
    tackles_def_3rd INTEGER,
    tackles_mid_3rd INTEGER,
    tackles_att_3rd INTEGER,
    
    -- Challenges
    challenge_tackles INTEGER,
    challenges INTEGER,
    challenge_tackles_pct NUMERIC(5,2),
    challenges_lost INTEGER,
    
    -- Blocks
    blocks INTEGER,
    blocked_shots INTEGER,
    blocked_passes INTEGER,
    
    -- Interceptions
    interceptions INTEGER,
    tackles_plus_interceptions INTEGER,
    clearances INTEGER,
    errors INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, game)
);

CREATE INDEX idx_fbref_team_match_defense_league_season ON fbref_team_match_defense(league, season);
CREATE INDEX idx_fbref_team_match_defense_team ON fbref_team_match_defense(team);
CREATE INDEX idx_fbref_team_match_defense_game ON fbref_team_match_defense(game);
CREATE TRIGGER update_fbref_team_match_defense_updated_at BEFORE UPDATE ON fbref_team_match_defense
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_match_defense IS 'FBref team match defensive statistics';

-- -----------------------------------------------------------------------------
-- Team Match Possession Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_match_possession (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,
    venue TEXT,
    result TEXT,
    
    -- Touches
    touches INTEGER,
    touches_def_pen_area INTEGER,
    touches_def_3rd INTEGER,
    touches_mid_3rd INTEGER,
    touches_att_3rd INTEGER,
    touches_att_pen_area INTEGER,
    touches_live_ball INTEGER,
    
    -- Take-Ons
    take_ons_attempted INTEGER,
    take_ons_successful INTEGER,
    take_ons_success_pct NUMERIC(5,2),
    take_ons_tackled INTEGER,
    take_ons_tackled_pct NUMERIC(5,2),
    
    -- Carries
    carries INTEGER,
    carry_distance INTEGER,
    carry_progressive_distance INTEGER,
    progressive_carries INTEGER,
    carries_into_final_third INTEGER,
    carries_into_penalty_area INTEGER,
    
    -- Receiving
    passes_received INTEGER,
    progressive_passes_received INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, game)
);

CREATE INDEX idx_fbref_team_match_possession_league_season ON fbref_team_match_possession(league, season);
CREATE INDEX idx_fbref_team_match_possession_team ON fbref_team_match_possession(team);
CREATE INDEX idx_fbref_team_match_possession_game ON fbref_team_match_possession(game);
CREATE TRIGGER update_fbref_team_match_possession_updated_at BEFORE UPDATE ON fbref_team_match_possession
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_match_possession IS 'FBref team match possession statistics';

-- -----------------------------------------------------------------------------
-- Team Match Miscellaneous Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_team_match_misc (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,
    venue TEXT,
    result TEXT,
    
    -- Performance
    cards_yellow INTEGER,
    cards_red INTEGER,
    fouls INTEGER,
    fouled INTEGER,
    offsides INTEGER,
    crosses INTEGER,
    interceptions INTEGER,
    tackles_won INTEGER,
    penalty_kicks_won INTEGER,
    penalty_kicks_conceded INTEGER,
    own_goals INTEGER,
    ball_recoveries INTEGER,
    
    -- Aerial Duels
    aerials_won INTEGER,
    aerials_lost INTEGER,
    aerials_won_pct NUMERIC(5,2),

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, game)
);

CREATE INDEX idx_fbref_team_match_misc_league_season ON fbref_team_match_misc(league, season);
CREATE INDEX idx_fbref_team_match_misc_team ON fbref_team_match_misc(team);
CREATE INDEX idx_fbref_team_match_misc_game ON fbref_team_match_misc(game);
CREATE TRIGGER update_fbref_team_match_misc_updated_at BEFORE UPDATE ON fbref_team_match_misc
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_team_match_misc IS 'FBref team match miscellaneous statistics';


-- =============================================================================
-- PLAYER SEASON STATISTICS (11 tables - season aggregated per player)
-- =============================================================================

-- Note: Standard player stats follow same pattern as team stats but per player
-- Tables will mirror team stat types with player-specific fields

-- -----------------------------------------------------------------------------
-- Player Season Standard Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_player_season_standard (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    player TEXT NOT NULL,

    -- Player Info
    nation TEXT,
    position TEXT,
    age NUMERIC(4,1),
    birth_year INTEGER,
    
    -- Playing Time
    matches_played INTEGER,
    starts INTEGER,
    minutes INTEGER,
    minutes_per_90 NUMERIC(5,1),
    
    -- Performance
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

    UNIQUE(league, season, team, player)
);

CREATE INDEX idx_fbref_player_season_standard_league_season ON fbref_player_season_standard(league, season);
CREATE INDEX idx_fbref_player_season_standard_player ON fbref_player_season_standard(player);
CREATE INDEX idx_fbref_player_season_standard_team ON fbref_player_season_standard(team);
CREATE TRIGGER update_fbref_player_season_standard_updated_at BEFORE UPDATE ON fbref_player_season_standard
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_player_season_standard IS 'FBref player season standard statistics';

-- Note: For brevity, the remaining 10 player season tables follow the same structure
-- as their team counterparts but with player-specific fields. They are:
-- - fbref_player_season_shooting
-- - fbref_player_season_passing  
-- - fbref_player_season_passing_types
-- - fbref_player_season_goal_shot_creation
-- - fbref_player_season_defense
-- - fbref_player_season_possession
-- - fbref_player_season_playing_time
-- - fbref_player_season_misc
-- - fbref_player_season_keeper
-- - fbref_player_season_keeper_adv

-- Each table will have similar columns to team tables with additions for:
-- - player name, nation, position, age, birth_year
-- - team association
-- - per 90 minute statistics

-- =============================================================================
-- PLAYER MATCH STATISTICS (7 tables - match-level data per player)
-- =============================================================================

-- -----------------------------------------------------------------------------
-- Player Match Summary Stats
-- -----------------------------------------------------------------------------
CREATE TABLE fbref_player_match_summary (
    id SERIAL PRIMARY KEY,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    team TEXT NOT NULL,
    player TEXT NOT NULL,
    game TEXT NOT NULL,

    -- Match Info
    date TIMESTAMP WITH TIME ZONE,
    opponent TEXT,
    venue TEXT,
    result TEXT,
    
    -- Player Info
    position TEXT,
    age TEXT,
    
    -- Playing Time
    minutes INTEGER,
    
    -- Performance
    goals INTEGER,
    assists INTEGER,
    penalty_kicks INTEGER,
    penalty_kicks_attempted INTEGER,
    shots INTEGER,
    shots_on_target INTEGER,
    cards_yellow INTEGER,
    cards_red INTEGER,
    
    -- Touches
    touches INTEGER,
    tackles INTEGER,
    interceptions INTEGER,
    blocks INTEGER,
    
    -- Expected
    xg NUMERIC(5,3),
    npxg NUMERIC(5,3),
    xag NUMERIC(5,3),
    
    -- Shot Creating Actions
    sca INTEGER,
    gca INTEGER,
    
    -- Passes
    passes_completed INTEGER,
    passes_attempted INTEGER,
    pass_completion_pct NUMERIC(5,2),
    progressive_passes INTEGER,
    
    -- Carries
    carries INTEGER,
    progressive_carries INTEGER,
    
    -- Take-Ons
    take_ons_attempted INTEGER,
    take_ons_successful INTEGER,

    -- Metadata
    data_source TEXT NOT NULL DEFAULT 'fbref',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(league, season, team, player, game)
);

CREATE INDEX idx_fbref_player_match_summary_league_season ON fbref_player_match_summary(league, season);
CREATE INDEX idx_fbref_player_match_summary_player ON fbref_player_match_summary(player);
CREATE INDEX idx_fbref_player_match_summary_team ON fbref_player_match_summary(team);
CREATE INDEX idx_fbref_player_match_summary_game ON fbref_player_match_summary(game);
CREATE TRIGGER update_fbref_player_match_summary_updated_at BEFORE UPDATE ON fbref_player_match_summary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMENT ON TABLE fbref_player_match_summary IS 'FBref player match summary statistics';

-- Note: The remaining 6 player match tables follow similar patterns:
-- - fbref_player_match_keepers
-- - fbref_player_match_passing
-- - fbref_player_match_passing_types
-- - fbref_player_match_defense
-- - fbref_player_match_possession
-- - fbref_player_match_misc

-- =============================================================================
-- SUMMARY: FBref Complete Table List (44 tables)
-- =============================================================================
-- Metadata: 2 tables (leagues, seasons)
-- Team Season: 11 tables (standard, keeper, keeper_adv, shooting, passing, passing_types, goal_shot_creation, defense, possession, playing_time, misc)
-- Team Match: 9 tables (schedule + 8 stat types)
-- Player Season: 11 tables (same types as team season)
-- Player Match: 7 tables (summary + 6 stat types)
-- Match Data: 4 tables (schedule, lineups, events, shot_events)
-- Total: 44 tables
-- =============================================================================
