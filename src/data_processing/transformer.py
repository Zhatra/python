"""Data transformer module for schema transformation and data cleaning."""

import logging
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
import re

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func

from src.database.connection import DatabaseConnection
from src.database.models import RawTransaction, Company, Charge

logger = logging.getLogger(__name__)


@dataclass
class TransformationReport:
    """Report containing transformation results and statistics."""
    
    total_raw_rows: int
    transformed_rows: int
    skipped_rows: int
    companies_created: int
    charges_created: int
    transformation_errors: List[Dict[str, Any]]
    data_quality_issues: List[Dict[str, Any]]
    execution_time_seconds: float
    
    @property
    def transformation_success_rate(self) -> float:
        """Calculate transformation success rate as percentage."""
        if self.total_raw_rows == 0:
            return 100.0
        return (self.transformed_rows / self.total_raw_rows) * 100
    
    def __str__(self) -> str:
        return (
            f"TransformationReport(total={self.total_raw_rows}, "
            f"transformed={self.transformed_rows}, "
            f"companies={self.companies_created}, charges={self.charges_created}, "
            f"success_rate={self.transformation_success_rate:.2f}%)"
        )


@dataclass
class ValidationResult:
    """Result of data validation."""
    
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    cleaned_value: Any = None
    
    def add_error(self, error: str) -> None:
        """Add an error to the validation result."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning to the validation result."""
        self.warnings.append(warning)


