-- =============================================================================
-- Additional Indexes and Cross-Table Constraints
-- =============================================================================
-- Description: Additional performance indexes and optional foreign key constraints
-- Note: Foreign keys are optional and can be enabled for data integrity
-- =============================================================================

\c football_stats

-- =============================================================================
-- CROSS-TABLE INDEXES FOR JOIN PERFORMANCE
-- =============================================================================

-- Note: Most primary indexes are already created in individual table files
-- These are additional composite indexes for common query patterns

-- Example: Querying player stats across multiple sources
-- CREATE INDEX idx_cross_player_league_season ON fbref_player_season_standard(player, league, season);
-- CREATE INDEX idx_cross_player_league_season_understat ON understat_player_season_stats(player, league, season);

-- Example: Joining match data from different sources by date and teams
-- CREATE INDEX idx_cross_match_date_teams_fbref ON fbref_schedule(date, home_team, away_team);
-- CREATE INDEX idx_cross_match_date_teams_understat ON understat_schedule(date, home_team, away_team);

-- =============================================================================
-- OPTIONAL FOREIGN KEY CONSTRAINTS
-- =============================================================================

-- Note: Foreign keys are commented out by default for performance during bulk loading
-- Uncomment these after initial data load if strict referential integrity is needed

-- Example: Link FBref lineups to schedule
-- ALTER TABLE fbref_lineups
--     ADD CONSTRAINT fk_fbref_lineups_schedule
--     FOREIGN KEY (league, season, game)
--     REFERENCES fbref_schedule(league, season, game)
--     ON DELETE CASCADE;

-- Example: Link FBref events to schedule
-- ALTER TABLE fbref_events
--     ADD CONSTRAINT fk_fbref_events_schedule
--     FOREIGN KEY (league, season, game)
--     REFERENCES fbref_schedule(league, season, game)
--     ON DELETE CASCADE;

-- Example: Link FBref shot events to schedule
-- ALTER TABLE fbref_shot_events
--     ADD CONSTRAINT fk_fbref_shot_events_schedule
--     FOREIGN KEY (league, season, game)
--     REFERENCES fbref_schedule(league, season, game)
--     ON DELETE CASCADE;

-- =============================================================================
-- MATERIALIZED VIEWS FOR PERFORMANCE (Optional)
-- =============================================================================

-- Note: Materialized views can improve query performance for common aggregations
-- These are examples and should be created based on actual query patterns

-- Example: Combined schedule from all sources
-- CREATE MATERIALIZED VIEW mv_all_schedules AS
-- SELECT 'fbref' as source, league, season, game, date, home_team, away_team, home_xg, away_xg
-- FROM fbref_schedule
-- UNION ALL
-- SELECT 'understat' as source, league, season, game, date, home_team, away_team, home_xg, away_xg
-- FROM understat_schedule
-- UNION ALL
-- SELECT 'fotmob' as source, league, season, game, date, home_team, away_team, NULL::numeric, NULL::numeric
-- FROM fotmob_schedule;

-- CREATE INDEX idx_mv_all_schedules_date ON mv_all_schedules(date);
-- CREATE INDEX idx_mv_all_schedules_teams ON mv_all_schedules(home_team, away_team);

-- Refresh materialized view
-- REFRESH MATERIALIZED VIEW mv_all_schedules;

-- =============================================================================
-- PARTITIONING (Optional - for very large datasets)
-- =============================================================================

-- Note: For tables with millions of rows, consider partitioning by season or date
-- This is an advanced optimization and should only be done if query performance requires it

-- Example: Partition fbref_shot_events by season
-- -- First, create the parent table with partitioning
-- -- CREATE TABLE fbref_shot_events_partitioned (
-- --     LIKE fbref_shot_events INCLUDING ALL
-- -- ) PARTITION BY LIST (season);
--
-- -- Then create partitions for each season
-- -- CREATE TABLE fbref_shot_events_2021 PARTITION OF fbref_shot_events_partitioned
-- --     FOR VALUES IN ('2021');
-- -- CREATE TABLE fbref_shot_events_2122 PARTITION OF fbref_shot_events_partitioned
-- --     FOR VALUES IN ('2122');

-- =============================================================================
-- FULL-TEXT SEARCH INDEXES (Optional)
-- =============================================================================

-- Note: If searching for players or teams by name, full-text search can improve performance

-- Example: Full-text search on player names
-- ALTER TABLE fbref_player_season_standard
--     ADD COLUMN player_search tsvector
--     GENERATED ALWAYS AS (to_tsvector('english', player)) STORED;
--
-- CREATE INDEX idx_fbref_player_search ON fbref_player_season_standard USING GIN (player_search);

-- Example: Full-text search on team names
-- ALTER TABLE fbref_schedule
--     ADD COLUMN teams_search tsvector
--     GENERATED ALWAYS AS (
--         to_tsvector('english', home_team) || to_tsvector('english', away_team)
--     ) STORED;
--
-- CREATE INDEX idx_fbref_schedule_teams_search ON fbref_schedule USING GIN (teams_search);

-- =============================================================================
-- ANALYTICS HELPER VIEWS (Optional)
-- =============================================================================

-- Note: Create views for common analytics queries

-- Example: Top scorers across all seasons
-- CREATE VIEW v_top_scorers AS
-- SELECT
--     player,
--     team,
--     league,
--     season,
--     goals,
--     assists,
--     goals + assists as goal_contributions,
--     xg,
--     goals - xg as goals_vs_xg
-- FROM fbref_player_season_standard
-- WHERE minutes >= 900  -- At least 10 full matches
-- ORDER BY goals DESC, assists DESC;

-- Example: Team performance summary
-- CREATE VIEW v_team_performance AS
-- SELECT
--     league,
--     season,
--     team,
--     COUNT(*) as matches,
--     SUM(CASE WHEN home_goals > away_goals THEN 1 ELSE 0 END) as wins,
--     SUM(CASE WHEN home_goals = away_goals THEN 1 ELSE 0 END) as draws,
--     SUM(CASE WHEN home_goals < away_goals THEN 1 ELSE 0 END) as losses,
--     SUM(home_goals) as goals_for,
--     SUM(away_goals) as goals_against,
--     SUM(home_goals) - SUM(away_goals) as goal_difference,
--     SUM(home_xg) as xg_for,
--     SUM(away_xg) as xg_against
-- FROM fbref_schedule
-- WHERE home_goals IS NOT NULL  -- Only completed matches
-- GROUP BY league, season, team
-- ORDER BY league, season, wins DESC, goal_difference DESC;

-- =============================================================================
-- DATABASE MAINTENANCE
-- =============================================================================

-- Vacuum and analyze after bulk loading
-- VACUUM ANALYZE;

-- Update statistics for query planner
-- ANALYZE;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON SCHEMA public IS 'Football statistics database with data from 9 sources covering top European leagues';
