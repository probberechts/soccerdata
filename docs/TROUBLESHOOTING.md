# Troubleshooting Guide

Common issues and solutions for the football statistics database.

## Database Issues

### Cannot Connect to Database

**Error:**
```
ConnectionError: Failed to connect to database
```

**Solutions:**

1. **Check PostgreSQL is running:**
   ```bash
   sudo systemctl status postgresql  # Linux
   brew services list  # macOS
   ```

2. **Verify credentials in `.env`:**
   ```bash
   cat .env
   # Ensure DB_HOST, DB_PORT, DB_USER, DB_PASSWORD are correct
   ```

3. **Test connection manually:**
   ```bash
   psql -h localhost -U postgres -d football_stats
   ```

4. **Check PostgreSQL logs:**
   ```bash
   sudo tail -f /var/log/postgresql/postgresql-*.log
   ```

### Tables Not Found

**Error:**
```
relation "fbref_schedule" does not exist
```

**Solutions:**

1. **Run schema files:**
   ```bash
   cat schema/*.sql | psql -U postgres football_stats
   ```

2. **Verify tables exist:**
   ```bash
   psql -U postgres football_stats -c "\dt"
   ```

### Permission Denied

**Error:**
```
permission denied for table fbref_schedule
```

**Solution:**

```sql
-- Grant permissions to your user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_username;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_username;
```

## Extraction Issues

### Rate Limiting / Blocked Requests

**Error:**
```
HTTPError: 429 Too Many Requests
```

**Solutions:**

1. **Increase delays in `config/data_sources.yaml`:**
   ```yaml
   rate_limiting:
     requests_per_minute: 10  # Reduce from 20
     delay_between_requests: 5  # Increase from 3
   ```

2. **Use a proxy (advanced):**
   See soccerdata documentation for proxy configuration.

### API Timeouts

**Error:**
```
ReadTimeout: HTTPSConnectionPool(host='fbref.com', port=443)
```

**Solutions:**

1. **Check internet connection**

2. **Increase retry attempts in `config/data_sources.yaml`:**
   ```yaml
   retry:
     max_attempts: 5  # Increase from 3
     max_delay: 120  # Increase from 60
   ```

3. **Try again later** - Source may be temporarily unavailable

### No Data Found

**Warning:**
```
No data available for ENG-Premier League 2324
```

**Causes:**

1. **Season not yet available** - Future seasons have no data yet
2. **League name mismatch** - Verify league name in `config/leagues.yaml`
3. **Data source doesn't cover that league/season**

**Solution:**

Check data availability for specific source/league combination.

### ImportError

**Error:**
```
ModuleNotFoundError: No module named 'psycopg2'
```

**Solution:**

```bash
pip install -r requirements-database.txt
```

## Data Quality Issues

### Duplicate Records

**Symptom:** Same match appears multiple times

**Diagnosis:**
```sql
SELECT
    league,
    season,
    game,
    COUNT(*) as count
FROM fbref_schedule
GROUP BY league, season, game
HAVING COUNT(*) > 1;
```

**Solution:**

UNIQUE constraints should prevent this. If duplicates exist:

```sql
-- Keep only the most recent version
DELETE FROM fbref_schedule a USING fbref_schedule b
WHERE a.id < b.id
    AND a.league = b.league
    AND a.season = b.season
    AND a.game = b.game;
```

### Missing Data

**Symptom:** Expected records not in database

**Diagnosis:**

1. **Check extraction status:**
   ```sql
   SELECT * FROM data_load_status
   WHERE table_name = 'fbref_schedule'
       AND league = 'ENG-Premier League'
       AND season = '2324';
   ```

2. **Check for errors:**
   ```sql
   SELECT
       data_source,
       table_name,
       league,
       season,
       error_message
   FROM data_load_status
   WHERE status = 'failed';
   ```

**Solution:**

1. Reset failed status and retry:
   ```sql
   UPDATE data_load_status
   SET status = 'pending', error_message = NULL
   WHERE status = 'failed';
   ```

