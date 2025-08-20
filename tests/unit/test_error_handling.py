"""Tests for comprehensive error handling and validation."""

import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import Mock, patch

from src.exceptions import (
    TechnicalTestError, DataValidationError, NumberOutOfRangeError,
    NumberAlreadyExtractedError, NoNumbersExtractedError, 
    MultipleNumbersExtractedError, InvalidAmountError, InvalidStatusError,
    DatabaseConnectionError, DatabaseTransactionError, FileNotFoundError,
    FileFormatError, DateConsistencyError
)
from src.validation import InputValidator, APIInputValidator, ValidationResult
from src.api.number_set import NumberSet


class TestCustomExceptions:
    """Test custom exception classes."""
    
    def test_technical_test_error_base(self):
        """Test base TechnicalTestError functionality."""
        error = TechnicalTestError(
            "Test error message",
            error_code="TEST_ERROR",
            details={"key": "value"}
        )
        
        assert error.message == "Test error message"
        assert error.error_code == "TEST_ERROR"
        assert error.details == {"key": "value"}
        
        error_dict = error.to_dict()
        assert error_dict["error"] == "TEST_ERROR"
        assert error_dict["message"] == "Test error message"
        assert error_dict["details"] == {"key": "value"}
    
    def test_number_out_of_range_error(self):
        """Test NumberOutOfRangeError exception."""
        error = NumberOutOfRangeError(150, 1, 100)
        
        assert error.number == 150
        assert error.error_code == "NUMBER_OUT_OF_RANGE"
        assert "150 is outside valid range (1-100)" in error.message
        assert error.details["min_value"] == 1
        assert error.details["max_value"] == 100
    
    def test_number_already_extracted_error(self):
        """Test NumberAlreadyExtractedError exception."""
        error = NumberAlreadyExtractedError(42)
        
        assert error.number == 42
        assert error.operation == "extract"
        assert error.error_code == "NUMBER_ALREADY_EXTRACTED"
        assert "42 has already been extracted" in error.message
    
    def test_no_numbers_extracted_error(self):
        """Test NoNumbersExtractedError exception."""
        error = NoNumbersExtractedError()
        
        assert error.operation == "find_missing"
        assert error.error_code == "NO_NUMBERS_EXTRACTED"
        assert "No numbers have been extracted" in error.message
    
    def test_multiple_numbers_extracted_error(self):
        """Test MultipleNumbersExtractedError exception."""
        error = MultipleNumbersExtractedError(5)
        
        assert error.operation == "find_missing"
        assert error.error_code == "MULTIPLE_NUMBERS_EXTRACTED"
        assert "5 numbers are extracted" in error.message
        assert error.details["extracted_count"] == 5
    
    def test_invalid_amount_error(self):
        """Test InvalidAmountError exception."""
        error = InvalidAmountError(-10.50, "Amount cannot be negative")
        
        assert error.error_code == "INVALID_AMOUNT"
        assert "Amount cannot be negative: -10.5" in error.message
        assert error.details["invalid_amount"] == "-10.5"
        assert error.details["reason"] == "Amount cannot be negative"
    
    def test_invalid_status_error(self):
        """Test InvalidStatusError exception."""
        valid_statuses = ["paid", "pending", "refunded"]
        error = InvalidStatusError("invalid_status", valid_statuses)
        
        assert error.error_code == "INVALID_STATUS"
        assert "Invalid status: invalid_status" in error.message
        assert error.details["invalid_status"] == "invalid_status"
        assert error.details["valid_statuses"] == valid_statuses
    
    def test_database_connection_error(self):
        """Test DatabaseConnectionError exception."""
        connection_string = "postgresql://user:password@localhost/db"
        error = DatabaseConnectionError("Connection failed", connection_string)
        
        assert "Connection failed" in error.message
        # Password should be masked
        assert "password" not in error.details["connection_string"]
        assert "***" in error.details["connection_string"]
    
    def test_date_consistency_error(self):
        """Test DateConsistencyError exception."""
        created_at = "2023-01-01T10:00:00"
        updated_at = "2022-12-31T10:00:00"
        error = DateConsistencyError(
            "Updated date before created date",
            created_at=created_at,
            updated_at=updated_at
        )
        
        assert error.error_code == "DATE_CONSISTENCY_ERROR"
        assert error.details["created_at"] == created_at
        assert error.details["updated_at"] == updated_at


