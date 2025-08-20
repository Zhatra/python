"""Unit tests for DataLoader class."""

import pytest
import pandas as pd
from decimal import Decimal
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from src.data_processing.loader import DataLoader, ValidationReport, LoadingReport
from src.database.models import RawTransaction


class TestDataLoader:
    """Test cases for DataLoader class."""
    
    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock context managers properly
        mock_session_context = MagicMock()
        mock_session_context.__enter__ = Mock(return_value=mock_session)
        mock_session_context.__exit__ = Mock(return_value=None)
        
        mock_conn.get_session.return_value = mock_session_context
        mock_conn.get_transaction.return_value = mock_session_context
        
        return mock_conn
    
    @pytest.fixture
    def data_loader(self, mock_db_connection):
        """DataLoader instance with mocked database connection."""
        return DataLoader(db_connection=mock_db_connection)
    
    @pytest.fixture
    def sample_csv_data(self):
        """Sample CSV data for testing."""
        return pd.DataFrame({
            'id': ['test_id_1', 'test_id_2', 'test_id_3'],
            'name': ['Company A', 'Company B', 'Company A'],
            'company_id': ['comp_1', 'comp_2', 'comp_1'],
            'amount': ['100.50', '200.75', '50.00'],
            'status': ['paid', 'pending_payment', 'voided'],
            'created_at': ['2019-01-01', '2019-01-02', '2019-01-03'],
            'paid_at': ['2019-01-01', '', '']
        })
    
    @pytest.fixture
    def invalid_csv_data(self):
        """Invalid CSV data for testing validation."""
        return pd.DataFrame({
            'id': ['', 'test_id_2', 'test_id_3'],  # Missing ID
            'name': ['Company A', 'Company B', 'A' * 150],  # Name too long
            'company_id': ['comp_1', '', 'comp_3'],  # Missing company_id
            'amount': ['100.50', 'invalid_amount', '-50.00'],  # Invalid amounts
            'status': ['paid', 'invalid_status', 'voided'],  # Invalid status
            'created_at': ['2019-01-01', 'invalid_date', '2019-01-03'],
            'paid_at': ['2019-01-01', '', '']
        })
    
    def test_init_with_default_connection(self):
        """Test DataLoader initialization with default connection."""
        with patch('src.database.connection.db_connection') as mock_global_conn:
            loader = DataLoader()
            assert loader.db_connection == mock_global_conn
    
    def test_init_with_custom_connection(self, mock_db_connection):
        """Test DataLoader initialization with custom connection."""
        loader = DataLoader(db_connection=mock_db_connection)
        assert loader.db_connection == mock_db_connection
    
    def test_read_csv_file_success(self, data_loader, tmp_path):
        """Test successful CSV file reading."""
        # Create temporary CSV file
        csv_file = tmp_path / "test.csv"
        csv_content = """id,name,company_id,amount,status,created_at,paid_at
test_id_1,Company A,comp_1,100.50,paid,2019-01-01,2019-01-01
test_id_2,Company B,comp_2,200.75,pending_payment,2019-01-02,"""
        csv_file.write_text(csv_content)
        
        df = data_loader._read_csv_file(str(csv_file))
        
        assert len(df) == 2
        assert list(df.columns) == DataLoader.EXPECTED_COLUMNS
        assert df.iloc[0]['id'] == 'test_id_1'
        assert df.iloc[1]['paid_at'] is None  # Empty string converted to None
    
    def test_read_csv_file_missing_columns(self, data_loader, tmp_path):
        """Test CSV file reading with missing columns."""
        csv_file = tmp_path / "test.csv"
        csv_content = """id,name,amount,status
test_id_1,Company A,100.50,paid"""
        csv_file.write_text(csv_content)
        
        with pytest.raises(ValueError, match="Missing required columns"):
            data_loader._read_csv_file(str(csv_file))
    
    def test_read_csv_file_not_found(self, data_loader):
        """Test CSV file reading with non-existent file."""
        with pytest.raises(FileNotFoundError):
            data_loader.load_csv_to_database("non_existent_file.csv")
    
    def test_read_csv_file_empty(self, data_loader, tmp_path):
        """Test CSV file reading with empty file."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        
        with pytest.raises(ValueError, match="CSV file is empty"):
            data_loader._read_csv_file(str(csv_file))
    
    def test_validate_data_integrity_valid_data(self, data_loader, sample_csv_data):
        """Test data validation with valid data."""
        report = data_loader.validate_data_integrity(sample_csv_data)
        
        assert isinstance(report, ValidationReport)
        assert report.total_rows == 3
        assert report.valid_rows == 3
        assert report.invalid_rows == 0
        assert len(report.errors) == 0
        assert report.success_rate == 100.0
    
    def test_validate_data_integrity_invalid_data(self, data_loader, invalid_csv_data):
        """Test data validation with invalid data."""
        report = data_loader.validate_data_integrity(invalid_csv_data)
        
        assert isinstance(report, ValidationReport)
        assert report.total_rows == 3
        assert report.invalid_rows > 0
        assert len(report.errors) > 0
        assert report.success_rate < 100.0
        
        # Check specific error types
        error_types = [error['type'] for error in report.errors]
        assert 'missing_required_field' in error_types
        assert 'field_too_long' in error_types
        assert 'invalid_amount_format' in error_types
        assert 'invalid_status' in error_types
    
    def test_validate_row_valid(self, data_loader):
        """Test single row validation with valid data."""
        valid_row = pd.Series({
            'id': 'test_id_1',
            'name': 'Company A',
            'company_id': 'comp_1',
            'amount': '100.50',
            'status': 'paid',
            'created_at': '2019-01-01',
            'paid_at': '2019-01-01'
        })
        
        errors = data_loader._validate_row(valid_row, 0)
        assert len(errors) == 0
    
    def test_validate_row_missing_id(self, data_loader):
        """Test single row validation with missing ID."""
        invalid_row = pd.Series({
            'id': '',
            'name': 'Company A',
            'company_id': 'comp_1',
            'amount': '100.50',
            'status': 'paid',
            'created_at': '2019-01-01',
            'paid_at': '2019-01-01'
        })
        
        errors = data_loader._validate_row(invalid_row, 0)
        assert len(errors) == 1
        assert errors[0]['type'] == 'missing_required_field'
        assert errors[0]['field'] == 'id'
    
    def test_validate_row_invalid_amount(self, data_loader):
        """Test single row validation with invalid amount."""
        invalid_row = pd.Series({
            'id': 'test_id_1',
            'name': 'Company A',
            'company_id': 'comp_1',
            'amount': 'not_a_number',
            'status': 'paid',
            'created_at': '2019-01-01',
            'paid_at': '2019-01-01'
        })
        
        errors = data_loader._validate_row(invalid_row, 0)
        assert len(errors) == 1
        assert errors[0]['type'] == 'invalid_amount_format'
        assert errors[0]['field'] == 'amount'
    
    def test_validate_row_negative_amount(self, data_loader):
        """Test single row validation with negative amount."""
        invalid_row = pd.Series({
            'id': 'test_id_1',
            'name': 'Company A',
            'company_id': 'comp_1',
            'amount': '-100.50',
            'status': 'paid',
            'created_at': '2019-01-01',
            'paid_at': '2019-01-01'
        })
        
        errors = data_loader._validate_row(invalid_row, 0)
        assert len(errors) == 1
        assert errors[0]['type'] == 'invalid_amount'
        assert errors[0]['field'] == 'amount'
    
    def test_validate_row_invalid_status(self, data_loader):
        """Test single row validation with invalid status."""
        invalid_row = pd.Series({
            'id': 'test_id_1',
            'name': 'Company A',
            'company_id': 'comp_1',
            'amount': '100.50',
            'status': 'invalid_status',
            'created_at': '2019-01-01',
            'paid_at': '2019-01-01'
        })
        
        errors = data_loader._validate_row(invalid_row, 0)
        assert len(errors) == 1
        assert errors[0]['type'] == 'invalid_status'
        assert errors[0]['field'] == 'status'
    
    def test_validate_row_field_too_long(self, data_loader):
        """Test single row validation with field too long."""
        invalid_row = pd.Series({
            'id': 'test_id_1',
            'name': 'A' * 150,  # Exceeds max length of 130
            'company_id': 'comp_1',
            'amount': '100.50',
            'status': 'paid',
            'created_at': '2019-01-01',
            'paid_at': '2019-01-01'
        })
        
        errors = data_loader._validate_row(invalid_row, 0)
        assert len(errors) == 1
        assert errors[0]['type'] == 'field_too_long'
        assert errors[0]['field'] == 'name'
    
    def test_is_valid_date_format(self, data_loader):
        """Test date format validation."""
        assert data_loader._is_valid_date_format('2019-01-01') is True
        assert data_loader._is_valid_date_format('2019-12-31') is True
        assert data_loader._is_valid_date_format('') is True  # Empty is valid
        assert data_loader._is_valid_date_format(None) is True  # None is valid
        assert data_loader._is_valid_date_format('invalid_date') is False
        assert data_loader._is_valid_date_format('2019-13-01') is False  # Invalid month
    
    def test_row_to_raw_transaction_success(self, data_loader):
        """Test successful conversion of row to RawTransaction."""
        row = pd.Series({
            'id': 'test_id_1',
            'name': 'Company A',
            'company_id': 'comp_1',
            'amount': '100.50',
            'status': 'paid',
            'created_at': '2019-01-01',
            'paid_at': '2019-01-01'
        })
        
        transaction = data_loader._row_to_raw_transaction(row)
        
        assert isinstance(transaction, RawTransaction)
        assert transaction.id == 'test_id_1'
        assert transaction.name == 'Company A'
        assert transaction.company_id == 'comp_1'
        assert transaction.amount == Decimal('100.50')
        assert transaction.status == 'paid'
        assert transaction.created_at == '2019-01-01'
        assert transaction.paid_at == '2019-01-01'
    
    def test_row_to_raw_transaction_with_nulls(self, data_loader):
        """Test conversion of row with null values to RawTransaction."""
        row = pd.Series({
            'id': 'test_id_1',
            'name': None,
            'company_id': 'comp_1',
            'amount': None,
            'status': 'paid',
            'created_at': '2019-01-01',
            'paid_at': None
        })
        
        transaction = data_loader._row_to_raw_transaction(row)
        
        assert transaction.id == 'test_id_1'
        assert transaction.name is None
        assert transaction.amount is None
        assert transaction.paid_at is None
    
    def test_row_to_raw_transaction_invalid_amount(self, data_loader):
        """Test conversion with invalid amount raises error."""
        row = pd.Series({
            'id': 'test_id_1',
            'name': 'Company A',
            'company_id': 'comp_1',
            'amount': 'invalid_amount',
            'status': 'paid',
            'created_at': '2019-01-01',
            'paid_at': '2019-01-01'
        })
        
        with pytest.raises(ValueError, match="Failed to convert row to RawTransaction"):
            data_loader._row_to_raw_transaction(row)
    
    @patch('src.data_processing.loader.Path')
    def test_load_csv_to_database_success(self, mock_path, data_loader, sample_csv_data):
        """Test successful CSV loading to database."""
        # Mock file existence
        mock_path.return_value.exists.return_value = True
        
        # Mock CSV reading
        with patch.object(data_loader, '_read_csv_file', return_value=sample_csv_data):
            with patch.object(data_loader, '_load_dataframe_to_database', return_value=(3, [])):
                report = data_loader.load_csv_to_database('test.csv')
        
        assert isinstance(report, LoadingReport)
        assert report.total_rows_processed == 3
        assert report.rows_loaded == 3
        assert report.rows_skipped == 0
        assert report.loading_success_rate == 100.0
    
    def test_load_dataframe_to_database_success(self, data_loader, sample_csv_data):
        """Test successful DataFrame loading to database."""
        mock_session = Mock()
        data_loader.db_connection.get_transaction.return_value.__enter__.return_value = mock_session
        
        with patch.object(data_loader, '_load_batch_to_database', return_value=(3, [])):
            rows_loaded, errors = data_loader._load_dataframe_to_database(sample_csv_data, 1000)
        
        assert rows_loaded == 3
        assert len(errors) == 0
    
    def test_load_dataframe_to_database_with_errors(self, data_loader, sample_csv_data):
        """Test DataFrame loading with database errors."""
        mock_session = Mock()
        data_loader.db_connection.get_transaction.return_value.__enter__.return_value = mock_session
        
        # Mock database error
        data_loader.db_connection.get_transaction.return_value.__enter__.side_effect = SQLAlchemyError("DB Error")
        
        rows_loaded, errors = data_loader._load_dataframe_to_database(sample_csv_data, 1000)
        
        assert rows_loaded == 0
        assert len(errors) == 1
        assert errors[0]['type'] == 'database_error'
    
    def test_load_batch_to_database_success(self, data_loader, sample_csv_data):
        """Test successful batch loading to database."""
        mock_session = Mock()
        
        with patch.object(data_loader, '_row_to_raw_transaction') as mock_convert:
            mock_convert.return_value = Mock(spec=RawTransaction)
            
            rows_loaded, errors = data_loader._load_batch_to_database(
                mock_session, sample_csv_data, 0
            )
        
        assert rows_loaded == 3
        assert len(errors) == 0
        assert mock_session.add.call_count == 3
        assert mock_session.flush.called
    
    def test_load_batch_to_database_with_flush_error(self, data_loader, sample_csv_data):
        """Test batch loading with flush error."""
        mock_session = Mock()
        mock_session.flush.side_effect = SQLAlchemyError("Flush error")
        
        with patch.object(data_loader, '_load_rows_individually', return_value=(2, [{'error': 'test'}])):
            rows_loaded, errors = data_loader._load_batch_to_database(
                mock_session, sample_csv_data, 0
            )
        
        assert rows_loaded == 2
        assert len(errors) == 1
        assert mock_session.rollback.called
    
    def test_load_rows_individually_success(self, data_loader, sample_csv_data):
        """Test individual row loading success."""
        mock_session = Mock()
        
        with patch.object(data_loader, '_row_to_raw_transaction') as mock_convert:
            mock_convert.return_value = Mock(spec=RawTransaction)
            
            rows_loaded, errors = data_loader._load_rows_individually(
                mock_session, sample_csv_data, 0
            )
        
        assert rows_loaded == 3
        assert len(errors) == 0
        assert mock_session.add.call_count == 3
        assert mock_session.flush.call_count == 3
    
    def test_load_rows_individually_with_errors(self, data_loader, sample_csv_data):
        """Test individual row loading with errors."""
        mock_session = Mock()
        mock_session.flush.side_effect = SQLAlchemyError("Individual row error")
        
        with patch.object(data_loader, '_row_to_raw_transaction') as mock_convert:
            mock_convert.return_value = Mock(spec=RawTransaction)
            
            rows_loaded, errors = data_loader._load_rows_individually(
                mock_session, sample_csv_data, 0
            )
        
        assert rows_loaded == 0
        assert len(errors) == 3  # One error per row
        assert all(error['type'] == 'individual_row_error' for error in errors)
    
    def test_get_loading_statistics_success(self, data_loader):
        """Test getting loading statistics successfully."""
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.count.return_value = 100
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        
        data_loader.db_connection.get_session.return_value.__enter__.return_value = mock_session
        
        stats = data_loader.get_loading_statistics()
        
        assert 'total_rows' in stats
        assert 'status_distribution' in stats
        assert 'rows_with_amount' in stats
        assert 'unique_companies' in stats
        assert stats['total_rows'] == 100
    
    def test_get_loading_statistics_with_error(self, data_loader):
        """Test getting loading statistics with database error."""
        data_loader.db_connection.get_session.return_value.__enter__.side_effect = SQLAlchemyError("DB Error")
        
        stats = data_loader.get_loading_statistics()
        
        assert 'error' in stats
        assert 'DB Error' in stats['error']


class TestValidationReport:
    """Test cases for ValidationReport class."""
    
    def test_validation_report_creation(self):
        """Test ValidationReport creation and properties."""
        report = ValidationReport(
            total_rows=100,
            valid_rows=90,
            invalid_rows=10,
            errors=[],
            warnings=[],
            duplicates=5
        )
        
        assert report.total_rows == 100
        assert report.valid_rows == 90
        assert report.invalid_rows == 10
        assert report.duplicates == 5
        assert report.success_rate == 90.0
    
    def test_validation_report_zero_rows(self):
        """Test ValidationReport with zero rows."""
        report = ValidationReport(
            total_rows=0,
            valid_rows=0,
            invalid_rows=0,
            errors=[],
            warnings=[],
            duplicates=0
        )
        
        assert report.success_rate == 0.0
    
    def test_validation_report_str(self):
        """Test ValidationReport string representation."""
        report = ValidationReport(
            total_rows=100,
            valid_rows=90,
            invalid_rows=10,
            errors=[],
            warnings=[],
            duplicates=5
        )
        
        str_repr = str(report)
        assert 'total=100' in str_repr
        assert 'valid=90' in str_repr
        assert 'invalid=10' in str_repr
        assert 'success_rate=90.00%' in str_repr


class TestLoadingReport:
    """Test cases for LoadingReport class."""
    
    def test_loading_report_creation(self):
        """Test LoadingReport creation and properties."""
        validation_report = ValidationReport(
            total_rows=100, valid_rows=90, invalid_rows=10,
            errors=[], warnings=[], duplicates=0
        )
        
        report = LoadingReport(
            file_path='/path/to/test.csv',
            total_rows_processed=100,
            rows_loaded=85,
            rows_skipped=15,
            validation_report=validation_report,
            loading_errors=[],
            execution_time_seconds=5.5
        )
        
        assert report.file_path == '/path/to/test.csv'
        assert report.total_rows_processed == 100
        assert report.rows_loaded == 85
        assert report.rows_skipped == 15
        assert report.loading_success_rate == 85.0
        assert report.execution_time_seconds == 5.5
    
    def test_loading_report_zero_processed(self):
        """Test LoadingReport with zero processed rows."""
        validation_report = ValidationReport(
            total_rows=0, valid_rows=0, invalid_rows=0,
            errors=[], warnings=[], duplicates=0
        )
        
        report = LoadingReport(
            file_path='/path/to/empty.csv',
            total_rows_processed=0,
            rows_loaded=0,
            rows_skipped=0,
            validation_report=validation_report,
            loading_errors=[],
            execution_time_seconds=0.1
        )
        
        assert report.loading_success_rate == 0.0
    
    def test_loading_report_str(self):
        """Test LoadingReport string representation."""
        validation_report = ValidationReport(
            total_rows=100, valid_rows=90, invalid_rows=10,
            errors=[], warnings=[], duplicates=0
        )
        
        report = LoadingReport(
            file_path='/path/to/test.csv',
            total_rows_processed=100,
            rows_loaded=85,
            rows_skipped=15,
            validation_report=validation_report,
            loading_errors=[],
            execution_time_seconds=5.5
        )
        
        str_repr = str(report)
        assert 'file=test.csv' in str_repr
        assert 'processed=100' in str_repr
        assert 'loaded=85' in str_repr
        assert 'loading_success_rate=85.00%' in str_repr