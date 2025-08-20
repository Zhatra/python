"""Unit tests for DataTransformer class."""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from src.data_processing.transformer import (
    DataTransformer, TransformationReport, ValidationResult
)
from src.database.models import RawTransaction, Company, Charge


class TestDataTransformer:
    """Test cases for DataTransformer class."""
    
    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock context managers properly
        mock_session_context = Mock()
        mock_session_context.__enter__ = Mock(return_value=mock_session)
        mock_session_context.__exit__ = Mock(return_value=None)
        
        mock_conn.get_session.return_value = mock_session_context
        mock_conn.get_transaction.return_value = mock_session_context
        
        return mock_conn
    
    @pytest.fixture
    def transformer(self, mock_db_connection):
        """Create DataTransformer instance with mocked connection."""
        return DataTransformer(db_connection=mock_db_connection)
    
    @pytest.fixture
    def sample_raw_data(self):
        """Sample raw transaction data."""
        return [
            RawTransaction(
                id="48ba4bdbfb56ceebb32f2bd0263e759be942af3d",
                name="MiPasajefy",
                company_id="cbf1c8b09cd5b549416d49d220a40cbd317f952e",
                amount=Decimal("3.0"),
                status="voided",
                created_at="2019-03-19",
                paid_at=None
            ),
            RawTransaction(
                id="81633ba310a50b673efd469c37139576982901aa",
                name="MiPasajefy",
                company_id="cbf1c8b09cd5b549416d49d220a40cbd317f952e",
                amount=Decimal("102.61"),
                status="paid",
                created_at="2019-02-27",
                paid_at="2019-02-27"
            ),
            RawTransaction(
                id="496d2511ac4e58e78d6540142590c54e507af7d9",
                name="Muebles chidos",
                company_id="8f642dc67fccf861548dfe1c761ce22f795e91f0",
                amount=Decimal("5599.0"),
                status="pending_payment",
                created_at="2019-02-19",
                paid_at=None
            )
        ]
    
    def test_init_with_connection(self, mock_db_connection):
        """Test DataTransformer initialization with connection."""
        transformer = DataTransformer(db_connection=mock_db_connection)
        assert transformer.db_connection == mock_db_connection
    
    def test_init_without_connection(self):
        """Test DataTransformer initialization without connection."""
        with patch('src.database.connection.db_connection') as mock_global_connection:
            transformer = DataTransformer()
            assert transformer.db_connection == mock_global_connection
    
    def test_raw_data_to_dataframe(self, transformer, sample_raw_data):
        """Test conversion of raw data to DataFrame."""
        df = transformer._raw_data_to_dataframe(sample_raw_data)
        
        assert len(df) == 3
        assert list(df.columns) == ['id', 'name', 'company_id', 'amount', 'status', 'created_at', 'paid_at']
        assert df.iloc[0]['name'] == "MiPasajefy"
        assert df.iloc[1]['amount'] == Decimal("102.61")
        assert df.iloc[2]['status'] == "pending_payment"
    
    def test_parse_and_validate_date_valid_formats(self, transformer):
        """Test date parsing with various valid formats."""
        test_cases = [
            ("2019-03-19", datetime(2019, 3, 19)),
            ("2019-03-19 14:30:00", datetime(2019, 3, 19, 14, 30, 0)),
            ("2019/03/19", datetime(2019, 3, 19)),
            ("19-03-2019", datetime(2019, 3, 19)),
        ]
        
        for date_str, expected in test_cases:
            result = transformer._parse_and_validate_date(date_str, 'created_at')
            assert result.is_valid
            assert result.cleaned_value.date() == expected.date()
    
    def test_parse_and_validate_date_invalid_formats(self, transformer):
        """Test date parsing with invalid formats."""
        invalid_dates = ["invalid-date", "2019-13-45", "", None]
        
        for date_str in invalid_dates:
            result = transformer._parse_and_validate_date(date_str, 'created_at')
            if date_str in ["", None]:
                # Empty dates should fail for required fields
                assert not result.is_valid
                assert "is required" in result.errors[0]
            else:
                assert not result.is_valid
                assert "Unable to parse" in result.errors[0]
    
    def test_parse_and_validate_date_optional_field(self, transformer):
        """Test date parsing for optional fields."""
        result = transformer._parse_and_validate_date(None, 'paid_at')
        assert result.is_valid  # Optional field can be None
        assert result.cleaned_value is None
    
    def test_validate_row_for_transformation_valid_row(self, transformer):
        """Test row validation with valid data."""
        row = pd.Series({
            'id': '48ba4bdbfb56ceebb32f2bd0263e759be942af3d',
            'name': 'MiPasajefy',
            'company_id': 'cbf1c8b09cd5b549416d49d220a40cbd317f952e',
            'amount': Decimal('3.0'),
            'status': 'voided',
            'created_at': '2019-03-19',
            'paid_at': None
        })
        
        result = transformer._validate_row_for_transformation(row, 0)
        
        assert result.is_valid
        assert result.cleaned_value is not None
        assert result.cleaned_value['id'] == '48ba4bdbfb56ceebb32f2bd0'  # Truncated to 24 chars
        assert result.cleaned_value['status'] == 'voided'
        assert isinstance(result.cleaned_value['created_at'], datetime)
    
    def test_validate_row_for_transformation_missing_required_fields(self, transformer):
        """Test row validation with missing required fields."""
        row = pd.Series({
            'id': None,
            'name': 'MiPasajefy',
            'company_id': None,
            'amount': None,
            'status': 'voided',
            'created_at': '2019-03-19',
            'paid_at': None
        })
        
        result = transformer._validate_row_for_transformation(row, 0)
        
        assert not result.is_valid
        assert "ID is required" in result.errors
        assert "Company ID is required" in result.errors
        assert "Amount is required" in result.errors
    
    def test_validate_row_for_transformation_invalid_status(self, transformer):
        """Test row validation with invalid status."""
        row = pd.Series({
            'id': '48ba4bdbfb56ceebb32f2bd0263e759be942af3d',
            'name': 'MiPasajefy',
            'company_id': 'cbf1c8b09cd5b549416d49d220a40cbd317f952e',
            'amount': Decimal('3.0'),
            'status': 'invalid_status',
            'created_at': '2019-03-19',
            'paid_at': None
        })
        
        result = transformer._validate_row_for_transformation(row, 0)
        
        assert not result.is_valid
        assert any("Invalid status" in error for error in result.errors)
    
    def test_validate_row_for_transformation_negative_amount(self, transformer):
        """Test row validation with negative amount."""
        row = pd.Series({
            'id': '48ba4bdbfb56ceebb32f2bd0263e759be942af3d',
            'name': 'MiPasajefy',
            'company_id': 'cbf1c8b09cd5b549416d49d220a40cbd317f952e',
            'amount': Decimal('-3.0'),
            'status': 'voided',
            'created_at': '2019-03-19',
            'paid_at': None
        })
        
        result = transformer._validate_row_for_transformation(row, 0)
        
        assert not result.is_valid
        assert "Amount cannot be negative" in result.errors
    
    def test_validate_row_for_transformation_field_truncation(self, transformer):
        """Test row validation with field truncation."""
        long_id = 'a' * 50  # Longer than 24 chars
        long_company_id = 'b' * 50  # Longer than 24 chars
        long_name = 'c' * 200  # Longer than 130 chars
        
        row = pd.Series({
            'id': long_id,
            'name': long_name,
            'company_id': long_company_id,
            'amount': Decimal('3.0'),
            'status': 'voided',
            'created_at': '2019-03-19',
            'paid_at': None
        })
        
        result = transformer._validate_row_for_transformation(row, 0)
        
        assert result.is_valid
        assert len(result.cleaned_value['id']) == 24
        assert len(result.cleaned_value['company_id']) == 24
        assert len(result.cleaned_value['name']) == 130
        assert len(result.warnings) >= 3  # Should have truncation warnings
    
    def test_standardize_company_name(self, transformer):
        """Test company name standardization."""
        test_cases = [
            ("mipasajefy", "Mipasajefy"),
            ("MUEBLES CHIDOS", "Muebles Chidos"),
            ("  extra   spaces  ", "Extra Spaces"),
            ("", "Unknown Company"),
            (None, "Unknown Company")
        ]
        
        for input_name, expected in test_cases:
            result = transformer._standardize_company_name(input_name)
            assert result == expected
    
    def test_extract_companies(self, transformer):
        """Test company extraction from transaction data."""
        df = pd.DataFrame([
            {
                'company_id': 'comp1',
                'name': 'Company 1',
                'id': 'tx1',
                'amount': 100,
                'status': 'paid'
            },
            {
                'company_id': 'comp1',
                'name': 'Company 1',
                'id': 'tx2',
                'amount': 200,
                'status': 'paid'
            },
            {
                'company_id': 'comp2',
                'name': 'Company 2',
                'id': 'tx3',
                'amount': 300,
                'status': 'pending_payment'
            }
        ])
        
        companies_df = transformer._extract_companies(df)
        
        assert len(companies_df) == 2
        assert 'company_name' in companies_df.columns
        assert 'created_at' in companies_df.columns
        assert companies_df['company_id'].tolist() == ['comp1', 'comp2']
    
    def test_transform_charges(self, transformer):
        """Test charge transformation."""
        df = pd.DataFrame([
            {
                'id': 'tx1',
                'company_id': 'comp1',
                'amount': Decimal('100.00'),
                'status': 'paid',
                'created_at': datetime(2019, 1, 1),
                'updated_at': datetime(2019, 1, 2)
            },
            {
                'id': 'tx2',
                'company_id': 'comp2',
                'amount': Decimal('200.00'),
                'status': 'pending_payment',
                'created_at': datetime(2019, 1, 3),
                'updated_at': None
            }
        ])
        
        charges_df = transformer._transform_charges(df)
        
        assert len(charges_df) == 2
        expected_columns = ['id', 'company_id', 'amount', 'status', 'created_at', 'updated_at']
        assert all(col in charges_df.columns for col in expected_columns)
    
    def test_apply_business_rules_remove_duplicates(self, transformer):
        """Test business rule for removing duplicates."""
        df = pd.DataFrame([
            {
                'id': 'tx1',
                'company_id': 'comp1',
                'name': 'Company 1',
                'amount': Decimal('100.00'),
                'status': 'paid',
                'created_at': datetime(2019, 1, 1),
                'paid_at': datetime(2019, 1, 1),
                'updated_at': None
            },
            {
                'id': 'tx1',  # Duplicate ID
                'company_id': 'comp1',
                'name': 'Company 1',
                'amount': Decimal('150.00'),
                'status': 'paid',
                'created_at': datetime(2019, 1, 2),
                'paid_at': datetime(2019, 1, 2),
                'updated_at': None
            },
            {
                'id': 'tx2',
                'company_id': 'comp2',
                'name': 'Company 2',
                'amount': Decimal('200.00'),
                'status': 'pending_payment',
                'created_at': datetime(2019, 1, 3),
                'paid_at': None,
                'updated_at': None
            }
        ])
        
        cleaned_df, issues = transformer._apply_business_rules(df)
        
        assert len(cleaned_df) == 2  # One duplicate removed
        assert any(issue['type'] == 'duplicates_removed' for issue in issues)
        assert cleaned_df['id'].tolist() == ['tx1', 'tx2']
    
    def test_apply_business_rules_small_amounts(self, transformer):
        """Test business rule for adjusting small amounts."""
        df = pd.DataFrame([
            {
                'id': 'tx1',
                'company_id': 'comp1',
                'name': 'Company 1',
                'amount': Decimal('0.005'),  # Very small amount
                'status': 'paid',
                'created_at': datetime(2019, 1, 1),
                'paid_at': datetime(2019, 1, 1),
                'updated_at': None
            },
            {
                'id': 'tx2',
                'company_id': 'comp2',
                'name': 'Company 2',
                'amount': Decimal('100.00'),
                'status': 'paid',
                'created_at': datetime(2019, 1, 2),
                'paid_at': datetime(2019, 1, 2),
                'updated_at': None
            }
        ])
        
        cleaned_df, issues = transformer._apply_business_rules(df)
        
        assert cleaned_df.iloc[0]['amount'] == Decimal('0.01')  # Adjusted
        assert cleaned_df.iloc[1]['amount'] == Decimal('100.00')  # Unchanged
        assert any(issue['type'] == 'small_amounts_adjusted' for issue in issues)
    
    def test_validate_date_consistency(self, transformer):
        """Test date consistency validation."""
        df = pd.DataFrame([
            {
                'status': 'paid',
                'created_at': datetime(2019, 1, 2),
                'paid_at': datetime(2019, 1, 1)  # paid_at before created_at
            },
            {
                'status': 'paid',
                'created_at': datetime(2019, 1, 1),
                'paid_at': datetime(2019, 1, 2)  # Correct order
            },
            {
                'status': 'pending_payment',
                'created_at': datetime(2019, 1, 1),
                'paid_at': None  # No paid_at for pending
            }
        ])
        
        issues = transformer._validate_date_consistency(df)
        
        assert len(issues) == 1
        assert issues[0]['type'] == 'date_consistency_error'
        assert issues[0]['count'] == 1
    
    def test_load_companies_new_companies(self, transformer, mock_db_connection):
        """Test loading new companies."""
        mock_session = mock_db_connection.get_transaction.return_value.__enter__.return_value
        mock_session.query.return_value.filter.return_value.first.return_value = None  # No existing companies
        
        companies_df = pd.DataFrame([
            {
                'company_id': 'comp1',
                'company_name': 'Company 1',
                'created_at': datetime.now(),
                'updated_at': None
            },
            {
                'company_id': 'comp2',
                'company_name': 'Company 2',
                'created_at': datetime.now(),
                'updated_at': None
            }
        ])
        
        count = transformer._load_companies(mock_session, companies_df)
        
        assert count == 2
        assert mock_session.add.call_count == 2
        mock_session.flush.assert_called_once()
    
    def test_load_companies_existing_companies(self, transformer, mock_db_connection):
        """Test loading companies when they already exist."""
        mock_session = mock_db_connection.get_transaction.return_value.__enter__.return_value
        mock_session.query.return_value.filter.return_value.first.return_value = Mock()  # Existing company
        
        companies_df = pd.DataFrame([
            {
                'company_id': 'comp1',
                'company_name': 'Company 1',
                'created_at': datetime.now(),
                'updated_at': None
            }
        ])
        
        count = transformer._load_companies(mock_session, companies_df)
        
        assert count == 0  # No new companies created
        mock_session.add.assert_not_called()
    
    def test_load_charges_new_charges(self, transformer, mock_db_connection):
        """Test loading new charges."""
        mock_session = mock_db_connection.get_transaction.return_value.__enter__.return_value
        mock_session.query.return_value.filter.return_value.first.return_value = None  # No existing charges
        
        charges_df = pd.DataFrame([
            {
                'id': 'tx1',
                'company_id': 'comp1',
                'amount': Decimal('100.00'),
                'status': 'paid',
                'created_at': datetime.now(),
                'updated_at': None
            }
        ])
        
        count = transformer._load_charges(mock_session, charges_df)
        
        assert count == 1
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
    
    def test_transform_to_schema_empty_data(self, transformer, mock_db_connection):
        """Test transformation with empty raw data."""
        mock_session = mock_db_connection.get_transaction.return_value.__enter__.return_value
        mock_session.query.return_value.all.return_value = []  # No raw data
        
        report = transformer.transform_to_schema()
        
        assert report.total_raw_rows == 0
        assert report.transformed_rows == 0
        assert report.companies_created == 0
        assert report.charges_created == 0
    
    @patch('time.time')
    def test_transform_to_schema_success(self, mock_time, transformer, mock_db_connection, sample_raw_data):
        """Test successful transformation."""
        mock_time.side_effect = [1000, 1010]  # Start and end times
        
        mock_session = mock_db_connection.get_transaction.return_value.__enter__.return_value
        mock_session.query.return_value.all.return_value = sample_raw_data
        
        # Mock existing company/charge queries to return None (no existing records)
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        report = transformer.transform_to_schema()
        
        assert report.total_raw_rows == 3
        assert report.transformed_rows > 0
        assert report.execution_time_seconds == 10
        assert report.transformation_success_rate > 0
    
    def test_validation_result_add_error(self):
        """Test ValidationResult error handling."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        result.add_error("Test error")
        
        assert not result.is_valid
        assert "Test error" in result.errors
    
    def test_validation_result_add_warning(self):
        """Test ValidationResult warning handling."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        result.add_warning("Test warning")
        
        assert result.is_valid  # Warnings don't affect validity
        assert "Test warning" in result.warnings
    
    def test_transformation_report_success_rate(self):
        """Test TransformationReport success rate calculation."""
        report = TransformationReport(
            total_raw_rows=100,
            transformed_rows=95,
            skipped_rows=5,
            companies_created=10,
            charges_created=95,
            transformation_errors=[],
            data_quality_issues=[],
            execution_time_seconds=10.0
        )
        
        assert report.transformation_success_rate == 95.0
    
    def test_transformation_report_success_rate_zero_rows(self):
        """Test TransformationReport success rate with zero rows."""
        report = TransformationReport(
            total_raw_rows=0,
            transformed_rows=0,
            skipped_rows=0,
            companies_created=0,
            charges_created=0,
            transformation_errors=[],
            data_quality_issues=[],
            execution_time_seconds=0.0
        )
        
        assert report.transformation_success_rate == 100.0
    
    def test_transformation_report_str(self):
        """Test TransformationReport string representation."""
        report = TransformationReport(
            total_raw_rows=100,
            transformed_rows=95,
            skipped_rows=5,
            companies_created=10,
            charges_created=95,
            transformation_errors=[],
            data_quality_issues=[],
            execution_time_seconds=10.0
        )
        
        str_repr = str(report)
        assert "total=100" in str_repr
        assert "transformed=95" in str_repr
        assert "companies=10" in str_repr
        assert "charges=95" in str_repr
        assert "success_rate=95.00%" in str_repr


