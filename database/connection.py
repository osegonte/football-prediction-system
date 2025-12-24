"""
Database connection handler for PostgreSQL.
"""
import psycopg2
from psycopg2.extras import execute_values
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Handles PostgreSQL database connections."""
    
    def __init__(self, dbname='football_data', user='osegonte', host='localhost', port=5432):
        self.dbname = dbname
        self.user = user
        self.host = host
        self.port = port
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(
                dbname=self.dbname,
                user=self.user,
                host=self.host,
                port=self.port
            )
            self.cursor = self.conn.cursor()
            logger.info("Database connection established")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")
    
    def commit(self):
        """Commit current transaction."""
        if self.conn:
            self.conn.commit()
    
    def rollback(self):
        """Rollback current transaction."""
        if self.conn:
            self.conn.rollback()
    
    def execute(self, query: str, params: tuple = None):
        """Execute a single query."""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return True
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            self.rollback()
            return False
    
    def fetchone(self):
        """Fetch one result."""
        return self.cursor.fetchone()
    
    def fetchall(self):
        """Fetch all results."""
        return self.cursor.fetchall()
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.disconnect()


def get_connection():
    """Get a database connection."""
    return DatabaseConnection()


def test_connection():
    """Test database connection."""
    with get_connection() as db:
        db.execute("SELECT COUNT(*) FROM fixtures")
        count = db.fetchone()[0]
        print(f"✅ Database connection successful!")
        print(f"   Current fixtures in database: {count}")
        return True


if __name__ == "__main__":
    test_connection()
