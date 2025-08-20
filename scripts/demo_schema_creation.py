#!/usr/bin/env python3
"""
Demo script for normalized schema creation and data distribution.

This script demonstrates:
1. Creating the normalized database schema
2. Distributing data from raw tables to normalized tables
3. Validating the schema and data integrity
4. Generating statistics and reports
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.database.connection import db_connection
from src.database.manager import DatabaseManager
from src.config import get_database_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main demonstration function."""
    logger.info("Starting normalized schema creation and data distribution demo")
    
    try:
        # Initialize database connection
        config = get_database_config()
        logger.info(f"Connecting to database: {config['host']}:{config['port']}/{config['database']}")
        
        if not db_connection.test_connection():
            logger.error("Failed to connect to database")
            return False
        
        # Initialize database manager
        manager = DatabaseManager()
        
        # Step 1: Create normalized schema
        logger.info("=" * 60)
        logger.info("STEP 1: Creating normalized database schema")
        logger.info("=" * 60)
        
        if manager.create_normalized_schema():
            logger.info("✓ Normalized schema created successfully")
        else:
            logger.error("✗ Failed to create normalized schema")
            return False
        
        # Step 2: Validate schema structure
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: Validating schema structure")
        logger.info("=" * 60)
        
        validation_result = manager.validate_normalized_schema()
        
        if validation_result['is_valid']:
            logger.info("✓ Schema validation passed")
            logger.info(f"  - Schema exists: {validation_result['schema_exists']}")
            logger.info(f"  - Companies table exists: {validation_result['companies_table_exists']}")
            logger.info(f"  - Charges table exists: {validation_result['charges_table_exists']}")
            logger.info(f"  - Foreign key constraints: {len(validation_result['foreign_key_constraints'])}")
            logger.info(f"  - Indexes: {len(validation_result['indexes'])}")
        else:
            logger.error("✗ Schema validation failed")
            for error in validation_result['validation_errors']:
                logger.error(f"  - {error}")
            return False
        
        # Step 3: Check if we have raw data to distribute
        logger.info("\n" + "=" * 60)
        logger.info("STEP 3: Checking raw data availability")
        logger.info("=" * 60)
        
        raw_count = manager.get_table_row_count('raw_transactions', 'raw_data')
        if raw_count is None or raw_count == 0:
            logger.warning("No raw data found to distribute")
            logger.info("Please load raw data first using the data loader")
            logger.info("You can run: python scripts/demo_data_loader.py")
            return True
        
        logger.info(f"Found {raw_count} raw transaction records to process")
        
        # Step 4: Distribute data to normalized tables
        logger.info("\n" + "=" * 60)
        logger.info("STEP 4: Distributing data to normalized tables")
        logger.info("=" * 60)
        
        distribution_result = manager.distribute_data_to_normalized_tables()
        
        if distribution_result['success']:
            logger.info("✓ Data distribution completed successfully")
            
            report = distribution_result['transformation_report']
            logger.info(f"  - Total raw rows: {report['total_raw_rows']}")
            logger.info(f"  - Transformed rows: {report['transformed_rows']}")
            logger.info(f"  - Skipped rows: {report['skipped_rows']}")
            logger.info(f"  - Companies created: {report['companies_created']}")
            logger.info(f"  - Charges created: {report['charges_created']}")
            logger.info(f"  - Success rate: {report['success_rate']:.2f}%")
            logger.info(f"  - Execution time: {report['execution_time_seconds']:.2f} seconds")
            
            if report['errors_count'] > 0:
                logger.warning(f"  - Transformation errors: {report['errors_count']}")
            
            if report['quality_issues_count'] > 0:
                logger.warning(f"  - Data quality issues: {report['quality_issues_count']}")
            
        else:
            logger.error("✗ Data distribution failed")
            logger.error(f"Error: {distribution_result['error']}")
            return False
        
        # Step 5: Generate distribution statistics
        logger.info("\n" + "=" * 60)
        logger.info("STEP 5: Generating distribution statistics")
        logger.info("=" * 60)
        
        stats = manager.get_data_distribution_statistics()
        
        if 'error' not in stats:
            logger.info("✓ Distribution statistics generated")
            
            # Record counts
            counts = stats['record_counts']
            logger.info(f"  Record Counts:")
            logger.info(f"    - Raw transactions: {counts['raw_transactions']}")
            logger.info(f"    - Companies: {counts['companies']}")
            logger.info(f"    - Charges: {counts['charges']}")
            logger.info(f"    - Transformation rate: {counts['transformation_rate']:.2f}%")
            
            # Company statistics
            if stats['company_statistics']:
                logger.info(f"  Company Statistics:")
                for company in stats['company_statistics']:
                    logger.info(f"    - {company['company_name']}: {company['charge_count']} charges, ${company['total_amount']:.2f}")
            
            # Status distribution
            if stats['status_distribution']:
                logger.info(f"  Status Distribution:")
                for status in stats['status_distribution']:
                    logger.info(f"    - {status['status']}: {status['count']} charges, ${status['total_amount']:.2f}")
            
            # Data integrity
            integrity = stats['data_integrity']
            logger.info(f"  Data Integrity:")
            logger.info(f"    - Integrity score: {integrity['integrity_score']:.1f}/100")
            logger.info(f"    - Orphaned charges: {integrity['orphaned_charges']}")
            logger.info(f"    - Companies without charges: {integrity['companies_without_charges']}")
            
        else:
            logger.error("✗ Failed to generate distribution statistics")
            logger.error(f"Error: {stats['error']}")
        
        # Step 6: Create reporting view
        logger.info("\n" + "=" * 60)
        logger.info("STEP 6: Creating reporting view")
        logger.info("=" * 60)
        
        if manager.create_reporting_view():
            logger.info("✓ Daily transaction summary view created successfully")
        else:
            logger.error("✗ Failed to create reporting view")
        
        # Step 7: Final database information
        logger.info("\n" + "=" * 60)
        logger.info("STEP 7: Final database information")
        logger.info("=" * 60)
        
        db_info = manager.get_database_info()
        logger.info("✓ Database information retrieved")
        logger.info(f"  Schemas: {', '.join(db_info['schemas'])}")
        
        for schema, tables in db_info['tables'].items():
            if tables:
                logger.info(f"  {schema} schema tables:")
                for table, info in tables.items():
                    logger.info(f"    - {table}: {info['row_count']} rows, {info['columns']} columns")
        
        if db_info['views']:
            logger.info(f"  Views: {', '.join(db_info['views'])}")
        
        logger.info("\n" + "=" * 60)
        logger.info("DEMO COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info("The normalized schema has been created and data has been distributed.")
        logger.info("You can now query the normalized_data.companies and normalized_data.charges tables.")
        logger.info("Use the normalized_data.daily_transaction_summary view for reporting.")
        
        return True
        
    except Exception as e:
        logger.error(f"Demo failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    finally:
        # Close database connection
        if db_connection:
            db_connection.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)