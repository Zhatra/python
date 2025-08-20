#!/usr/bin/env python3
"""Demo script for DataExtractor functionality."""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.data_processing.extractor import DataExtractor
from src.database.connection import DatabaseConnection
from src.config import app_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Demonstrate DataExtractor functionality."""
    logger.info("Starting DataExtractor demo")
    
    try:
        # Initialize database connection
        db_connection = DatabaseConnection()
        
        # Test connection
        if not db_connection.test_connection():
            logger.error("Database connection failed")
            return 1
        
        # Initialize extractor
        extractor = DataExtractor(db_connection)
        
        # Create output directory
        output_dir = Path(app_config.OUTPUT_DATA_PATH)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("DataExtractor initialized successfully")
        
        # Demo 1: Extract raw transactions to CSV
        logger.info("Demo 1: Extracting raw transactions to CSV")
        try:
            csv_output = output_dir / "raw_transactions_demo.csv"
            metadata = extractor.extract_raw_transactions(
                output_path=str(csv_output),
                output_format="csv"
            )
            logger.info(f"CSV extraction completed: {metadata.extracted_rows} rows in {metadata.execution_time_seconds:.2f}s")
            logger.info(f"Output file: {csv_output}")
            
            # Validate the output file
            validation = extractor.validate_output_file(str(csv_output))
            if validation['valid']:
                logger.info(f"CSV file validation: PASSED ({validation['file_size_bytes']} bytes)")
            else:
                logger.warning(f"CSV file validation: FAILED - {validation['error']}")
                
        except Exception as e:
            logger.warning(f"CSV extraction failed (this is expected if no data exists): {e}")
        
        # Demo 2: Extract raw transactions to Parquet
        logger.info("Demo 2: Extracting raw transactions to Parquet")
        try:
            parquet_output = output_dir / "raw_transactions_demo.parquet"
            metadata = extractor.extract_raw_transactions(
                output_path=str(parquet_output),
                output_format="parquet"
            )
            logger.info(f"Parquet extraction completed: {metadata.extracted_rows} rows in {metadata.execution_time_seconds:.2f}s")
            logger.info(f"Output file: {parquet_output}")
            
            # Validate the output file
            validation = extractor.validate_output_file(str(parquet_output))
            if validation['valid']:
                logger.info(f"Parquet file validation: PASSED ({validation['file_size_bytes']} bytes)")
            else:
                logger.warning(f"Parquet file validation: FAILED - {validation['error']}")
                
        except Exception as e:
            logger.warning(f"Parquet extraction failed (this is expected if no data exists): {e}")
        
        # Demo 3: Show extraction statistics
        logger.info("Demo 3: Extraction statistics")
        stats = extractor.get_extraction_statistics()
        logger.info(f"Total extractions: {stats.total_extractions}")
        logger.info(f"Successful extractions: {stats.successful_extractions}")
        logger.info(f"Total rows extracted: {stats.total_rows_extracted}")
        logger.info(f"Average execution time: {stats.average_extraction_time:.2f}s")
        logger.info(f"Formats used: {stats.formats_used}")
        
        # Demo 4: Export metadata
        logger.info("Demo 4: Exporting extraction metadata")
        metadata_output = output_dir / "extraction_metadata.json"
        extractor.export_extraction_metadata(str(metadata_output))
        logger.info(f"Metadata exported to: {metadata_output}")
        
        logger.info("DataExtractor demo completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        return 1
    finally:
        # Clean up
        if 'db_connection' in locals():
            db_connection.close()


if __name__ == "__main__":
    sys.exit(main())