class TestInputValidator:
    """Test input validation utilities."""
    
    def test_validate_number_range_valid(self):
        """Test valid number range validation."""
        result = InputValidator.validate_number_range(50, 1, 100)
        
        assert result.is_valid
        assert result.cleaned_value == 50
        assert len(result.errors) == 0
    
    def test_validate_number_range_invalid_type(self):
        """Test number range validation with invalid type."""
        result = InputValidator.validate_number_range("not_a_number", 1, 100)
        
        assert not result.is_valid
        assert "must be an integer" in result.errors[0]
    
    def test_validate_number_range_out_of_range(self):
        """Test number range validation with out of range value."""
        with pytest.raises(NumberOutOfRangeError):
            InputValidator.validate_number_range(150, 1, 100)
    
    def test_validate_amount_valid(self):
        """Test valid amount validation."""
        result = InputValidator.validate_amount("123.45")
        
        assert result.is_valid
        assert result.cleaned_value == Decimal("123.45")
        assert len(result.errors) == 0
    
    def test_validate_amount_negative(self):
        """Test amount validation with negative value."""
        with pytest.raises(InvalidAmountError) as exc_info:
            InputValidator.validate_amount(-50.0)
        
        assert "cannot be negative" in str(exc_info.value)
    
    def test_validate_amount_zero_not_allowed(self):
        """Test amount validation with zero when not allowed."""
        with pytest.raises(InvalidAmountError) as exc_info:
            InputValidator.validate_amount(0, allow_zero=False)
        
        assert "cannot be zero" in str(exc_info.value)
    
    def test_validate_amount_zero_allowed(self):
        """Test amount validation with zero when allowed."""
        result = InputValidator.validate_amount(0, allow_zero=True)
        
        assert result.is_valid
        assert result.cleaned_value == Decimal("0")
    
    def test_validate_amount_high_precision(self):
        """Test amount validation with high precision."""
        result = InputValidator.validate_amount("123.456789")
        
        assert result.is_valid
        assert result.cleaned_value == Decimal("123.46")  # Rounded to 2 decimal places
        assert "more than 2 decimal places" in result.warnings[0]
    
    def test_validate_amount_invalid_format(self):
        """Test amount validation with invalid format."""
        with pytest.raises(InvalidAmountError) as exc_info:
            InputValidator.validate_amount("not_a_number")
        
        assert "Invalid amount format" in str(exc_info.value)
    
    def test_validate_status_valid(self):
        """Test valid status validation."""
        result = InputValidator.validate_status("paid")
        
        assert result.is_valid
        assert result.cleaned_value == "paid"
        assert len(result.errors) == 0
    
    def test_validate_status_case_insensitive(self):
        """Test status validation is case insensitive."""
        result = InputValidator.validate_status("PAID")
        
        assert result.is_valid
        assert result.cleaned_value == "paid"
    
    def test_validate_status_with_whitespace(self):
        """Test status validation with whitespace."""
        result = InputValidator.validate_status("  refunded  ")
        
        assert result.is_valid
        assert result.cleaned_value == "refunded"
    
    def test_validate_status_invalid(self):
        """Test status validation with invalid status."""
        with pytest.raises(InvalidStatusError) as exc_info:
            InputValidator.validate_status("invalid_status")
        
        assert "Invalid status: invalid_status" in str(exc_info.value)
    
    def test_validate_status_empty(self):
        """Test status validation with empty value."""
        result = InputValidator.validate_status("")
        
        assert not result.is_valid
        assert "Status is required" in result.errors[0]
    
    def test_validate_string_field_valid(self):
        """Test valid string field validation."""
        result = InputValidator.validate_string_field("test value", "Test Field")
        
        assert result.is_valid
        assert result.cleaned_value == "test value"
    
    def test_validate_string_field_required_missing(self):
        """Test string field validation with missing required value."""
        result = InputValidator.validate_string_field(None, "Test Field", required=True)
        
        assert not result.is_valid
        assert "Test Field is required" in result.errors[0]
    
    def test_validate_string_field_optional_missing(self):
        """Test string field validation with missing optional value."""
        result = InputValidator.validate_string_field(None, "Test Field", required=False)
        
        assert result.is_valid
        assert result.cleaned_value is None
    
    def test_validate_string_field_too_long(self):
        """Test string field validation with value too long."""
        long_value = "a" * 200
        result = InputValidator.validate_string_field(long_value, "Test Field", max_length=100)
        
        assert result.is_valid  # Still valid but truncated
        assert len(result.cleaned_value) == 100
        assert "exceeds maximum length" in result.warnings[0]
    
    def test_validate_string_field_too_short(self):
        """Test string field validation with value too short."""
        result = InputValidator.validate_string_field("ab", "Test Field", min_length=5)
        
        assert not result.is_valid
        assert "must be at least 5 characters" in result.errors[0]
    
    def test_validate_date_valid_formats(self):
        """Test date validation with various valid formats."""
        test_dates = [
            "2023-01-15",
            "2023-01-15 14:30:00",
            "2023/01/15",
            "15-01-2023",
            "01/15/2023",
            "2023-01-15T14:30:00"
        ]
        
        for date_str in test_dates:
            result = InputValidator.validate_date(date_str, "Test Date")
            assert result.is_valid, f"Failed to parse date: {date_str}"
            assert isinstance(result.cleaned_value, datetime)
    
    def test_validate_date_invalid_format(self):
        """Test date validation with invalid format."""
        result = InputValidator.validate_date("not_a_date", "Test Date")
        
        assert not result.is_valid
        assert "Unable to parse Test Date" in result.errors[0]
    
    def test_validate_date_required_missing(self):
        """Test date validation with missing required value."""
        result = InputValidator.validate_date(None, "Test Date", required=True)
        
        assert not result.is_valid
        assert "Test Date is required" in result.errors[0]
    
    def test_validate_date_optional_missing(self):
        """Test date validation with missing optional value."""
        result = InputValidator.validate_date(None, "Test Date", required=False)
        
        assert result.is_valid
        assert result.cleaned_value is None
    
    def test_validate_date_consistency_valid(self):
        """Test date consistency validation with valid dates."""
        created_at = datetime(2023, 1, 1, 10, 0, 0)
        updated_at = datetime(2023, 1, 2, 10, 0, 0)
        
        result = InputValidator.validate_date_consistency(created_at, updated_at)
        assert result.is_valid
    
    def test_validate_date_consistency_invalid(self):
        """Test date consistency validation with invalid dates."""
        created_at = datetime(2023, 1, 2, 10, 0, 0)
        updated_at = datetime(2023, 1, 1, 10, 0, 0)  # Before created_at
        
        with pytest.raises(DateConsistencyError):
            InputValidator.validate_date_consistency(created_at, updated_at)
    
    def test_validate_file_path_valid(self):
        """Test file path validation with valid path."""
        result = InputValidator.validate_file_path("test.csv", "csv")
        
        assert result.is_valid
        assert result.cleaned_value == "test.csv"
    
    def test_validate_file_path_wrong_format(self):
        """Test file path validation with wrong format."""
        with pytest.raises(FileFormatError):
            InputValidator.validate_file_path("test.txt", "csv")
    
    def test_validate_file_path_unsupported_format(self):
        """Test file path validation with unsupported format."""
        result = InputValidator.validate_file_path("test.xyz")
        
        assert not result.is_valid
        assert "Unsupported file format" in result.errors[0]
    
    def test_validate_batch_size_valid(self):
        """Test batch size validation with valid value."""
        result = InputValidator.validate_batch_size(1000)
        
        assert result.is_valid
        assert result.cleaned_value == 1000
    
    def test_validate_batch_size_default(self):
        """Test batch size validation with None (default)."""
        result = InputValidator.validate_batch_size(None)
        
        assert result.is_valid
        assert result.cleaned_value == 1000  # Default value
    
    def test_validate_batch_size_invalid(self):
        """Test batch size validation with invalid value."""
        result = InputValidator.validate_batch_size(-100)
        
        assert not result.is_valid
        assert "must be positive" in result.errors[0]
    
    def test_validate_batch_size_large(self):
        """Test batch size validation with large value."""
        result = InputValidator.validate_batch_size(200000)
        
        assert result.is_valid
        assert result.cleaned_value == 200000
        assert "Large batch size may cause memory issues" in result.warnings[0]
    
    def test_validate_transaction_record_valid(self):
        """Test complete transaction record validation with valid data."""
        record = {
            'id': 'test_id_123',
            'company_id': 'company_456',
            'name': 'Test Company',
            'amount': '123.45',
            'status': 'paid',
            'created_at': '2023-01-15 10:00:00',
            'updated_at': '2023-01-15 11:00:00'
        }
        
        result = InputValidator.validate_transaction_record(record)
        
        assert result.is_valid
        assert result.cleaned_value['id'] == 'test_id_123'
        assert result.cleaned_value['company_id'] == 'company_456'
        assert result.cleaned_value['company_name'] == 'Test Company'
        assert result.cleaned_value['amount'] == Decimal('123.45')
        assert result.cleaned_value['status'] == 'paid'
        assert isinstance(result.cleaned_value['created_at'], datetime)
        assert isinstance(result.cleaned_value['updated_at'], datetime)
    
    def test_validate_transaction_record_missing_required(self):
        """Test transaction record validation with missing required fields."""
        record = {
            'name': 'Test Company',
            'amount': '123.45',
            'status': 'paid'
        }
        
        result = InputValidator.validate_transaction_record(record)
        
        assert not result.is_valid
        assert any("ID is required" in error for error in result.errors)
        assert any("Company ID is required" in error for error in result.errors)
        assert any("Created At is required" in error for error in result.errors)
    
    def test_validate_transaction_record_invalid_data(self):
        """Test transaction record validation with invalid data."""
        record = {
            'id': 'test_id',
            'company_id': 'company_id',
            'amount': 'not_a_number',
            'status': 'invalid_status',
            'created_at': 'not_a_date'
        }
        
        result = InputValidator.validate_transaction_record(record)
        
        assert not result.is_valid
        assert any("Invalid amount format" in error for error in result.errors)
        assert any("Invalid status" in error for error in result.errors)
        assert any("Unable to parse Created At" in error for error in result.errors)


