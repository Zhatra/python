#!/usr/bin/env python3
"""Demonstration script for DataLoader functionality."""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_processing.loader import DataLoader
from database.connection import DatabaseConnection
from database.manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Demonstrate DataLoader functionality."""
    logger.info("Starting DataLoader demonstration")
    
    # Initialize database connection and manager
    try:
        db_connection = DatabaseConnection()
        db_manager = DatabaseManager(db_connection)
        
        # Test database connection
        if not db_connection.test_connection():
            logger.error("Database connection failed")
            return 1
        
        # Initialize database structure
        logger.info("Initializing database structure...")
        if not db_manager.initialize_database():
            logger.error("Database initialization failed")
            return 1
        
        # Initialize DataLoader
        loader = DataLoader(db_connection)
        
        # Path to the CSV file
        csv_path = Path(__file__).parent.parent / "data" / "input" / "data_prueba_técnica.csv"
        
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            return 1
        
        logger.info(f"Loading CSV data from: {csv_path}")
        
        # Load CSV data with validation
        report = loader.load_csv_to_database(
            str(csv_path),
            batch_size=1000,
            validate_data=True
        )
        
        # Display results
        logger.info("=" * 60)
        logger.info("DATA LOADING RESULTS")
        logger.info("=" * 60)
        logger.info(f"File: {Path(report.file_path).name}")
        logger.info(f"Total rows processed: {report.total_rows_processed}")
        logger.info(f"Rows loaded: {report.rows_loaded}")
        logger.info(f"Rows skipped: {report.rows_skipped}")
        logger.info(f"Loading success rate: {report.loading_success_rate:.2f}%")
        logger.info(f"Execution time: {report.execution_time_seconds:.2f} seconds")
        
        # Validation results
        validation = report.validation_report
        logger.info("\nVALIDATION RESULTS:")
        logger.info(f"Valid rows: {validation.valid_rows}")
        logger.info(f"Invalid rows: {validation.invalid_rows}")
        logger.info(f"Validation success rate: {validation.success_rate:.2f}%")
        logger.info(f"Duplicates found: {validation.duplicates}")
        
        if validation.errors:
            logger.info(f"Validation errors: {len(validation.errors)}")
            # Show first few errors as examples
            for i, error in enumerate(validation.errors[:5]):
                logger.info(f"  Error {i+1}: {error['type']} - {error['message']}")
            if len(validation.errors) > 5:
                logger.info(f"  ... and {len(validation.errors) - 5} more errors")
        
        if validation.warnings:
            logger.info(f"Validation warnings: {len(validation.warnings)}")
            for warning in validation.warnings:
                logger.info(f"  Warning: {warning['message']}")
        
        if report.loading_errors:
            logger.info(f"Loading errors: {len(report.loading_errors)}")
            for i, error in enumerate(report.loading_errors[:3]):
                logger.info(f"  Loading error {i+1}: {error['type']} - {error['message']}")
        
        # Get loading statistics
        logger.info("\nLOADING STATISTICS:")
        stats = loader.get_loading_statistics()
        if 'error' not in stats:
            logger.info(f"Total rows in database: {stats['total_rows']}")
            logger.info(f"Unique companies: {stats['unique_companies']}")
            logger.info(f"Rows with amount: {stats['rows_with_amount']}")
            
            if stats['status_distribution']:
                logger.info("Status distribution:")
                for status, count in stats['status_distribution'].items():
                    logger.info(f"  {status}: {count}")
        else:
            logger.error(f"Failed to get statistics: {stats['error']}")
        
        logger.info("=" * 60)
        logger.info("DataLoader demonstration completed successfully!")
        
        return 0
        
    except Exception as e:
        logger.error(f"Demonstration failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())