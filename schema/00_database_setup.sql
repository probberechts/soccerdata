-- =============================================================================
-- Football Statistics Database Setup
-- =============================================================================
-- Description: Creates the database and required extensions for football stats
-- Created: 2025-11-27
-- =============================================================================

-- Drop existing database if it exists (CAUTION: Use with care!)
-- DROP DATABASE IF EXISTS football_stats;

-- Create the database
CREATE DATABASE football_stats
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Connect to the database
\c football_stats

-- =============================================================================
-- Extensions
-- =============================================================================

-- UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- JSONB operations
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Trigram similarity for fuzzy matching of player/team names
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
-- Schemas (Optional: Use schemas to organize tables by source)
-- =============================================================================
-- For now, we'll use the public schema, but this allows future organization

-- CREATE SCHEMA IF NOT EXISTS fbref;
-- CREATE SCHEMA IF NOT EXISTS fotmob;
-- CREATE SCHEMA IF NOT EXISTS understat;
-- CREATE SCHEMA IF NOT EXISTS whoscored;
-- CREATE SCHEMA IF NOT EXISTS sofascore;
-- CREATE SCHEMA IF NOT EXISTS espn;
-- CREATE SCHEMA IF NOT EXISTS clubelo;
-- CREATE SCHEMA IF NOT EXISTS matchhistory;
-- CREATE SCHEMA IF NOT EXISTS sofifa;

-- =============================================================================
-- Data Load Status Tracking Table
-- =============================================================================
-- Track the status of data loading operations for resume capability

CREATE TABLE IF NOT EXISTS data_load_status (
    id SERIAL PRIMARY KEY,
    data_source TEXT NOT NULL,
    table_name TEXT NOT NULL,
    league TEXT NOT NULL,
    season TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    rows_processed INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(data_source, table_name, league, season)
);

CREATE INDEX idx_data_load_status_source ON data_load_status(data_source);
CREATE INDEX idx_data_load_status_status ON data_load_status(status);
CREATE INDEX idx_data_load_status_league_season ON data_load_status(league, season);

-- =============================================================================
-- Common Trigger Function for updated_at
-- =============================================================================
-- Automatically updates the updated_at timestamp on row modifications

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Comments
-- =============================================================================

COMMENT ON DATABASE football_stats IS 'Comprehensive football statistics database covering top European leagues from 2020-2021 onwards';
COMMENT ON TABLE data_load_status IS 'Tracks data loading operations for monitoring and resume capability';
COMMENT ON FUNCTION update_updated_at_column() IS 'Trigger function to automatically update updated_at timestamp';
