"""Input validation utilities for API endpoints and data processing."""

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from src.exceptions import (
    DataValidationError, NumberOutOfRangeError, InvalidAmountError,
    InvalidStatusError, FileFormatError, DateConsistencyError
)


class ValidationResult:
    """Result of a validation operation."""
    
    def __init__(self, is_valid: bool = True):
        self.is_valid = is_valid
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.cleaned_value: Any = None
    
    def add_error(self, error: str) -> None:
        """Add an error and mark validation as failed."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str) -> None:
        """Add a warning (doesn't affect validity)."""
        self.warnings.append(warning)
    
    def set_cleaned_value(self, value: Any) -> None:
        """Set the cleaned/normalized value."""
        self.cleaned_value = value


class InputValidator:
    """Comprehensive input validation for API endpoints and data processing."""
    
    # Valid status values for transactions
    VALID_STATUSES = {
        'paid', 'pending_payment', 'voided', 'refunded', 
        'pre_authorized', 'charged_back'
    }
    
    # Maximum field lengths
    MAX_LENGTHS = {
        'id': 24,
        'company_id': 24,
        'company_name': 130,
        'status': 30
    }
    
    # Date format patterns
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
    
    # Supported file formats
    SUPPORTED_FILE_FORMATS = {'.csv', '.parquet'}
    
    @staticmethod
    def validate_number_range(number: int, min_value: int = 1, max_value: int = 100) -> ValidationResult:
        """Validate that a number is within the specified range.
        
        Args:
            number: Number to validate
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            
        Returns:
            ValidationResult with validation outcome
            
        Raises:
            NumberOutOfRangeError: If number is outside valid range
        """
        result = ValidationResult()
        
        if not isinstance(number, int):
            result.add_error(f"Number must be an integer, got {type(number).__name__}")
            return result
        
        if number < min_value or number > max_value:
            raise NumberOutOfRangeError(number, min_value, max_value)
        
        result.set_cleaned_value(number)
        return result
    
    @staticmethod
    def validate_amount(amount: Any, allow_zero: bool = False) -> ValidationResult:
        """Validate transaction amount.
        
        Args:
            amount: Amount to validate
            allow_zero: Whether to allow zero amounts
            
        Returns:
            ValidationResult with validation outcome
            
        Raises:
            InvalidAmountError: If amount is invalid
        """
        result = ValidationResult()
        
        if amount is None:
            result.add_error("Amount is required")
            return result
        
        try:
            decimal_amount = Decimal(str(amount))
            
            if decimal_amount < 0:
                raise InvalidAmountError(amount, "Amount cannot be negative")
            
            if not allow_zero and decimal_amount == 0:
                raise InvalidAmountError(amount, "Amount cannot be zero")
            
            # Check for reasonable precision (max 2 decimal places for currency)
            if decimal_amount.as_tuple().exponent < -2:
                result.add_warning("Amount has more than 2 decimal places, will be rounded")
                decimal_amount = decimal_amount.quantize(Decimal('0.01'))
            
            result.set_cleaned_value(decimal_amount)
            return result
            
        except (InvalidOperation, ValueError) as e:
            raise InvalidAmountError(amount, f"Invalid amount format: {str(e)}")
    
    @staticmethod
    def validate_status(status: str) -> ValidationResult:
        """Validate transaction status.
        
        Args:
            status: Status to validate
            
        Returns:
            ValidationResult with validation outcome
            
        Raises:
            InvalidStatusError: If status is invalid
        """
        result = ValidationResult()
        
        if not status or not isinstance(status, str):
            result.add_error("Status is required and must be a string")
            return result
        
        cleaned_status = status.strip().lower()
        
        if not cleaned_status:
            result.add_error("Status cannot be empty")
            return result
        
        if cleaned_status not in InputValidator.VALID_STATUSES:
            raise InvalidStatusError(status, list(InputValidator.VALID_STATUSES))
        
        result.set_cleaned_value(cleaned_status)
        return result
    
    @staticmethod
    def validate_string_field(value: Any, field_name: str, required: bool = True, 
                            max_length: Optional[int] = None, min_length: int = 0) -> ValidationResult:
        """Validate a string field with length constraints.
        
        Args:
            value: Value to validate
            field_name: Name of the field for error messages
            required: Whether the field is required
            max_length: Maximum allowed length
            min_length: Minimum required length
            
        Returns:
            ValidationResult with validation outcome
        """
        result = ValidationResult()
        
        if value is None or (isinstance(value, str) and not value.strip()):
            if required:
                result.add_error(f"{field_name} is required")
                return result
            else:
                result.set_cleaned_value(None)
                return result
        
        if not isinstance(value, str):
            result.add_error(f"{field_name} must be a string, got {type(value).__name__}")
            return result
        
        cleaned_value = value.strip()
        
        if len(cleaned_value) < min_length:
            result.add_error(f"{field_name} must be at least {min_length} characters long")
            return result
        
        if max_length and len(cleaned_value) > max_length:
            result.add_warning(f"{field_name} exceeds maximum length of {max_length}, will be truncated")
            cleaned_value = cleaned_value[:max_length]
        
        result.set_cleaned_value(cleaned_value)
        return result
    
    @staticmethod
    def validate_id_field(value: Any, field_name: str = "ID") -> ValidationResult:
        """Validate an ID field.
        
        Args:
            value: ID value to validate
            field_name: Name of the field for error messages
            
        Returns:
            ValidationResult with validation outcome
        """
        max_length = InputValidator.MAX_LENGTHS.get(field_name.lower(), 24)
        return InputValidator.validate_string_field(
            value, field_name, required=True, max_length=max_length, min_length=1
        )
    
    @staticmethod
    def validate_date(date_value: Any, field_name: str, required: bool = True) -> ValidationResult:
        """Validate and parse a date field.
        
        Args:
            date_value: Date value to validate
            field_name: Name of the field for error messages
            required: Whether the field is required
            
        Returns:
            ValidationResult with validation outcome
        """
        result = ValidationResult()
        
        if date_value is None or (isinstance(date_value, str) and not date_value.strip()):
            if required:
                result.add_error(f"{field_name} is required")
            else:
                result.set_cleaned_value(None)
            return result
        
        if isinstance(date_value, datetime):
            result.set_cleaned_value(date_value)
            return result
        
        date_str = str(date_value).strip()
        
        # Try different date formats
        for pattern in InputValidator.DATE_PATTERNS:
            try:
                parsed_date = datetime.strptime(date_str, pattern)
                result.set_cleaned_value(parsed_date)
                return result
            except ValueError:
                continue
        
        # Try pandas parsing as fallback
        try:
            import pandas as pd
            parsed_date = pd.to_datetime(date_str, errors='raise')
            result.set_cleaned_value(parsed_date.to_pydatetime())
            result.add_warning(f"{field_name} parsed with fallback method")
            return result
        except (ValueError, ImportError):
            pass
        
        result.add_error(f"Unable to parse {field_name}: {date_str}")
        return result
    
    @staticmethod
    def validate_date_consistency(created_at: datetime, updated_at: Optional[datetime] = None,
                                paid_at: Optional[datetime] = None) -> ValidationResult:
        """Validate date consistency rules.
        
        Args:
            created_at: Creation date
            updated_at: Update date (optional)
            paid_at: Payment date (optional)
            
        Returns:
            ValidationResult with validation outcome
            
        Raises:
            DateConsistencyError: If dates are inconsistent
        """
        result = ValidationResult()
        
        if updated_at and updated_at < created_at:
            raise DateConsistencyError(
                "Updated date cannot be before created date",
                created_at=created_at.isoformat(),
                updated_at=updated_at.isoformat()
            )
        
        if paid_at and paid_at < created_at:
            raise DateConsistencyError(
                "Payment date cannot be before created date",
                created_at=created_at.isoformat(),
                updated_at=paid_at.isoformat()
            )
        
        return result
    
    @staticmethod
    def validate_file_path(file_path: str, expected_format: Optional[str] = None,
                          must_exist: bool = False) -> ValidationResult:
        """Validate file path and format.
        
        Args:
            file_path: File path to validate
            expected_format: Expected file format (e.g., 'csv', 'parquet')
            must_exist: Whether the file must exist
            
        Returns:
            ValidationResult with validation outcome
            
        Raises:
            FileFormatError: If file format is invalid
        """
        result = ValidationResult()
        
        if not file_path or not isinstance(file_path, str):
            result.add_error("File path is required and must be a string")
            return result
        
        path_obj = Path(file_path)
        
        if must_exist and not path_obj.exists():
            result.add_error(f"File does not exist: {file_path}")
            return result
        
        if expected_format:
            expected_extension = f".{expected_format.lower()}"
            if path_obj.suffix.lower() != expected_extension:
                raise FileFormatError(file_path, expected_format)
        
        # Check if format is supported
        if path_obj.suffix.lower() not in InputValidator.SUPPORTED_FILE_FORMATS:
            result.add_error(f"Unsupported file format: {path_obj.suffix}")
            return result
        
        result.set_cleaned_value(str(path_obj))
        return result
    
    @staticmethod
    def validate_batch_size(batch_size: Any) -> ValidationResult:
        """Validate batch size parameter.
        
        Args:
            batch_size: Batch size to validate
            
        Returns:
            ValidationResult with validation outcome
        """
        result = ValidationResult()
        
        if batch_size is None:
            result.set_cleaned_value(1000)  # Default batch size
            return result
        
        if not isinstance(batch_size, int):
            try:
                batch_size = int(batch_size)
            except (ValueError, TypeError):
                result.add_error("Batch size must be an integer")
                return result
        
        if batch_size <= 0:
            result.add_error("Batch size must be positive")
            return result
        
        if batch_size > 100000:
            result.add_warning("Large batch size may cause memory issues")
        
        result.set_cleaned_value(batch_size)
        return result
    
    @staticmethod
    def validate_query_filters(filters: Optional[Dict[str, Any]]) -> ValidationResult:
        """Validate query filters dictionary.
        
        Args:
            filters: Query filters to validate
            
        Returns:
            ValidationResult with validation outcome
        """
        result = ValidationResult()
        
        if filters is None:
            result.set_cleaned_value({})
            return result
        
        if not isinstance(filters, dict):
            result.add_error("Query filters must be a dictionary")
            return result
        
        cleaned_filters = {}
        
        for key, value in filters.items():
            if not isinstance(key, str):
                result.add_error(f"Filter key must be string, got {type(key).__name__}")
                continue
            
            # Validate common filter types
            if key in ['company_id', 'status']:
                if isinstance(value, list):
                    # Validate list of values
                    cleaned_values = []
                    for v in value:
                        if isinstance(v, str) and v.strip():
                            cleaned_values.append(v.strip())
                    if cleaned_values:
                        cleaned_filters[key] = cleaned_values
                elif isinstance(value, str) and value.strip():
                    cleaned_filters[key] = value.strip()
            else:
                # For other filters, just ensure they're not empty
                if value is not None and str(value).strip():
                    cleaned_filters[key] = value
        
        result.set_cleaned_value(cleaned_filters)
        return result
    
    @staticmethod
    def validate_transaction_record(record: Dict[str, Any]) -> ValidationResult:
        """Validate a complete transaction record.
        
        Args:
            record: Transaction record to validate
            
        Returns:
            ValidationResult with validation outcome
        """
        result = ValidationResult()
        cleaned_record = {}
        
        # Validate ID
        id_result = InputValidator.validate_id_field(record.get('id'), 'ID')
        if not id_result.is_valid:
            result.errors.extend(id_result.errors)
        else:
            cleaned_record['id'] = id_result.cleaned_value
        
        # Validate company ID
        company_id_result = InputValidator.validate_id_field(record.get('company_id'), 'Company ID')
        if not company_id_result.is_valid:
            result.errors.extend(company_id_result.errors)
        else:
            cleaned_record['company_id'] = company_id_result.cleaned_value
        
        # Validate company name
        name_result = InputValidator.validate_string_field(
            record.get('name'), 'Company Name', required=False, 
            max_length=InputValidator.MAX_LENGTHS['company_name']
        )
        result.warnings.extend(name_result.warnings)
        if name_result.is_valid:
            cleaned_record['company_name'] = name_result.cleaned_value or 'Unknown Company'
        
        # Validate amount
        try:
            amount_result = InputValidator.validate_amount(record.get('amount'))
            if amount_result.is_valid:
                cleaned_record['amount'] = amount_result.cleaned_value
                result.warnings.extend(amount_result.warnings)
        except InvalidAmountError as e:
            result.add_error(e.message)
        
        # Validate status
        try:
            status_result = InputValidator.validate_status(record.get('status'))
            if status_result.is_valid:
                cleaned_record['status'] = status_result.cleaned_value
        except InvalidStatusError as e:
            result.add_error(e.message)
        
        # Validate dates
        created_at_result = InputValidator.validate_date(record.get('created_at'), 'Created At', required=True)
        if created_at_result.is_valid:
            cleaned_record['created_at'] = created_at_result.cleaned_value
            result.warnings.extend(created_at_result.warnings)
        else:
            result.errors.extend(created_at_result.errors)
        
        updated_at_result = InputValidator.validate_date(record.get('updated_at'), 'Updated At', required=False)
        if updated_at_result.is_valid:
            cleaned_record['updated_at'] = updated_at_result.cleaned_value
            result.warnings.extend(updated_at_result.warnings)
        else:
            result.errors.extend(updated_at_result.errors)
        
        # Validate date consistency if both dates are valid
        if 'created_at' in cleaned_record and 'updated_at' in cleaned_record:
            try:
                InputValidator.validate_date_consistency(
                    cleaned_record['created_at'], 
                    cleaned_record['updated_at']
                )
            except DateConsistencyError as e:
                result.add_error(e.message)
        
        if result.errors:
            result.is_valid = False
        else:
            result.set_cleaned_value(cleaned_record)
        
        return result


class APIInputValidator:
    """Specialized validator for API endpoints."""
    
    @staticmethod
    def validate_extract_number_input(number: Any) -> int:
        """Validate input for extract number endpoint.
        
        Args:
            number: Number to validate
            
        Returns:
            Validated number
            
        Raises:
            NumberOutOfRangeError: If number is invalid
        """
        if not isinstance(number, int):
            try:
                number = int(number)
            except (ValueError, TypeError):
                raise NumberOutOfRangeError(number, 1, 100)
        
        result = InputValidator.validate_number_range(number, 1, 100)
        if not result.is_valid:
            raise NumberOutOfRangeError(number, 1, 100)
        
        return result.cleaned_value
    
    @staticmethod
    def validate_pagination_params(limit: Any = None, offset: Any = None) -> Tuple[Optional[int], Optional[int]]:
        """Validate pagination parameters.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            Tuple of (validated_limit, validated_offset)
        """
        validated_limit = None
        validated_offset = None
        
        if limit is not None:
            try:
                validated_limit = int(limit)
                if validated_limit <= 0:
                    raise ValueError("Limit must be positive")
                if validated_limit > 10000:
                    validated_limit = 10000  # Cap at reasonable maximum
            except (ValueError, TypeError):
                raise DataValidationError("Limit must be a positive integer")
        
        if offset is not None:
            try:
                validated_offset = int(offset)
                if validated_offset < 0:
                    raise ValueError("Offset must be non-negative")
            except (ValueError, TypeError):
                raise DataValidationError("Offset must be a non-negative integer")
        
        return validated_limit, validated_offset
    
    @staticmethod
    def validate_date_range_params(start_date: Any = None, end_date: Any = None) -> Tuple[Optional[str], Optional[str]]:
        """Validate date range parameters for API queries.
        
        Args:
            start_date: Start date string
            end_date: End date string
            
        Returns:
            Tuple of (validated_start_date, validated_end_date)
        """
        validated_start = None
        validated_end = None
        
        if start_date is not None:
            start_result = InputValidator.validate_date(start_date, "Start Date", required=False)
            if not start_result.is_valid:
                raise DataValidationError(f"Invalid start date: {'; '.join(start_result.errors)}")
            if start_result.cleaned_value:
                validated_start = start_result.cleaned_value.strftime('%Y-%m-%d')
        
        if end_date is not None:
            end_result = InputValidator.validate_date(end_date, "End Date", required=False)
            if not end_result.is_valid:
                raise DataValidationError(f"Invalid end date: {'; '.join(end_result.errors)}")
            if end_result.cleaned_value:
                validated_end = end_result.cleaned_value.strftime('%Y-%m-%d')
        
        # Validate date range consistency
        if validated_start and validated_end:
            if validated_start > validated_end:
                raise DataValidationError("Start date cannot be after end date")
        
        return validated_start, validated_end