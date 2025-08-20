"""Custom exception classes for business logic errors."""

from typing import Any, Dict, List, Optional


class TechnicalTestError(Exception):
    """Base exception class for all technical test application errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """Initialize base exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            'error': self.error_code,
            'message': self.message,
            'details': self.details
        }


# Data Processing Exceptions
class DataProcessingError(TechnicalTestError):
    """Base exception for data processing errors."""
    pass


class DataValidationError(DataProcessingError):
    """Exception raised when data validation fails."""
    
    def __init__(self, message: str, validation_errors: Optional[List[Dict[str, Any]]] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.validation_errors = validation_errors or []
        self.details['validation_errors'] = self.validation_errors


class DataTransformationError(DataProcessingError):
    """Exception raised when data transformation fails."""
    
    def __init__(self, message: str, transformation_stage: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.transformation_stage = transformation_stage
        if transformation_stage:
            self.details['transformation_stage'] = transformation_stage


class DataLoadingError(DataProcessingError):
    """Exception raised when data loading fails."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, rows_processed: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.file_path = file_path
        self.rows_processed = rows_processed
        if file_path:
            self.details['file_path'] = file_path
        if rows_processed is not None:
            self.details['rows_processed'] = rows_processed


class DataExtractionError(DataProcessingError):
    """Exception raised when data extraction fails."""
    
    def __init__(self, message: str, output_path: Optional[str] = None, output_format: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.output_path = output_path
        self.output_format = output_format
        if output_path:
            self.details['output_path'] = output_path
        if output_format:
            self.details['output_format'] = output_format


# Database Exceptions
class DatabaseError(TechnicalTestError):
    """Base exception for database-related errors."""
    pass


class DatabaseConnectionError(DatabaseError):
    """Exception raised when database connection fails."""
    
    def __init__(self, message: str, connection_string: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        # Don't include sensitive connection details in the exception
        if connection_string:
            # Mask password in connection string
            masked_connection = self._mask_connection_string(connection_string)
            self.details['connection_string'] = masked_connection
    
    def _mask_connection_string(self, connection_string: str) -> str:
        """Mask sensitive information in connection string."""
        try:
            # Simple masking - replace password with asterisks
            if '@' in connection_string and ':' in connection_string:
                parts = connection_string.split('@')
                if len(parts) == 2:
                    user_pass = parts[0].split(':')
                    if len(user_pass) >= 3:  # protocol:user:password
                        user_pass[-1] = '***'
                        parts[0] = ':'.join(user_pass)
                        return '@'.join(parts)
            return connection_string
        except Exception:
            return "***"


class DatabaseTransactionError(DatabaseError):
    """Exception raised when database transaction fails."""
    
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.operation = operation
        if operation:
            self.details['operation'] = operation


class DatabaseSchemaError(DatabaseError):
    """Exception raised when database schema operations fail."""
    
    def __init__(self, message: str, schema_name: Optional[str] = None, table_name: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.schema_name = schema_name
        self.table_name = table_name
        if schema_name:
            self.details['schema_name'] = schema_name
        if table_name:
            self.details['table_name'] = table_name


# API Exceptions
class APIError(TechnicalTestError):
    """Base exception for API-related errors."""
    pass


class NumberSetError(APIError):
    """Exception raised for NumberSet operations."""
    
    def __init__(self, message: str, number: Optional[int] = None, operation: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.number = number
        self.operation = operation
        if number is not None:
            self.details['number'] = number
        if operation:
            self.details['operation'] = operation


class NumberAlreadyExtractedError(NumberSetError):
    """Exception raised when trying to extract an already extracted number."""
    
    def __init__(self, number: int, **kwargs):
        super().__init__(
            f"Number {number} has already been extracted",
            number=number,
            operation="extract",
            error_code="NUMBER_ALREADY_EXTRACTED",
            **kwargs
        )


class NumberOutOfRangeError(NumberSetError):
    """Exception raised when number is outside valid range."""
    
    def __init__(self, number: int, min_value: int = 1, max_value: int = 100, **kwargs):
        super().__init__(
            f"Number {number} is outside valid range ({min_value}-{max_value})",
            number=number,
            error_code="NUMBER_OUT_OF_RANGE",
            **kwargs
        )
        self.details.update({
            'min_value': min_value,
            'max_value': max_value
        })


class NoNumbersExtractedError(NumberSetError):
    """Exception raised when trying to find missing number but no numbers extracted."""
    
    def __init__(self, **kwargs):
        super().__init__(
            "No numbers have been extracted yet. Extract a number first.",
            operation="find_missing",
            error_code="NO_NUMBERS_EXTRACTED",
            **kwargs
        )


class MultipleNumbersExtractedError(NumberSetError):
    """Exception raised when multiple numbers are extracted but single missing expected."""
    
    def __init__(self, extracted_count: int, **kwargs):
        super().__init__(
            f"Cannot find single missing number when {extracted_count} numbers are extracted",
            operation="find_missing",
            error_code="MULTIPLE_NUMBERS_EXTRACTED",
            **kwargs
        )
        self.details['extracted_count'] = extracted_count


# Configuration Exceptions
class ConfigurationError(TechnicalTestError):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, config_key: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.config_key = config_key
        if config_key:
            self.details['config_key'] = config_key


# File System Exceptions
class FileSystemError(TechnicalTestError):
    """Exception raised for file system operations."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, operation: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.file_path = file_path
        self.operation = operation
        if file_path:
            self.details['file_path'] = file_path
        if operation:
            self.details['operation'] = operation


class FileNotFoundError(FileSystemError):
    """Exception raised when required file is not found."""
    
    def __init__(self, file_path: str, **kwargs):
        super().__init__(
            f"File not found: {file_path}",
            file_path=file_path,
            operation="read",
            error_code="FILE_NOT_FOUND",
            **kwargs
        )


class FileFormatError(FileSystemError):
    """Exception raised when file format is invalid."""
    
    def __init__(self, file_path: str, expected_format: Optional[str] = None, **kwargs):
        message = f"Invalid file format: {file_path}"
        if expected_format:
            message += f" (expected: {expected_format})"
        
        super().__init__(
            message,
            file_path=file_path,
            operation="parse",
            error_code="INVALID_FILE_FORMAT",
            **kwargs
        )
        if expected_format:
            self.details['expected_format'] = expected_format


# Business Logic Exceptions
class BusinessLogicError(TechnicalTestError):
    """Exception raised for business logic violations."""
    pass


class InvalidStatusError(BusinessLogicError):
    """Exception raised when transaction status is invalid."""
    
    def __init__(self, status: str, valid_statuses: Optional[List[str]] = None, **kwargs):
        message = f"Invalid status: {status}"
        if valid_statuses:
            message += f". Valid statuses: {', '.join(valid_statuses)}"
        
        super().__init__(
            message,
            error_code="INVALID_STATUS",
            **kwargs
        )
        self.details.update({
            'invalid_status': status,
            'valid_statuses': valid_statuses or []
        })


class InvalidAmountError(BusinessLogicError):
    """Exception raised when transaction amount is invalid."""
    
    def __init__(self, amount: Any, reason: str = "Invalid amount", **kwargs):
        super().__init__(
            f"{reason}: {amount}",
            error_code="INVALID_AMOUNT",
            **kwargs
        )
        self.details.update({
            'invalid_amount': str(amount),
            'reason': reason
        })


class DateConsistencyError(BusinessLogicError):
    """Exception raised when dates are inconsistent."""
    
    def __init__(self, message: str, created_at: Optional[str] = None, updated_at: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            error_code="DATE_CONSISTENCY_ERROR",
            **kwargs
        )
        if created_at:
            self.details['created_at'] = created_at
        if updated_at:
            self.details['updated_at'] = updated_at