class TestAPIInputValidator:
    """Test API-specific input validation."""
    
    def test_validate_extract_number_input_valid(self):
        """Test valid extract number input validation."""
        result = APIInputValidator.validate_extract_number_input(50)
        assert result == 50
    
    def test_validate_extract_number_input_string(self):
        """Test extract number input validation with string."""
        result = APIInputValidator.validate_extract_number_input("75")
        assert result == 75
    
    def test_validate_extract_number_input_out_of_range(self):
        """Test extract number input validation with out of range value."""
        with pytest.raises(NumberOutOfRangeError):
            APIInputValidator.validate_extract_number_input(150)
    
    def test_validate_extract_number_input_invalid_type(self):
        """Test extract number input validation with invalid type."""
        with pytest.raises(NumberOutOfRangeError):
            APIInputValidator.validate_extract_number_input("not_a_number")
    
    def test_validate_pagination_params_valid(self):
        """Test valid pagination parameters."""
        limit, offset = APIInputValidator.validate_pagination_params(10, 20)
        assert limit == 10
        assert offset == 20
    
    def test_validate_pagination_params_none(self):
        """Test pagination parameters with None values."""
        limit, offset = APIInputValidator.validate_pagination_params(None, None)
        assert limit is None
        assert offset is None
    
    def test_validate_pagination_params_invalid_limit(self):
        """Test pagination parameters with invalid limit."""
        with pytest.raises(DataValidationError) as exc_info:
            APIInputValidator.validate_pagination_params(-10, 0)
        assert "positive integer" in str(exc_info.value)
    
    def test_validate_pagination_params_invalid_offset(self):
        """Test pagination parameters with invalid offset."""
        with pytest.raises(DataValidationError) as exc_info:
            APIInputValidator.validate_pagination_params(10, -5)
        assert "non-negative integer" in str(exc_info.value)
    
    def test_validate_pagination_params_large_limit(self):
        """Test pagination parameters with large limit."""
        limit, offset = APIInputValidator.validate_pagination_params(50000, 0)
        assert limit == 10000  # Capped at maximum
        assert offset == 0
    
    def test_validate_date_range_params_valid(self):
        """Test valid date range parameters."""
        start, end = APIInputValidator.validate_date_range_params("2023-01-01", "2023-01-31")
        assert start == "2023-01-01"
        assert end == "2023-01-31"
    
    def test_validate_date_range_params_none(self):
        """Test date range parameters with None values."""
        start, end = APIInputValidator.validate_date_range_params(None, None)
        assert start is None
        assert end is None
    
    def test_validate_date_range_params_invalid_order(self):
        """Test date range parameters with invalid order."""
        with pytest.raises(DataValidationError) as exc_info:
            APIInputValidator.validate_date_range_params("2023-01-31", "2023-01-01")
        assert "Start date cannot be after end date" in str(exc_info.value)
    
    def test_validate_date_range_params_invalid_format(self):
        """Test date range parameters with invalid format."""
        with pytest.raises(DataValidationError) as exc_info:
            APIInputValidator.validate_date_range_params("not_a_date", "2023-01-31")
        assert "Invalid start date" in str(exc_info.value)


