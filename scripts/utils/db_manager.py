"""
Database Manager Module
Handles PostgreSQL connections and UPSERT operations
"""

import psycopg2
import psycopg2.extras
from psycopg2 import sql
from typing import List, Dict, Any, Optional
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations"""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str
    ):
        self.connection_params = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password
        }
        self._connection = None

    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    logger.info("Database connection successful")
                    return result[0] == 1
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """Execute a SELECT query and return results"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.fetchall()

    def execute_script(self, script_path: str) -> bool:
        """Execute a SQL script file"""
        try:
            with open(script_path, 'r') as f:
                script = f.read()

            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(script)

            logger.info(f"Successfully executed script: {script_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute script {script_path}: {e}")
            return False

    def bulk_insert(
        self,
        table_name: str,
        columns: List[str],
        data: List[Dict[str, Any]],
        conflict_columns: Optional[List[str]] = None,
        update_columns: Optional[List[str]] = None
    ) -> int:
        """
        Bulk insert with UPSERT capability

        Args:
            table_name: Target table name
            columns: List of column names
            data: List of dictionaries with data
            conflict_columns: Columns for ON CONFLICT clause
            update_columns: Columns to update on conflict

        Returns:
            Number of rows inserted/updated
        """
        if not data:
            logger.warning(f"No data to insert into {table_name}")
            return 0

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Build INSERT statement
                    cols = sql.SQL(', ').join(map(sql.Identifier, columns))
                    placeholders = sql.SQL(', ').join(sql.Placeholder() * len(columns))

                    query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                        sql.Identifier(table_name),
                        cols,
                        placeholders
                    )

                    # Add ON CONFLICT clause if specified
                    if conflict_columns and update_columns:
                        conflict_cols = sql.SQL(', ').join(
                            map(sql.Identifier, conflict_columns)
                        )
                        update_sets = sql.SQL(', ').join([
                            sql.SQL("{} = EXCLUDED.{}").format(
                                sql.Identifier(col),
                                sql.Identifier(col)
                            )
                            for col in update_columns
                        ])

                        query = sql.SQL("{} ON CONFLICT ({}) DO UPDATE SET {}, updated_at = NOW()").format(
                            query,
                            conflict_cols,
                            update_sets
                        )
                    elif conflict_columns:
                        # Just ignore conflicts
                        conflict_cols = sql.SQL(', ').join(
                            map(sql.Identifier, conflict_columns)
                        )
                        query = sql.SQL("{} ON CONFLICT ({}) DO NOTHING").format(
                            query,
                            conflict_cols
                        )

                    # Prepare data tuples
                    data_tuples = [
                        tuple(row.get(col) for col in columns)
                        for row in data
                    ]

                    # Execute bulk insert
                    psycopg2.extras.execute_batch(
                        cur,
                        query.as_string(conn),
                        data_tuples,
                        page_size=1000
                    )

                    rows_affected = cur.rowcount
                    logger.info(f"Inserted/updated {rows_affected} rows in {table_name}")
                    return rows_affected

        except Exception as e:
            logger.error(f"Bulk insert failed for {table_name}: {e}")
            raise

    def update_load_status(
        self,
        data_source: str,
        table_name: str,
        league: str,
        season: str,
        status: str,
        rows_processed: int = 0,
        error_message: Optional[str] = None
    ):
        """Update the data_load_status tracking table"""
        query = """
        INSERT INTO data_load_status
            (data_source, table_name, league, season, status, rows_processed,
             error_message, started_at, last_updated)
        VALUES (%s, %s, %s, %s, %s, %s, %s,
                CASE WHEN %s = 'in_progress' THEN NOW() ELSE NULL END,
                NOW())
        ON CONFLICT (data_source, table_name, league, season)
        DO UPDATE SET
            status = EXCLUDED.status,
            rows_processed = EXCLUDED.rows_processed,
            error_message = EXCLUDED.error_message,
            completed_at = CASE WHEN EXCLUDED.status = 'completed' THEN NOW() ELSE NULL END,
            last_updated = NOW()
        """

        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, (
                        data_source, table_name, league, season, status,
                        rows_processed, error_message, status
                    ))
        except Exception as e:
            logger.error(f"Failed to update load status: {e}")

    def get_load_status(
        self,
        data_source: Optional[str] = None,
        table_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get load status for tracking progress"""
        query = "SELECT * FROM data_load_status WHERE 1=1"
        params = []

        if data_source:
            query += " AND data_source = %s"
            params.append(data_source)

        if table_name:
            query += " AND table_name = %s"
            params.append(table_name)

        query += " ORDER BY last_updated DESC"

        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute(query, params)
                    return [dict(row) for row in cur.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get load status: {e}")
            return []
