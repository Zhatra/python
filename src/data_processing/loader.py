"""Data loader module for CSV file ingestion and database loading."""

import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.database.connection import DatabaseConnection
from src.database.models import RawTransaction
from src.exceptions import (
    DataLoadingError, DataValidationError, DatabaseError, 
    FileNotFoundError, FileFormatError
)
from src.validation import InputValidator

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Report containing validation results and statistics."""
    
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    duplicates: int
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_rows == 0:
            return 0.0
        return (self.valid_rows / self.total_rows) * 100
    
    def __str__(self) -> str:
        return (
            f"ValidationReport(total={self.total_rows}, "
            f"valid={self.valid_rows}, invalid={self.invalid_rows}, "
            f"success_rate={self.success_rate:.2f}%)"
        )


@dataclass
class LoadingReport:
    """Report containing loading results and statistics."""
    
    file_path: str
    total_rows_processed: int
    rows_loaded: int
    rows_skipped: int
    validation_report: ValidationReport
    loading_errors: List[Dict[str, Any]]
    execution_time_seconds: float
    
    @property
    def loading_success_rate(self) -> float:
        """Calculate loading success rate as percentage."""
        if self.total_rows_processed == 0:
            return 0.0
        return (self.rows_loaded / self.total_rows_processed) * 100
    
    def __str__(self) -> str:
        return (
            f"LoadingReport(file={Path(self.file_path).name}, "
            f"processed={self.total_rows_processed}, loaded={self.rows_loaded}, "
            f"loading_success_rate={self.loading_success_rate:.2f}%)"
        )


class DataLoader:
    """Handles CSV file ingestion and database loading operations."""
    
    # Expected CSV columns
    EXPECTED_COLUMNS = ['id', 'name', 'company_id', 'amount', 'status', 'created_at', 'paid_at']
    
    # Valid status values
    VALID_STATUSES = {
        'paid', 'pending_payment', 'voided', 'refunded', 
        'pre_authorized', 'charged_back'
    }
    
    # Maximum field lengths based on database schema
    MAX_LENGTHS = {
        'id': 64,
        'name': 130,
        'company_id': 64,
        'status': 50,
        'created_at': 50,
        'paid_at': 50
    }
    
    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """Initialize DataLoader with database connection.
        
        Args:
            db_connection: Database connection instance. If None, uses global instance.
        """
        from src.database.connection import db_connection as global_db_connection
        self.db_connection = db_connection or global_db_connection
    
    def load_csv_to_database(
        self, 
        csv_path: str, 
        batch_size: int = 1000,
        validate_data: bool = True
    ) -> LoadingReport:
        """Load CSV data into the database.
        
        Args:
            csv_path: Path to the CSV file to load
            batch_size: Number of rows to process in each batch
            validate_data: Whether to perform data validation
            
        Returns:
            LoadingReport with detailed results and statistics
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        import time
        start_time = time.time()
        
        logger.info(f"Starting CSV loading from: {csv_path}")
        
        # Validate file exists and format
        try:
            file_validation = InputValidator.validate_file_path(csv_path, 'csv', must_exist=True)
            if not file_validation.is_valid:
                raise DataLoadingError(
                    f"Invalid CSV file: {'; '.join(file_validation.errors)}",
                    file_path=csv_path
                )
        except FileNotFoundError:
            raise DataLoadingError(f"CSV file not found: {csv_path}", file_path=csv_path)
        
        try:
            # Read CSV file
            df = self._read_csv_file(csv_path)
            logger.info(f"Read {len(df)} rows from CSV file")
            
            # Validate data if requested
            validation_report = ValidationReport(
                total_rows=len(df),
                valid_rows=0,
                invalid_rows=0,
                errors=[],
                warnings=[],
                duplicates=0
            )
            
            if validate_data:
                validation_report = self.validate_data_integrity(df)
                logger.info(f"Validation completed: {validation_report}")
            
            # Load data to database
            rows_loaded, loading_errors = self._load_dataframe_to_database(
                df, batch_size
            )
            
            execution_time = time.time() - start_time
            
            # Create loading report
            loading_report = LoadingReport(
                file_path=csv_path,
                total_rows_processed=len(df),
                rows_loaded=rows_loaded,
                rows_skipped=len(df) - rows_loaded,
                validation_report=validation_report,
                loading_errors=loading_errors,
                execution_time_seconds=execution_time
            )
            
            logger.info(f"Loading completed: {loading_report}")
            return loading_report
            
        except DataLoadingError:
            # Re-raise our custom exceptions
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error during CSV loading: {e}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during CSV loading: {e}")
            raise DataLoadingError(f"Failed to load CSV data: {str(e)}", file_path=csv_path)
    
    def _read_csv_file(self, csv_path: str) -> pd.DataFrame:
        """Read and parse CSV file with proper handling.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            DataFrame with parsed CSV data
            
        Raises:
            ValueError: If CSV format is invalid
        """
        try:
            # Read CSV with pandas, handling various edge cases
            df = pd.read_csv(
                csv_path,
                dtype=str,  # Read all columns as strings initially
                na_values=['', 'NULL', 'null', 'None'],
                keep_default_na=False,
                encoding='utf-8'
            )
            
            # Validate expected columns
            missing_columns = set(self.EXPECTED_COLUMNS) - set(df.columns)
            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")
            
            # Select only expected columns in correct order
            df = df[self.EXPECTED_COLUMNS].copy()
            
            # Replace NaN values with None for database compatibility
            df = df.where(pd.notnull(df), None)
            
            return df
            
        except pd.errors.EmptyDataError:
            raise FileFormatError(csv_path, "csv")
        except pd.errors.ParserError as e:
            raise FileFormatError(csv_path, "csv")
        except Exception as e:
            raise DataLoadingError(f"Error reading CSV file: {str(e)}", file_path=csv_path)
    
    def validate_data_integrity(self, df: pd.DataFrame) -> ValidationReport:
        """Validate data integrity and quality.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            ValidationReport with validation results
        """
        logger.info("Starting data integrity validation")
        
        errors = []
        warnings = []
        valid_rows = 0
        
        # Check for duplicates
        duplicates = df.duplicated(subset=['id']).sum()
        if duplicates > 0:
            warnings.append({
                'type': 'duplicates',
                'message': f"Found {duplicates} duplicate IDs",
                'count': duplicates
            })
        
        # Validate each row
        for idx, row in df.iterrows():
            row_errors = self._validate_row(row, idx)
            if row_errors:
                errors.extend(row_errors)
            else:
                valid_rows += 1
        
        invalid_rows = len(df) - valid_rows
        
        validation_report = ValidationReport(
            total_rows=len(df),
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            errors=errors,
            warnings=warnings,
            duplicates=duplicates
        )
        
        logger.info(f"Validation completed: {validation_report}")
        return validation_report
    
    def _validate_row(self, row: pd.Series, row_index: int) -> List[Dict[str, Any]]:
        """Validate a single row of data.
        
        Args:
            row: Row data to validate
            row_index: Index of the row for error reporting
            
        Returns:
            List of validation errors for this row
        """
        errors = []
        
        # Validate required fields
        if pd.isna(row['id']) or not row['id']:
            errors.append({
                'type': 'missing_required_field',
                'field': 'id',
                'row': row_index,
                'message': 'ID is required'
            })
        
        if pd.isna(row['company_id']) or not row['company_id']:
            errors.append({
                'type': 'missing_required_field',
                'field': 'company_id',
                'row': row_index,
                'message': 'Company ID is required'
            })
        
        # Validate field lengths
        for field, max_length in self.MAX_LENGTHS.items():
            if row[field] and len(str(row[field])) > max_length:
                errors.append({
                    'type': 'field_too_long',
                    'field': field,
                    'row': row_index,
                    'message': f'{field} exceeds maximum length of {max_length}',
                    'value_length': len(str(row[field]))
                })
        
        # Validate amount
        if row['amount']:
            try:
                amount = Decimal(str(row['amount']))
                if amount < 0:
                    errors.append({
                        'type': 'invalid_amount',
                        'field': 'amount',
                        'row': row_index,
                        'message': 'Amount cannot be negative',
                        'value': str(row['amount'])
                    })
            except (InvalidOperation, ValueError):
                errors.append({
                    'type': 'invalid_amount_format',
                    'field': 'amount',
                    'row': row_index,
                    'message': 'Amount must be a valid decimal number',
                    'value': str(row['amount'])
                })
        
        # Validate status
        if row['status'] and row['status'] not in self.VALID_STATUSES:
            errors.append({
                'type': 'invalid_status',
                'field': 'status',
                'row': row_index,
                'message': f'Invalid status. Must be one of: {self.VALID_STATUSES}',
                'value': row['status']
            })
        
        # Validate date formats (basic check)
        for date_field in ['created_at', 'paid_at']:
            if row[date_field]:
                if not self._is_valid_date_format(row[date_field]):
                    errors.append({
                        'type': 'invalid_date_format',
                        'field': date_field,
                        'row': row_index,
                        'message': f'{date_field} has invalid date format',
                        'value': row[date_field]
                    })
        
        return errors
    
    def _is_valid_date_format(self, date_str: str) -> bool:
        """Check if date string has a valid format.
        
        Args:
            date_str: Date string to validate
            
        Returns:
            True if date format appears valid
        """
        if not date_str or pd.isna(date_str):
            return True  # Empty dates are allowed
        
        # Basic date format validation (YYYY-MM-DD)
        try:
            pd.to_datetime(date_str, errors='raise')
            return True
        except (ValueError, TypeError):
            return False
    
    def _load_dataframe_to_database(
        self, 
        df: pd.DataFrame, 
        batch_size: int
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Load DataFrame data to database in batches.
        
        Args:
            df: DataFrame to load
            batch_size: Number of rows per batch
            
        Returns:
            Tuple of (rows_loaded, loading_errors)
        """
        logger.info(f"Loading {len(df)} rows to database in batches of {batch_size}")
        
        rows_loaded = 0
        loading_errors = []
        
        try:
            with self.db_connection.get_transaction() as session:
                # Process data in batches
                for start_idx in range(0, len(df), batch_size):
                    end_idx = min(start_idx + batch_size, len(df))
                    batch_df = df.iloc[start_idx:end_idx]
                    
                    batch_loaded, batch_errors = self._load_batch_to_database(
                        session, batch_df, start_idx
                    )
                    
                    rows_loaded += batch_loaded
                    loading_errors.extend(batch_errors)
                    
                    logger.debug(f"Loaded batch {start_idx}-{end_idx}: {batch_loaded} rows")
                
                logger.info(f"Successfully loaded {rows_loaded} rows to database")
                
        except SQLAlchemyError as e:
            logger.error(f"Database error during loading: {e}")
            loading_errors.append({
                'type': 'database_error',
                'message': str(e),
                'batch': 'transaction'
            })
        
        return rows_loaded, loading_errors
    
    def _load_batch_to_database(
        self, 
        session: Session, 
        batch_df: pd.DataFrame, 
        batch_start_idx: int
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Load a single batch of data to database.
        
        Args:
            session: Database session
            batch_df: Batch DataFrame to load
            batch_start_idx: Starting index for error reporting
            
        Returns:
            Tuple of (rows_loaded, batch_errors)
        """
        batch_errors = []
        rows_loaded = 0
        
        for idx, row in batch_df.iterrows():
            try:
                # Convert row to RawTransaction model
                raw_transaction = self._row_to_raw_transaction(row)
                
                # Add to session
                session.add(raw_transaction)
                rows_loaded += 1
                
            except Exception as e:
                batch_errors.append({
                    'type': 'row_conversion_error',
                    'row': batch_start_idx + idx,
                    'message': str(e),
                    'data': row.to_dict()
                })
        
        try:
            # Flush the batch
            session.flush()
        except SQLAlchemyError as e:
            # If batch fails, try to identify problematic rows
            logger.warning(f"Batch flush failed, attempting individual row processing: {e}")
            session.rollback()
            
            # Process rows individually to identify issues
            individual_loaded, individual_errors = self._load_rows_individually(
                session, batch_df, batch_start_idx
            )
            
            rows_loaded = individual_loaded
            batch_errors.extend(individual_errors)
        
        return rows_loaded, batch_errors
    
    def _load_rows_individually(
        self, 
        session: Session, 
        batch_df: pd.DataFrame, 
        batch_start_idx: int
    ) -> Tuple[int, List[Dict[str, Any]]]:
        """Load rows individually when batch loading fails.
        
        Args:
            session: Database session
            batch_df: Batch DataFrame to load
            batch_start_idx: Starting index for error reporting
            
        Returns:
            Tuple of (rows_loaded, individual_errors)
        """
        individual_errors = []
        rows_loaded = 0
        
        for idx, row in batch_df.iterrows():
            try:
                raw_transaction = self._row_to_raw_transaction(row)
                session.add(raw_transaction)
                session.flush()
                rows_loaded += 1
                
            except SQLAlchemyError as e:
                session.rollback()
                individual_errors.append({
                    'type': 'individual_row_error',
                    'row': batch_start_idx + idx,
                    'message': str(e),
                    'data': row.to_dict()
                })
        
        return rows_loaded, individual_errors
    
    def _row_to_raw_transaction(self, row: pd.Series) -> RawTransaction:
        """Convert DataFrame row to RawTransaction model.
        
        Args:
            row: DataFrame row
            
        Returns:
            RawTransaction model instance
            
        Raises:
            ValueError: If row data is invalid
        """
        try:
            # Convert amount to Decimal if present
            amount = None
            if row['amount'] and not pd.isna(row['amount']):
                amount = Decimal(str(row['amount']))
            
            return RawTransaction(
                id=row['id'] if row['id'] and not pd.isna(row['id']) else None,
                name=row['name'] if row['name'] and not pd.isna(row['name']) else None,
                company_id=row['company_id'] if row['company_id'] and not pd.isna(row['company_id']) else None,
                amount=amount,
                status=row['status'] if row['status'] and not pd.isna(row['status']) else None,
                created_at=row['created_at'] if row['created_at'] and not pd.isna(row['created_at']) else None,
                paid_at=row['paid_at'] if row['paid_at'] and not pd.isna(row['paid_at']) else None
            )
            
        except Exception as e:
            raise ValueError(f"Failed to convert row to RawTransaction: {e}")
    
    def get_loading_statistics(self) -> Dict[str, Any]:
        """Get statistics about loaded data.
        
        Returns:
            Dictionary with loading statistics
        """
        try:
            with self.db_connection.get_session() as session:
                # Count total rows
                total_count = session.query(RawTransaction).count()
                
                # Count by status
                status_counts = {}
                for status in self.VALID_STATUSES:
                    count = session.query(RawTransaction).filter(
                        RawTransaction.status == status
                    ).count()
                    if count > 0:
                        status_counts[status] = count
                
                # Count rows with amounts
                rows_with_amount = session.query(RawTransaction).filter(
                    RawTransaction.amount.isnot(None)
                ).count()
                
                # Get unique companies
                unique_companies = session.query(RawTransaction.company_id).distinct().count()
                
                return {
                    'total_rows': total_count,
                    'status_distribution': status_counts,
                    'rows_with_amount': rows_with_amount,
                    'unique_companies': unique_companies,
                    'table_name': 'raw_transactions'
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get loading statistics: {e}")
            return {'error': str(e)}