class DataTransformer:
    """Handles data transformation from raw to normalized schema."""
    
    # Target schema field lengths
    TARGET_SCHEMA_LENGTHS = {
        'id': 24,
        'company_name': 130,
        'company_id': 24,
        'status': 30
    }
    
    # Valid status values for normalized schema
    VALID_STATUSES = {
        'paid', 'pending_payment', 'voided', 'refunded', 
        'pre_authorized', 'charged_back'
    }
    
    # Date format patterns to try for parsing
    DATE_PATTERNS = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y/%m/%d',
        '%Y/%m/%d %H:%M:%S',
        '%d-%m-%Y',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ'
    ]
    
    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """Initialize DataTransformer with database connection.
        
        Args:
            db_connection: Database connection instance. If None, uses global instance.
        """
        from src.database.connection import db_connection as global_db_connection
        self.db_connection = db_connection or global_db_connection
    
    def transform_to_schema(
        self, 
        source_table: str = "raw_transactions",
        batch_size: int = 1000,
        validate_data: bool = True,
        apply_business_rules: bool = True
    ) -> TransformationReport:
        """Transform raw data to match target normalized schema.
        
        Args:
            source_table: Source table name to transform from
            batch_size: Number of rows to process in each batch
            validate_data: Whether to perform data validation
            apply_business_rules: Whether to apply business rules
            
        Returns:
            TransformationReport with transformation results
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        import time
        start_time = time.time()
        
        logger.info(f"Starting data transformation from {source_table}")
        
        transformation_errors = []
        data_quality_issues = []
        transformed_rows = 0
        companies_created = 0
        charges_created = 0
        
        try:
            with self.db_connection.get_transaction() as session:
                # Get raw data
                raw_data = session.query(RawTransaction).all()
                total_raw_rows = len(raw_data)
                
                logger.info(f"Processing {total_raw_rows} raw transaction records")
                
                if total_raw_rows == 0:
                    logger.warning("No raw data found to transform")
                    return TransformationReport(
                        total_raw_rows=0,
                        transformed_rows=0,
                        skipped_rows=0,
                        companies_created=0,
                        charges_created=0,
                        transformation_errors=[],
                        data_quality_issues=[],
                        execution_time_seconds=time.time() - start_time
                    )
                
                # Convert to DataFrame for easier processing
                df = self._raw_data_to_dataframe(raw_data)
                
                # Apply data validation if requested
                if validate_data:
                    df, validation_issues = self._validate_transformed_data(df)
                    data_quality_issues.extend(validation_issues)
                
                # Apply business rules if requested
                if apply_business_rules:
                    df, business_rule_issues = self._apply_business_rules(df)
                    data_quality_issues.extend(business_rule_issues)
                
                # Extract unique companies
                companies_df = self._extract_companies(df)
                companies_created = self._load_companies(session, companies_df)
                
                # Transform charges
                charges_df = self._transform_charges(df)
                charges_created = self._load_charges(session, charges_df)
                
                transformed_rows = len(charges_df)
                
                execution_time = time.time() - start_time
                
                report = TransformationReport(
                    total_raw_rows=total_raw_rows,
                    transformed_rows=transformed_rows,
                    skipped_rows=total_raw_rows - transformed_rows,
                    companies_created=companies_created,
                    charges_created=charges_created,
                    transformation_errors=transformation_errors,
                    data_quality_issues=data_quality_issues,
                    execution_time_seconds=execution_time
                )
                
                logger.info(f"Transformation completed: {report}")
                return report
                
        except Exception as e:
            logger.error(f"Transformation failed: {e}")
            raise
    
    def _raw_data_to_dataframe(self, raw_data: List[RawTransaction]) -> pd.DataFrame:
        """Convert raw transaction data to DataFrame.
        
        Args:
            raw_data: List of RawTransaction objects
            
        Returns:
            DataFrame with raw transaction data
        """
        data = []
        for raw_tx in raw_data:
            data.append({
                'id': raw_tx.id,
                'name': raw_tx.name,
                'company_id': raw_tx.company_id,
                'amount': raw_tx.amount,
                'status': raw_tx.status,
                'created_at': raw_tx.created_at,
                'paid_at': raw_tx.paid_at
            })
        
        return pd.DataFrame(data)
    
    def _validate_transformed_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Validate data quality and integrity.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (validated_df, validation_issues)
        """
        logger.info("Validating transformed data")
        
        validation_issues = []
        valid_rows = []
        
        for idx, row in df.iterrows():
            validation_result = self._validate_row_for_transformation(row, idx)
            
            if validation_result.is_valid:
                # Use cleaned values if available
                if validation_result.cleaned_value:
                    valid_rows.append(validation_result.cleaned_value)
                else:
                    valid_rows.append(row.to_dict())
            else:
                validation_issues.append({
                    'type': 'validation_error',
                    'row_index': idx,
                    'errors': validation_result.errors,
                    'warnings': validation_result.warnings,
                    'original_data': row.to_dict()
                })
        
        validated_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame()
        
        logger.info(f"Validation completed: {len(valid_rows)}/{len(df)} rows valid")
        return validated_df, validation_issues
    
    def _validate_row_for_transformation(self, row: pd.Series, row_index: int) -> ValidationResult:
        """Validate a single row for transformation.
        
        Args:
            row: Row data to validate
            row_index: Index of the row for error reporting
            
        Returns:
            ValidationResult with validation outcome
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        cleaned_row = row.to_dict()
        
        # Validate required fields
        if pd.isna(row['id']) or not str(row['id']).strip():
            result.add_error("ID is required")
        else:
            # Clean and validate ID length
            cleaned_id = str(row['id']).strip()
            if len(cleaned_id) > self.TARGET_SCHEMA_LENGTHS['id']:
                # Truncate ID to fit target schema
                cleaned_id = cleaned_id[:self.TARGET_SCHEMA_LENGTHS['id']]
                result.add_warning(f"ID truncated to {self.TARGET_SCHEMA_LENGTHS['id']} characters")
            cleaned_row['id'] = cleaned_id
        
        if pd.isna(row['company_id']) or not str(row['company_id']).strip():
            result.add_error("Company ID is required")
        else:
            # Clean and validate company_id length
            cleaned_company_id = str(row['company_id']).strip()
            if len(cleaned_company_id) > self.TARGET_SCHEMA_LENGTHS['company_id']:
                cleaned_company_id = cleaned_company_id[:self.TARGET_SCHEMA_LENGTHS['company_id']]
                result.add_warning(f"Company ID truncated to {self.TARGET_SCHEMA_LENGTHS['company_id']} characters")
            cleaned_row['company_id'] = cleaned_company_id
        
        # Validate and clean company name
        if pd.isna(row['name']) or not str(row['name']).strip():
            result.add_warning("Company name is missing")
            cleaned_row['name'] = 'Unknown Company'
        else:
            cleaned_name = str(row['name']).strip()
            if len(cleaned_name) > self.TARGET_SCHEMA_LENGTHS['company_name']:
                cleaned_name = cleaned_name[:self.TARGET_SCHEMA_LENGTHS['company_name']]
                result.add_warning(f"Company name truncated to {self.TARGET_SCHEMA_LENGTHS['company_name']} characters")
            cleaned_row['name'] = cleaned_name
        
        # Validate amount
        if pd.isna(row['amount']):
            result.add_error("Amount is required")
        else:
            try:
                amount = Decimal(str(row['amount']))
                if amount < 0:
                    result.add_error("Amount cannot be negative")
                else:
                    cleaned_row['amount'] = amount
            except (InvalidOperation, ValueError):
                result.add_error(f"Invalid amount format: {row['amount']}")
        
        # Validate and clean status
        if pd.isna(row['status']) or not str(row['status']).strip():
            result.add_error("Status is required")
        else:
            cleaned_status = str(row['status']).strip().lower()
            if cleaned_status not in self.VALID_STATUSES:
                result.add_error(f"Invalid status: {cleaned_status}. Valid statuses: {self.VALID_STATUSES}")
            else:
                if len(cleaned_status) > self.TARGET_SCHEMA_LENGTHS['status']:
                    cleaned_status = cleaned_status[:self.TARGET_SCHEMA_LENGTHS['status']]
                    result.add_warning(f"Status truncated to {self.TARGET_SCHEMA_LENGTHS['status']} characters")
                cleaned_row['status'] = cleaned_status
        
        # Validate and convert dates
        created_at_result = self._parse_and_validate_date(row['created_at'], 'created_at')
        if not created_at_result.is_valid:
            result.errors.extend(created_at_result.errors)
        else:
            cleaned_row['created_at'] = created_at_result.cleaned_value
        
        # paid_at is optional
        if not pd.isna(row['paid_at']) and str(row['paid_at']).strip():
            paid_at_result = self._parse_and_validate_date(row['paid_at'], 'paid_at')
            if not paid_at_result.is_valid:
                result.warnings.extend([f"paid_at: {error}" for error in paid_at_result.errors])
                cleaned_row['paid_at'] = None
            else:
                cleaned_row['paid_at'] = paid_at_result.cleaned_value
        else:
            cleaned_row['paid_at'] = None
        
        if result.is_valid:
            result.cleaned_value = cleaned_row
        
        return result
    
    def _parse_and_validate_date(self, date_value: Any, field_name: str) -> ValidationResult:
        """Parse and validate a date field.
        
        Args:
            date_value: Date value to parse
            field_name: Name of the field for error reporting
            
        Returns:
            ValidationResult with parsed date or errors
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if pd.isna(date_value) or not str(date_value).strip():
            if field_name == 'created_at':
                result.add_error(f"{field_name} is required")
            return result
        
        date_str = str(date_value).strip()
        
        # Try different date formats
        for pattern in self.DATE_PATTERNS:
            try:
                parsed_date = datetime.strptime(date_str, pattern)
                result.cleaned_value = parsed_date
                return result
            except ValueError:
                continue
        
        # If no pattern matched, try pandas parsing as last resort
        try:
            parsed_date = pd.to_datetime(date_str, errors='raise')
            result.cleaned_value = parsed_date.to_pydatetime()
            result.add_warning(f"{field_name} parsed with fallback method")
            return result
        except (ValueError, TypeError):
            result.add_error(f"Unable to parse {field_name}: {date_str}")
        
        return result
    
    def _apply_business_rules(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Apply business rules and data cleaning strategies.
        
        Args:
            df: DataFrame to apply business rules to
            
        Returns:
            Tuple of (cleaned_df, business_rule_issues)
        """
        logger.info("Applying business rules")
        
        business_rule_issues = []
        cleaned_df = df.copy()
        
        # Business Rule 1: Remove duplicate transactions
        initial_count = len(cleaned_df)
        cleaned_df = cleaned_df.drop_duplicates(subset=['id'], keep='first')
        duplicates_removed = initial_count - len(cleaned_df)
        
        if duplicates_removed > 0:
            business_rule_issues.append({
                'type': 'duplicates_removed',
                'message': f"Removed {duplicates_removed} duplicate transactions",
                'count': duplicates_removed
            })
        
        # Business Rule 2: Standardize company names
        cleaned_df['name'] = cleaned_df['name'].apply(self._standardize_company_name)
        
        # Business Rule 3: Handle edge cases for amounts
        # Convert very small amounts (< 0.01) to 0.01 to avoid precision issues
        small_amounts = cleaned_df['amount'] < Decimal('0.01')
        if small_amounts.any():
            count = small_amounts.sum()
            cleaned_df.loc[small_amounts, 'amount'] = Decimal('0.01')
            business_rule_issues.append({
                'type': 'small_amounts_adjusted',
                'message': f"Adjusted {count} amounts smaller than 0.01 to 0.01",
                'count': count
            })
        
        # Business Rule 4: Set updated_at for paid transactions
        paid_mask = cleaned_df['status'] == 'paid'
        if 'paid_at' in cleaned_df.columns:
            cleaned_df.loc[paid_mask, 'updated_at'] = cleaned_df.loc[paid_mask, 'paid_at']
        else:
            # If paid_at column doesn't exist, set updated_at to created_at for paid transactions
            cleaned_df.loc[paid_mask, 'updated_at'] = cleaned_df.loc[paid_mask, 'created_at']
        
        # Business Rule 5: Validate date consistency
        date_issues = self._validate_date_consistency(cleaned_df)
        business_rule_issues.extend(date_issues)
        
        logger.info(f"Business rules applied: {len(business_rule_issues)} issues identified")
        return cleaned_df, business_rule_issues
    
    def _standardize_company_name(self, company_name: str) -> str:
        """Standardize company name format.
        
        Args:
            company_name: Raw company name
            
        Returns:
            Standardized company name
        """
        if pd.isna(company_name) or not str(company_name).strip():
            return 'Unknown Company'
        
        # Clean and standardize
        name = str(company_name).strip()
        
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name)
        
        # Capitalize first letter of each word
        name = name.title()
        
        return name
    
    def _validate_date_consistency(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Validate date consistency rules.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            List of date consistency issues
        """
        issues = []
        
        # Check if paid_at is after created_at for paid transactions
        paid_df = df[df['status'] == 'paid'].copy()
        if not paid_df.empty:
            # Only check rows where both dates are available
            both_dates = paid_df.dropna(subset=['created_at', 'paid_at'])
            if not both_dates.empty:
                inconsistent = both_dates['paid_at'] < both_dates['created_at']
                if inconsistent.any():
                    count = inconsistent.sum()
                    issues.append({
                        'type': 'date_consistency_error',
                        'message': f"Found {count} paid transactions where paid_at is before created_at",
                        'count': count
                    })
        
        return issues
    
    def _extract_companies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract unique companies from transaction data.
        
        Args:
            df: DataFrame with transaction data
            
        Returns:
            DataFrame with unique companies
        """
        companies = df[['company_id', 'name']].drop_duplicates(subset=['company_id'])
        companies = companies.rename(columns={'name': 'company_name'})
        companies['created_at'] = datetime.now()
        companies['updated_at'] = None
        
        return companies
    
    def _transform_charges(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform transaction data to charges format.
        
        Args:
            df: DataFrame with transaction data
            
        Returns:
            DataFrame with charges data
        """
        charges = df[['id', 'company_id', 'amount', 'status', 'created_at', 'updated_at']].copy()
        
        # Ensure updated_at is properly set
        charges['updated_at'] = charges.apply(
            lambda row: row['updated_at'] if pd.notna(row['updated_at']) else None,
            axis=1
        )
        
        return charges
    
    def _load_companies(self, session, companies_df: pd.DataFrame) -> int:
        """Load companies into the database.
        
        Args:
            session: Database session
            companies_df: DataFrame with company data
            
        Returns:
            Number of companies created
        """
        companies_created = 0
        
        for _, row in companies_df.iterrows():
            # Check if company already exists
            existing = session.query(Company).filter(
                Company.company_id == row['company_id']
            ).first()
            
            if not existing:
                company = Company(
                    company_id=row['company_id'],
                    company_name=row['company_name'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                session.add(company)
                companies_created += 1
        
        session.flush()
        return companies_created
    
    def _load_charges(self, session, charges_df: pd.DataFrame) -> int:
        """Load charges into the database.
        
        Args:
            session: Database session
            charges_df: DataFrame with charges data
            
        Returns:
            Number of charges created
        """
        charges_created = 0
        
        for _, row in charges_df.iterrows():
            # Check if charge already exists
            existing = session.query(Charge).filter(
                Charge.id == row['id']
            ).first()
            
            if not existing:
                charge = Charge(
                    id=row['id'],
                    company_id=row['company_id'],
                    amount=row['amount'],
                    status=row['status'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                session.add(charge)
                charges_created += 1
        
        session.flush()
        return charges_created
    
    def get_transformation_statistics(self) -> Dict[str, Any]:
        """Get statistics about transformed data.
        
        Returns:
            Dictionary with transformation statistics
        """
        try:
            with self.db_connection.get_session() as session:
                # Count companies
                companies_count = session.query(Company).count()
                
                # Count charges
                charges_count = session.query(Charge).count()
                
                # Count charges by status
                status_counts = {}
                for status in self.VALID_STATUSES:
                    count = session.query(Charge).filter(
                        Charge.status == status
                    ).count()
                    if count > 0:
                        status_counts[status] = count
                
                # Get date range
                date_stats = session.query(
                    func.min(Charge.created_at).label('earliest_date'),
                    func.max(Charge.created_at).label('latest_date')
                ).first()
                
                return {
                    'companies_count': companies_count,
                    'charges_count': charges_count,
                    'status_distribution': status_counts,
                    'date_range': {
                        'earliest': date_stats.earliest_date.isoformat() if date_stats.earliest_date else None,
                        'latest': date_stats.latest_date.isoformat() if date_stats.latest_date else None
                    },
                    'schema': 'normalized_data'
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to get transformation statistics: {e}")
            return {'error': str(e)}
    
    def validate_transformation_integrity(self) -> Dict[str, Any]:
        """Validate the integrity of the transformation.
        
        Returns:
            Dictionary with integrity validation results
        """
        try:
            with self.db_connection.get_session() as session:
                # Count raw vs transformed records
                raw_count = session.query(RawTransaction).count()
                charges_count = session.query(Charge).count()
                
                # Check for orphaned charges (charges without companies)
                orphaned_charges = session.query(Charge).outerjoin(Company).filter(
                    Company.company_id.is_(None)
                ).count()
                
                # Check for companies without charges
                companies_without_charges = session.query(Company).outerjoin(Charge).filter(
                    Charge.company_id.is_(None)
                ).count()
                
                # Validate amount consistency
                amount_issues = session.query(Charge).filter(
                    Charge.amount <= 0
                ).count()
                
                # Validate date consistency
                date_issues = session.query(Charge).filter(
                    Charge.updated_at < Charge.created_at
                ).count()
                
                integrity_score = 100.0
                issues = []
                
                if orphaned_charges > 0:
                    issues.append(f"{orphaned_charges} charges without corresponding companies")
                    integrity_score -= 20
                
                if amount_issues > 0:
                    issues.append(f"{amount_issues} charges with invalid amounts")
                    integrity_score -= 10
                
                if date_issues > 0:
                    issues.append(f"{date_issues} charges with date inconsistencies")
                    integrity_score -= 10
                
                return {
                    'integrity_score': max(0, integrity_score),
                    'raw_records': raw_count,
                    'transformed_records': charges_count,
                    'transformation_rate': (charges_count / raw_count * 100) if raw_count > 0 else 0,
                    'orphaned_charges': orphaned_charges,
                    'companies_without_charges': companies_without_charges,
                    'amount_issues': amount_issues,
                    'date_issues': date_issues,
                    'issues': issues,
                    'is_valid': len(issues) == 0
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to validate transformation integrity: {e}")
            return {'error': str(e), 'is_valid': False}