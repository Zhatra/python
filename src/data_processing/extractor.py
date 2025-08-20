"""Data extractor module for database-to-file extraction."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
import time

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database.connection import DatabaseConnection
from src.database.models import RawTransaction, Company, Charge
from src.config import app_config

logger = logging.getLogger(__name__)


@dataclass
class ExtractionMetadata:
    """Metadata for extraction operations."""
    
    extraction_id: str
    source_table: str
    source_schema: str
    output_format: str
    output_path: str
    total_rows: int
    extracted_rows: int
    execution_time_seconds: float
    extraction_timestamp: datetime
    file_size_bytes: Optional[int] = None
    compression_used: Optional[str] = None
    query_filters: Optional[Dict[str, Any]] = None
    
    @property
    def extraction_success_rate(self) -> float:
        """Calculate extraction success rate as percentage."""
        if self.total_rows == 0:
            return 100.0
        return (self.extracted_rows / self.total_rows) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            'extraction_id': self.extraction_id,
            'source_table': self.source_table,
            'source_schema': self.source_schema,
            'output_format': self.output_format,
            'output_path': self.output_path,
            'total_rows': self.total_rows,
            'extracted_rows': self.extracted_rows,
            'execution_time_seconds': self.execution_time_seconds,
            'extraction_timestamp': self.extraction_timestamp.isoformat(),
            'file_size_bytes': self.file_size_bytes,
            'compression_used': self.compression_used,
            'query_filters': self.query_filters,
            'extraction_success_rate': self.extraction_success_rate
        }


@dataclass
class ExtractionStatistics:
    """Statistics for extraction operations."""
    
    total_extractions: int
    successful_extractions: int
    failed_extractions: int
    total_rows_extracted: int
    total_execution_time_seconds: float
    formats_used: Dict[str, int]
    average_extraction_time: float
    largest_extraction_rows: int
    
    def __str__(self) -> str:
        return (
            f"ExtractionStatistics(total={self.total_extractions}, "
            f"successful={self.successful_extractions}, "
            f"avg_time={self.average_extraction_time:.2f}s)"
        )


class DataExtractor:
    """Handles database-to-file extraction operations."""
    
    # Supported output formats
    SUPPORTED_FORMATS = {'csv', 'parquet'}
    
    # Default chunk size for large datasets
    DEFAULT_CHUNK_SIZE = 10000
    
    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """Initialize DataExtractor with database connection.
        
        Args:
            db_connection: Database connection instance. If None, uses global instance.
        """
        from src.database.connection import db_connection as global_db_connection
        self.db_connection = db_connection or global_db_connection
        self._extraction_history: List[ExtractionMetadata] = []
    
    def extract_to_csv(
        self, 
        output_path: str,
        table_name: str = "raw_transactions",
        schema: str = "raw_data",
        query_filters: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = None,
        include_header: bool = True,
        date_format: str = "%Y-%m-%d %H:%M:%S"
    ) -> ExtractionMetadata:
        """Extract data from database to CSV format.
        
        Args:
            output_path: Path where CSV file will be saved
            table_name: Name of the table to extract from
            schema: Database schema name
            query_filters: Optional filters to apply to the query
            chunk_size: Number of rows to process at once for large datasets
            include_header: Whether to include column headers in CSV
            date_format: Format for datetime columns
            
        Returns:
            ExtractionMetadata with extraction details
            
        Raises:
            ValueError: If parameters are invalid
            SQLAlchemyError: If database operation fails
        """
        logger.info(f"Starting CSV extraction from {schema}.{table_name} to {output_path}")
        
        return self._extract_data(
            output_path=output_path,
            output_format="csv",
            table_name=table_name,
            schema=schema,
            query_filters=query_filters,
            chunk_size=chunk_size,
            format_options={
                'include_header': include_header,
                'date_format': date_format,
                'index': False
            }
        )
    
    def extract_to_parquet(
        self,
        output_path: str,
        table_name: str = "raw_transactions",
        schema: str = "raw_data",
        query_filters: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = None,
        compression: str = "snappy"
    ) -> ExtractionMetadata:
        """Extract data from database to Parquet format.
        
        Args:
            output_path: Path where Parquet file will be saved
            table_name: Name of the table to extract from
            schema: Database schema name
            query_filters: Optional filters to apply to the query
            chunk_size: Number of rows to process at once for large datasets
            compression: Compression algorithm ('snappy', 'gzip', 'brotli', None)
            
        Returns:
            ExtractionMetadata with extraction details
            
        Raises:
            ValueError: If parameters are invalid
            SQLAlchemyError: If database operation fails
        """
        logger.info(f"Starting Parquet extraction from {schema}.{table_name} to {output_path}")
        
        return self._extract_data(
            output_path=output_path,
            output_format="parquet",
            table_name=table_name,
            schema=schema,
            query_filters=query_filters,
            chunk_size=chunk_size,
            format_options={
                'compression': compression,
                'index': False
            }
        )    

    def _extract_data(
        self,
        output_path: str,
        output_format: str,
        table_name: str,
        schema: str,
        query_filters: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = None,
        format_options: Optional[Dict[str, Any]] = None
    ) -> ExtractionMetadata:
        """Internal method to extract data with specified parameters.
        
        Args:
            output_path: Path where file will be saved
            output_format: Output format ('csv' or 'parquet')
            table_name: Name of the table to extract from
            schema: Database schema name
            query_filters: Optional filters to apply to the query
            chunk_size: Number of rows to process at once
            format_options: Format-specific options
            
        Returns:
            ExtractionMetadata with extraction details
        """
        start_time = time.time()
        extraction_id = f"ext_{int(start_time)}_{output_format}"
        
        # Validate parameters
        self._validate_extraction_parameters(
            output_path, output_format, table_name, schema
        )
        
        # Set default chunk size
        chunk_size = chunk_size or self.DEFAULT_CHUNK_SIZE
        format_options = format_options or {}
        
        try:
            # Create output directory if it doesn't exist
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Get total row count
            total_rows = self._get_table_row_count(table_name, schema, query_filters)
            logger.info(f"Total rows to extract: {total_rows}")
            
            # Extract data
            if total_rows <= chunk_size:
                # Small dataset - extract in single operation
                extracted_rows = self._extract_single_chunk(
                    output_path, output_format, table_name, schema,
                    query_filters, format_options
                )
            else:
                # Large dataset - extract in chunks
                extracted_rows = self._extract_in_chunks(
                    output_path, output_format, table_name, schema,
                    query_filters, chunk_size, format_options, total_rows
                )
            
            execution_time = time.time() - start_time
            
            # Get file size
            file_size = output_file.stat().st_size if output_file.exists() else None
            
            # Create metadata
            metadata = ExtractionMetadata(
                extraction_id=extraction_id,
                source_table=table_name,
                source_schema=schema,
                output_format=output_format,
                output_path=output_path,
                total_rows=total_rows,
                extracted_rows=extracted_rows,
                execution_time_seconds=execution_time,
                extraction_timestamp=datetime.now(),
                file_size_bytes=file_size,
                compression_used=format_options.get('compression'),
                query_filters=query_filters
            )
            
            # Store in history
            self._extraction_history.append(metadata)
            
            logger.info(f"Extraction completed: {extracted_rows}/{total_rows} rows in {execution_time:.2f}s")
            return metadata
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise
    
    def _validate_extraction_parameters(
        self,
        output_path: str,
        output_format: str,
        table_name: str,
        schema: str
    ) -> None:
        """Validate extraction parameters.
        
        Args:
            output_path: Output file path
            output_format: Output format
            table_name: Table name
            schema: Schema name
            
        Raises:
            ValueError: If parameters are invalid
        """
        if not output_path:
            raise ValueError("Output path is required")
        
        if output_format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format: {output_format}. Supported: {self.SUPPORTED_FORMATS}")
        
        if not table_name:
            raise ValueError("Table name is required")
        
        if not schema:
            raise ValueError("Schema name is required")
        
        # Validate output path extension matches format
        output_file = Path(output_path)
        expected_extension = f".{output_format}"
        if not output_file.suffix.lower() == expected_extension:
            raise ValueError(f"Output path should have {expected_extension} extension")
    
    def _get_table_row_count(
        self,
        table_name: str,
        schema: str,
        query_filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """Get the number of rows in a table with optional filters.
        
        Args:
            table_name: Name of the table
            schema: Database schema name
            query_filters: Optional filters to apply
            
        Returns:
            Number of rows
        """
        try:
            with self.db_connection.get_session() as session:
                # Build count query
                count_query = f"SELECT COUNT(*) FROM {schema}.{table_name}"
                
                # Add filters if provided
                if query_filters:
                    where_conditions = []
                    for column, value in query_filters.items():
                        if isinstance(value, list):
                            # Handle IN clause
                            placeholders = ','.join([f"'{v}'" for v in value])
                            where_conditions.append(f"{column} IN ({placeholders})")
                        else:
                            where_conditions.append(f"{column} = '{value}'")
                    
                    if where_conditions:
                        count_query += " WHERE " + " AND ".join(where_conditions)
                
                result = session.execute(text(count_query))
                return result.scalar() or 0
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get row count: {e}")
            raise
    
    def _extract_single_chunk(
        self,
        output_path: str,
        output_format: str,
        table_name: str,
        schema: str,
        query_filters: Optional[Dict[str, Any]],
        format_options: Dict[str, Any]
    ) -> int:
        """Extract data in a single operation for small datasets.
        
        Args:
            output_path: Output file path
            output_format: Output format
            table_name: Table name
            schema: Schema name
            query_filters: Query filters
            format_options: Format-specific options
            
        Returns:
            Number of rows extracted
        """
        try:
            with self.db_connection.get_session() as session:
                # Build query
                query = f"SELECT * FROM {schema}.{table_name}"
                
                # Add filters if provided
                if query_filters:
                    where_conditions = []
                    for column, value in query_filters.items():
                        if isinstance(value, list):
                            placeholders = ','.join([f"'{v}'" for v in value])
                            where_conditions.append(f"{column} IN ({placeholders})")
                        else:
                            where_conditions.append(f"{column} = '{value}'")
                    
                    if where_conditions:
                        query += " WHERE " + " AND ".join(where_conditions)
                
                # Execute query and load into DataFrame
                df = pd.read_sql(query, session.connection())
                
                # Write to file
                self._write_dataframe_to_file(df, output_path, output_format, format_options)
                
                return len(df)
                
        except Exception as e:
            logger.error(f"Single chunk extraction failed: {e}")
            raise
    
    def _extract_in_chunks(
        self,
        output_path: str,
        output_format: str,
        table_name: str,
        schema: str,
        query_filters: Optional[Dict[str, Any]],
        chunk_size: int,
        format_options: Dict[str, Any],
        total_rows: int
    ) -> int:
        """Extract data in chunks for large datasets.
        
        Args:
            output_path: Output file path
            output_format: Output format
            table_name: Table name
            schema: Schema name
            query_filters: Query filters
            chunk_size: Size of each chunk
            format_options: Format-specific options
            total_rows: Total number of rows
            
        Returns:
            Number of rows extracted
        """
        logger.info(f"Extracting {total_rows} rows in chunks of {chunk_size}")
        
        extracted_rows = 0
        first_chunk = True
        
        try:
            with self.db_connection.get_session() as session:
                # Build base query
                base_query = f"SELECT * FROM {schema}.{table_name}"
                
                # Add filters if provided
                if query_filters:
                    where_conditions = []
                    for column, value in query_filters.items():
                        if isinstance(value, list):
                            placeholders = ','.join([f"'{v}'" for v in value])
                            where_conditions.append(f"{column} IN ({placeholders})")
                        else:
                            where_conditions.append(f"{column} = '{value}'")
                    
                    if where_conditions:
                        base_query += " WHERE " + " AND ".join(where_conditions)
                
                # Process chunks
                for offset in range(0, total_rows, chunk_size):
                    chunk_query = f"{base_query} LIMIT {chunk_size} OFFSET {offset}"
                    
                    # Load chunk into DataFrame
                    chunk_df = pd.read_sql(chunk_query, session.connection())
                    
                    if len(chunk_df) == 0:
                        break
                    
                    # Write chunk to file
                    if output_format == 'csv':
                        self._append_csv_chunk(
                            chunk_df, output_path, format_options, 
                            include_header=first_chunk
                        )
                    else:  # parquet
                        # For parquet, we need to collect all chunks and write once
                        # or use a different approach
                        if first_chunk:
                            all_chunks = [chunk_df]
                        else:
                            all_chunks.append(chunk_df)
                    
                    extracted_rows += len(chunk_df)
                    first_chunk = False
                    
                    logger.debug(f"Processed chunk: {offset}-{offset + len(chunk_df)}")
                
                # For parquet, write all chunks at once
                if output_format == 'parquet' and extracted_rows > 0:
                    combined_df = pd.concat(all_chunks, ignore_index=True)
                    self._write_dataframe_to_file(
                        combined_df, output_path, output_format, format_options
                    )
                
                return extracted_rows
                
        except Exception as e:
            logger.error(f"Chunked extraction failed: {e}")
            raise
    
    def _write_dataframe_to_file(
        self,
        df: pd.DataFrame,
        output_path: str,
        output_format: str,
        format_options: Dict[str, Any]
    ) -> None:
        """Write DataFrame to file in specified format.
        
        Args:
            df: DataFrame to write
            output_path: Output file path
            output_format: Output format
            format_options: Format-specific options
        """
        if output_format == 'csv':
            df.to_csv(
                output_path,
                index=format_options.get('index', False),
                header=format_options.get('include_header', True),
                date_format=format_options.get('date_format', '%Y-%m-%d %H:%M:%S')
            )
        elif output_format == 'parquet':
            df.to_parquet(
                output_path,
                index=format_options.get('index', False),
                compression=format_options.get('compression', 'snappy')
            )
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _append_csv_chunk(
        self,
        chunk_df: pd.DataFrame,
        output_path: str,
        format_options: Dict[str, Any],
        include_header: bool
    ) -> None:
        """Append a chunk to CSV file.
        
        Args:
            chunk_df: DataFrame chunk to append
            output_path: Output file path
            format_options: Format-specific options
            include_header: Whether to include header
        """
        mode = 'w' if include_header else 'a'
        chunk_df.to_csv(
            output_path,
            mode=mode,
            index=format_options.get('index', False),
            header=include_header,
            date_format=format_options.get('date_format', '%Y-%m-%d %H:%M:%S')
        )
    
    def extract_raw_transactions(
        self,
        output_path: str,
        output_format: str = "csv",
        company_ids: Optional[List[str]] = None,
        status_filter: Optional[List[str]] = None,
        date_range: Optional[Dict[str, str]] = None
    ) -> ExtractionMetadata:
        """Extract raw transaction data with common filters.
        
        Args:
            output_path: Path where file will be saved
            output_format: Output format ('csv' or 'parquet')
            company_ids: Optional list of company IDs to filter by
            status_filter: Optional list of statuses to filter by
            date_range: Optional date range filter with 'start' and 'end' keys
            
        Returns:
            ExtractionMetadata with extraction details
        """
        query_filters = {}
        
        if company_ids:
            query_filters['company_id'] = company_ids
        
        if status_filter:
            query_filters['status'] = status_filter
        
        # Note: Date range filtering would require more complex SQL for string dates
        # This is a simplified implementation
        
        if output_format == 'csv':
            return self.extract_to_csv(
                output_path=output_path,
                table_name="raw_transactions",
                schema="raw_data",
                query_filters=query_filters
            )
        elif output_format == 'parquet':
            return self.extract_to_parquet(
                output_path=output_path,
                table_name="raw_transactions",
                schema="raw_data",
                query_filters=query_filters
            )
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    def extract_normalized_data(
        self,
        output_path: str,
        output_format: str = "csv",
        table_name: str = "charges",
        company_ids: Optional[List[str]] = None,
        status_filter: Optional[List[str]] = None
    ) -> ExtractionMetadata:
        """Extract normalized data (charges or companies).
        
        Args:
            output_path: Path where file will be saved
            output_format: Output format ('csv' or 'parquet')
            table_name: Table to extract ('charges' or 'companies')
            company_ids: Optional list of company IDs to filter by
            status_filter: Optional list of statuses to filter by (charges only)
            
        Returns:
            ExtractionMetadata with extraction details
        """
        if table_name not in ['charges', 'companies']:
            raise ValueError("table_name must be 'charges' or 'companies'")
        
        query_filters = {}
        
        if company_ids:
            query_filters['company_id'] = company_ids
        
        if status_filter and table_name == 'charges':
            query_filters['status'] = status_filter
        
        if output_format == 'csv':
            return self.extract_to_csv(
                output_path=output_path,
                table_name=table_name,
                schema="normalized_data",
                query_filters=query_filters
            )
        elif output_format == 'parquet':
            return self.extract_to_parquet(
                output_path=output_path,
                table_name=table_name,
                schema="normalized_data",
                query_filters=query_filters
            )
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    def extract_daily_summary(
        self,
        output_path: str,
        output_format: str = "csv"
    ) -> ExtractionMetadata:
        """Extract data from the daily transaction summary view.
        
        Args:
            output_path: Path where file will be saved
            output_format: Output format ('csv' or 'parquet')
            
        Returns:
            ExtractionMetadata with extraction details
        """
        if output_format == 'csv':
            return self.extract_to_csv(
                output_path=output_path,
                table_name="daily_transaction_summary",
                schema="normalized_data"
            )
        elif output_format == 'parquet':
            return self.extract_to_parquet(
                output_path=output_path,
                table_name="daily_transaction_summary",
                schema="normalized_data"
            )
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    def get_extraction_metadata(self, extraction_id: Optional[str] = None) -> Union[ExtractionMetadata, List[ExtractionMetadata]]:
        """Get extraction metadata for specific extraction or all extractions.
        
        Args:
            extraction_id: Optional extraction ID to get specific metadata
            
        Returns:
            ExtractionMetadata for specific extraction or list of all metadata
        """
        if extraction_id:
            for metadata in self._extraction_history:
                if metadata.extraction_id == extraction_id:
                    return metadata
            raise ValueError(f"Extraction ID not found: {extraction_id}")
        
        return self._extraction_history.copy()
    
    def get_extraction_statistics(self) -> ExtractionStatistics:
        """Generate statistics for all extraction operations.
        
        Returns:
            ExtractionStatistics with aggregated statistics
        """
        if not self._extraction_history:
            return ExtractionStatistics(
                total_extractions=0,
                successful_extractions=0,
                failed_extractions=0,
                total_rows_extracted=0,
                total_execution_time_seconds=0.0,
                formats_used={},
                average_extraction_time=0.0,
                largest_extraction_rows=0
            )
        
        successful_extractions = [
            m for m in self._extraction_history 
            if m.extraction_success_rate == 100.0
        ]
        
        failed_extractions = len(self._extraction_history) - len(successful_extractions)
        
        total_rows = sum(m.extracted_rows for m in self._extraction_history)
        total_time = sum(m.execution_time_seconds for m in self._extraction_history)
        
        # Count formats used
        formats_used = {}
        for metadata in self._extraction_history:
            format_name = metadata.output_format
            formats_used[format_name] = formats_used.get(format_name, 0) + 1
        
        # Find largest extraction
        largest_extraction = max(
            self._extraction_history,
            key=lambda m: m.extracted_rows,
            default=self._extraction_history[0]
        )
        
        return ExtractionStatistics(
            total_extractions=len(self._extraction_history),
            successful_extractions=len(successful_extractions),
            failed_extractions=failed_extractions,
            total_rows_extracted=total_rows,
            total_execution_time_seconds=total_time,
            formats_used=formats_used,
            average_extraction_time=total_time / len(self._extraction_history),
            largest_extraction_rows=largest_extraction.extracted_rows
        )
    
    def clear_extraction_history(self) -> None:
        """Clear the extraction history."""
        self._extraction_history.clear()
        logger.info("Extraction history cleared")
    
    def export_extraction_metadata(self, output_path: str) -> None:
        """Export extraction metadata to JSON file.
        
        Args:
            output_path: Path where JSON file will be saved
        """
        import json
        
        metadata_list = [m.to_dict() for m in self._extraction_history]
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump({
                'extraction_history': metadata_list,
                'statistics': self.get_extraction_statistics().__dict__,
                'export_timestamp': datetime.now().isoformat()
            }, f, indent=2, default=str)
        
        logger.info(f"Extraction metadata exported to: {output_path}")
    
    def validate_output_file(self, file_path: str) -> Dict[str, Any]:
        """Validate an extracted output file.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Dictionary with validation results
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            return {
                'valid': False,
                'error': 'File does not exist',
                'file_path': file_path
            }
        
        try:
            file_size = file_path_obj.stat().st_size
            
            # Try to read the file based on extension
            if file_path_obj.suffix.lower() == '.csv':
                df = pd.read_csv(file_path, nrows=5)  # Read first 5 rows for validation
                file_format = 'csv'
            elif file_path_obj.suffix.lower() == '.parquet':
                df = pd.read_parquet(file_path)
                file_format = 'parquet'
            else:
                return {
                    'valid': False,
                    'error': 'Unsupported file format',
                    'file_path': file_path
                }
            
            return {
                'valid': True,
                'file_path': file_path,
                'file_format': file_format,
                'file_size_bytes': file_size,
                'columns': list(df.columns),
                'column_count': len(df.columns),
                'sample_row_count': len(df),
                'estimated_total_rows': 'unknown' if file_format == 'parquet' else None
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'file_path': file_path
            }