class TestDataTransformerEdgeCases:
    """Test edge cases and error scenarios for DataTransformer."""
    
    @pytest.fixture
    def transformer(self):
        """Create DataTransformer instance with mocked connection."""
        mock_conn = Mock()
        return DataTransformer(db_connection=mock_conn)
    
    def test_parse_date_with_pandas_fallback(self, transformer):
        """Test date parsing with pandas fallback."""
        # Use a date format that's not in our standard patterns but pandas can parse
        with patch('pandas.to_datetime') as mock_pd_datetime:
            mock_pd_datetime.return_value.to_pydatetime.return_value = datetime(2019, 3, 19)
            
            result = transformer._parse_and_validate_date("Mar 19, 2019", 'created_at')
            
            assert result.is_valid
            assert len(result.warnings) == 1
            assert "parsed with fallback method" in result.warnings[0]
    
    def test_standardize_company_name_edge_cases(self, transformer):
        """Test company name standardization with edge cases."""
        test_cases = [
            ("   ", "Unknown Company"),  # Only whitespace
            ("a" * 200, ("a" * 200).title()),  # Very long name (should be truncated elsewhere)
            ("multiple   spaces   here", "Multiple Spaces Here"),
            ("123 numeric company", "123 Numeric Company")
        ]
        
        for input_name, expected in test_cases:
            result = transformer._standardize_company_name(input_name)
            assert result == expected
    
    def test_validate_row_invalid_amount_format(self, transformer):
        """Test row validation with invalid amount format."""
        row = pd.Series({
            'id': 'test_id',
            'name': 'Test Company',
            'company_id': 'test_company',
            'amount': 'invalid_amount',
            'status': 'paid',
            'created_at': '2019-03-19',
            'paid_at': None
        })
        
        result = transformer._validate_row_for_transformation(row, 0)
        
        assert not result.is_valid
        assert any("Invalid amount format" in error for error in result.errors)
    
    def test_apply_business_rules_updated_at_for_paid(self, transformer):
        """Test business rule for setting updated_at for paid transactions."""
        df = pd.DataFrame([
            {
                'id': 'tx1',
                'company_id': 'comp1',
                'name': 'Company 1',
                'amount': Decimal('100.00'),
                'status': 'paid',
                'created_at': datetime(2019, 1, 1),
                'paid_at': datetime(2019, 1, 2),
                'updated_at': None
            },
            {
                'id': 'tx2',
                'company_id': 'comp2',
                'name': 'Company 2',
                'amount': Decimal('200.00'),
                'status': 'pending_payment',
                'created_at': datetime(2019, 1, 3),
                'paid_at': None,
                'updated_at': None
            }
        ])
        
        cleaned_df, issues = transformer._apply_business_rules(df)
        
        # Paid transaction should have updated_at set to paid_at
        assert cleaned_df.iloc[0]['updated_at'] == datetime(2019, 1, 2)
        # Pending transaction should still have None updated_at
        assert pd.isna(cleaned_df.iloc[1]['updated_at'])