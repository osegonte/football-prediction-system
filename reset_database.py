"""
DATABASE RESET SCRIPT
Clears all tables for a fresh data collection start
"""

from database.connection import get_connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Clear all tables in the database."""
    
    tables = [
        'player_statistics',
        'match_statistics', 
        'team_matches',
        'fixtures',
        'scraping_log',
        'scraping_sessions'
    ]
    
    print("\n" + "="*80)
    print("⚠️  DATABASE RESET")
    print("="*80)
    print("\nThis will DELETE ALL DATA from:")
    for table in tables:
        print(f"   - {table}")
    print("\n" + "="*80)
    
    confirm = input("\nType 'YES' to confirm: ")
    
    if confirm != 'YES':
        print("❌ Cancelled")
        return
    
    try:
        with get_connection() as db:
            for table in tables:
                logger.info(f"Clearing {table}...")
                db.execute(f"TRUNCATE TABLE {table} CASCADE")
                logger.info(f"✅ {table} cleared")
        
        print("\n" + "="*80)
        print("✅ DATABASE RESET COMPLETE")
        print("="*80)
        print("\n🚀 Ready for fresh data collection!\n")
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise

if __name__ == "__main__":
    reset_database()