2. Re-run extraction with `--no-skip-completed`

### Inconsistent Statistics

**Symptom:** Values don't match between sources

**Explanation:** This is expected. Different sources use different methodologies:
- FBref uses Opta data
- Understat has proprietary xG models
- FotMob may round or aggregate differently

## Performance Issues

### Slow Extraction

**Symptom:** Extraction takes very long

**Solutions:**

1. **Extract fewer sources:**
   ```bash
   python -m scripts.orchestrator --sources fbref --seasons 2324
   ```

2. **Extract one league at a time:**
   ```bash
   python -m scripts.orchestrator \
       --leagues "ENG-Premier League" \
       --seasons 2324
   ```

3. **Check network speed**

4. **Monitor rate limiting** - May be waiting between requests

### Database Performance

**Symptom:** Queries are slow

**Solutions:**

1. **Create indexes (already in schema/99_indexes_constraints.sql):**
   ```bash
   psql -U postgres football_stats < schema/99_indexes_constraints.sql
   ```

2. **Vacuum database:**
   ```sql
   VACUUM ANALYZE;
   ```

3. **Check table sizes:**
   ```sql
   SELECT
       schemaname,
       tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
   FROM pg_tables
   WHERE schemaname = 'public'
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
   ```

## Configuration Issues

### Config File Not Found

**Error:**
```
FileNotFoundError: config/data_sources.yaml
```

**Solution:**

Ensure you're running scripts from the repository root:

```bash
cd /path/to/soccerdata
python -m scripts.orchestrator --seasons 2324
```

### Invalid YAML

**Error:**
```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Solution:**

1. **Check YAML syntax** - Use spaces, not tabs
2. **Validate YAML:**
   ```bash
   python -c "import yaml; yaml.safe_load(open('config/data_sources.yaml'))"
   ```

## Log Analysis

### Find Errors in Logs

```bash
# Search for ERROR level messages
grep ERROR logs/orchestrator_*.log

# Search for specific error
grep -i "connection" logs/*.log

# Count errors by type
grep ERROR logs/*.log | cut -d: -f4 | sort | uniq -c
```

### Monitor Active Extraction

```bash
# Follow orchestrator log in real-time
tail -f logs/orchestrator_$(date +%Y%m%d).log

# Watch extraction progress
watch -n 5 'psql -U postgres football_stats -c "SELECT data_source, COUNT(*) FILTER (WHERE status = '\''completed'\'') as completed FROM data_load_status GROUP BY data_source;"'
```

## Getting Help

If you encounter an issue not covered here:

1. **Check logs** for detailed error messages
2. **Query `data_load_status`** for extraction status
3. **Verify configuration** files are correct
4. **Test with minimal settings** (one source/league/season)
5. **Check soccerdata library issues** on GitHub

## Common SQL Queries for Debugging

### Check Extraction Status

```sql
-- Overall status
SELECT
    status,
    COUNT(*) as count,
    SUM(rows_processed) as total_rows
FROM data_load_status
GROUP BY status;

-- By data source
SELECT
    data_source,
    status,
    COUNT(*) as count
FROM data_load_status
GROUP BY data_source, status
ORDER BY data_source, status;

-- Recent failures
SELECT
    data_source,
    table_name,
    league,
    season,
    error_message,
    last_updated
FROM data_load_status
WHERE status = 'failed'
ORDER BY last_updated DESC
LIMIT 10;
```

### Verify Data

```sql
-- Count records by source
SELECT 'fbref_schedule' as table_name, COUNT(*) as records FROM fbref_schedule
UNION ALL
SELECT 'fotmob_schedule', COUNT(*) FROM fotmob_schedule
UNION ALL
SELECT 'understat_schedule', COUNT(*) FROM understat_schedule
ORDER BY table_name;

-- Check for data in specific season
SELECT COUNT(*) FROM fbref_schedule
WHERE league = 'ENG-Premier League' AND season = '2324';
```
