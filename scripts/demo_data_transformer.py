#!/usr/bin/env python3
"""Demo script for DataTransformer functionality."""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_processing.transformer import DataTransformer
from src.database.connection import db_connection
from src.config import app_config
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Demonstrate DataTransformer functionality."""
    logger.info("Starting DataTransformer demo")
    
    try:
        # Test database connection
        logger.info("Testing database connection...")
        if not db_connection.test_connection():
            logger.error("Database connection failed")
            return
        
        # Create transformer
        transformer = DataTransformer()
        
        # Check if we have raw data to transform
        with db_connection.get_session() as session:
            from src.database.models import RawTransaction
            raw_count = session.query(RawTransaction).count()
            
            if raw_count == 0:
                logger.warning("No raw transaction data found. Please load data first using demo_data_loader.py")
                return
            
            logger.info(f"Found {raw_count} raw transaction records to transform")
        
        # Perform transformation
        logger.info("Starting data transformation...")
        report = transformer.transform_to_schema(
            validate_data=True,
            apply_business_rules=True
        )
        
        # Display results
        logger.info("Transformation completed!")
        logger.info(f"Transformation Report:")
        logger.info(f"  Total raw rows: {report.total_raw_rows}")
        logger.info(f"  Transformed rows: {report.transformed_rows}")
        logger.info(f"  Skipped rows: {report.skipped_rows}")
        logger.info(f"  Companies created: {report.companies_created}")
        logger.info(f"  Charges created: {report.charges_created}")
        logger.info(f"  Success rate: {report.transformation_success_rate:.2f}%")
        logger.info(f"  Execution time: {report.execution_time_seconds:.2f} seconds")
        
        if report.data_quality_issues:
            logger.info(f"  Data quality issues: {len(report.data_quality_issues)}")
            for issue in report.data_quality_issues[:5]:  # Show first 5 issues
                logger.info(f"    - {issue.get('type', 'unknown')}: {issue.get('message', 'no message')}")
        
        # Get transformation statistics
        logger.info("Getting transformation statistics...")
        stats = transformer.get_transformation_statistics()
        
        if 'error' not in stats:
            logger.info("Transformation Statistics:")
            logger.info(f"  Companies: {stats['companies_count']}")
            logger.info(f"  Charges: {stats['charges_count']}")
            logger.info(f"  Status distribution: {stats['status_distribution']}")
            logger.info(f"  Date range: {stats['date_range']['earliest']} to {stats['date_range']['latest']}")
        
        # Validate transformation integrity
        logger.info("Validating transformation integrity...")
        integrity = transformer.validate_transformation_integrity()
        
        if 'error' not in integrity:
            logger.info("Integrity Validation:")
            logger.info(f"  Integrity score: {integrity['integrity_score']:.1f}/100")
            logger.info(f"  Transformation rate: {integrity['transformation_rate']:.2f}%")
            logger.info(f"  Is valid: {integrity['is_valid']}")
            
            if integrity['issues']:
                logger.warning("Integrity issues found:")
                for issue in integrity['issues']:
                    logger.warning(f"    - {issue}")
        
        logger.info("DataTransformer demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise
    finally:
        # Close database connection
        db_connection.close()


if __name__ == "__main__":
    main()