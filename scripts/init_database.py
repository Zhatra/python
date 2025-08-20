#!/usr/bin/env python3
"""Database initialization script."""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.manager import DatabaseManager
from src.database.connection import db_connection
from src.config import db_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Initialize the database structure."""
    logger.info("Starting database initialization...")
    logger.info(f"Database: {db_config.HOST}:{db_config.PORT}/{db_config.NAME}")
    
    try:
        # Create database manager
        db_manager = DatabaseManager()
        
        # Initialize database
        if db_manager.initialize_database():
            logger.info("✅ Database initialization completed successfully!")
            
            # Show database info
            info = db_manager.get_database_info()
            logger.info(f"Created schemas: {info['schemas']}")
            logger.info(f"Created tables: {sum(len(tables) for tables in info['tables'].values())}")
            logger.info(f"Created views: {len(info['views'])}")
            
            return 0
        else:
            logger.error("❌ Database initialization failed!")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Database initialization error: {e}")
        return 1
    
    finally:
        # Close database connections
        db_connection.close()


if __name__ == "__main__":
    sys.exit(main())