class TestNumberSetErrorHandling:
    """Test NumberSet class error handling."""
    
    def test_number_set_init_invalid_max_number(self):
        """Test NumberSet initialization with invalid max_number."""
        with pytest.raises(ValueError) as exc_info:
            NumberSet(-10)
        assert "positive integer" in str(exc_info.value)
    
    def test_number_set_extract_invalid_type(self):
        """Test NumberSet extract with invalid type."""
        number_set = NumberSet()
        
        with pytest.raises(TypeError) as exc_info:
            number_set.extract("not_a_number")
        assert "must be an integer" in str(exc_info.value)
    
    def test_number_set_extract_out_of_range(self):
        """Test NumberSet extract with out of range number."""
        number_set = NumberSet()
        
        with pytest.raises(NumberOutOfRangeError) as exc_info:
            number_set.extract(150)
        assert exc_info.value.number == 150
    
    def test_number_set_extract_already_extracted(self):
        """Test NumberSet extract with already extracted number."""
        number_set = NumberSet()
        number_set.extract(50)  # Extract once
        
        with pytest.raises(NumberAlreadyExtractedError) as exc_info:
            number_set.extract(50)  # Try to extract again
        assert exc_info.value.number == 50
    
    def test_number_set_find_missing_no_extractions(self):
        """Test NumberSet find_missing_number with no extractions."""
        number_set = NumberSet()
        
        with pytest.raises(NoNumbersExtractedError):
            number_set.find_missing_number()
    
    def test_number_set_find_missing_multiple_extractions(self):
        """Test NumberSet find_missing_number with multiple extractions."""
        number_set = NumberSet()
        number_set.extract(25)
        number_set.extract(75)
        
        with pytest.raises(MultipleNumbersExtractedError) as exc_info:
            number_set.find_missing_number()
        assert exc_info.value.details["extracted_count"] == 2
    
    def test_number_set_successful_operations(self):
        """Test NumberSet successful operations."""
        number_set = NumberSet()
        
        # Successful extraction
        result = number_set.extract(42)
        assert result is True
        assert 42 in number_set.get_extracted_numbers()
        assert 42 not in number_set.get_current_set()
        
        # Successful missing number calculation
        missing = number_set.find_missing_number()
        assert missing == 42
        
        # Successful reset
        number_set.reset()
        assert len(number_set.get_extracted_numbers()) == 0
        assert len(number_set.get_current_set()) == 100


class TestValidationResult:
    """Test ValidationResult utility class."""
    
    def test_validation_result_init(self):
        """Test ValidationResult initialization."""
        result = ValidationResult()
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.cleaned_value is None
    
    def test_validation_result_add_error(self):
        """Test adding errors to ValidationResult."""
        result = ValidationResult()
        result.add_error("Test error")
        
        assert result.is_valid is False
        assert "Test error" in result.errors
    
    def test_validation_result_add_warning(self):
        """Test adding warnings to ValidationResult."""
        result = ValidationResult()
        result.add_warning("Test warning")
        
        assert result.is_valid is True  # Warnings don't affect validity
        assert "Test warning" in result.warnings
    
    def test_validation_result_set_cleaned_value(self):
        """Test setting cleaned value in ValidationResult."""
        result = ValidationResult()
        result.set_cleaned_value("cleaned_value")
        
        assert result.cleaned_value == "cleaned_value"