"""Integration tests for DataLoader with real CSV data."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

from src.data_processing.loader import DataLoader


class TestDataLoaderIntegration:
    """Integration tests for DataLoader."""
    
    @pytest.fixture
    def sample_csv_content(self):
        """Sample CSV content for testing."""
        return """id,name,company_id,amount,status,created_at,paid_at
test_id_1,MiPasajefy,cbf1c8b09cd5b549416d49d220a40cbd317f952e,100.50,paid,2019-01-01,2019-01-01
test_id_2,MiPasajefy,cbf1c8b09cd5b549416d49d220a40cbd317f952e,200.75,pending_payment,2019-01-02,
test_id_3,Muebles chidos,8f642dc67fccf861548dfe1c761ce22f795e91f0,50.00,voided,2019-01-03,"""
    
    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection for integration tests."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock context managers properly
        mock_session_context = MagicMock()
        mock_session_context.__enter__ = Mock(return_value=mock_session)
        mock_session_context.__exit__ = Mock(return_value=None)
        
        mock_conn.get_session.return_value = mock_session_context
        mock_conn.get_transaction.return_value = mock_session_context
        
        return mock_conn
    
    def test_read_csv_file_integration(self, sample_csv_content, mock_db_connection):
        """Test reading a real CSV file."""
        loader = DataLoader(db_connection=mock_db_connection)
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_content)
            csv_path = f.name
        
        try:
            # Test reading CSV
            df = loader._read_csv_file(csv_path)
            
            assert len(df) == 3
            assert list(df.columns) == DataLoader.EXPECTED_COLUMNS
            assert df.iloc[0]['id'] == 'test_id_1'
            assert df.iloc[0]['amount'] == '100.50'
            assert df.iloc[1]['paid_at'] is None  # Empty string converted to None
            
        finally:
            # Clean up
            Path(csv_path).unlink()
    
    def test_validate_data_integrity_integration(self, sample_csv_content, mock_db_connection):
        """Test data validation with real CSV data."""
        loader = DataLoader(db_connection=mock_db_connection)
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_content)
            csv_path = f.name
        
        try:
            # Read and validate CSV
            df = loader._read_csv_file(csv_path)
            report = loader.validate_data_integrity(df)
            
            assert report.total_rows == 3
            assert report.valid_rows == 3
            assert report.invalid_rows == 0
            assert len(report.errors) == 0
            assert report.success_rate == 100.0
            
        finally:
            # Clean up
            Path(csv_path).unlink()
    
    def test_validate_data_with_errors_integration(self, mock_db_connection):
        """Test data validation with invalid CSV data."""
        loader = DataLoader(db_connection=mock_db_connection)
        
        # CSV with validation errors
        invalid_csv_content = """id,name,company_id,amount,status,created_at,paid_at
,MiPasajefy,cbf1c8b09cd5b549416d49d220a40cbd317f952e,100.50,paid,2019-01-01,2019-01-01
test_id_2,""" + "A" * 150 + """,cbf1c8b09cd5b549416d49d220a40cbd317f952e,invalid_amount,invalid_status,invalid_date,
test_id_3,MiPasajefy,,50.00,voided,2019-01-03,"""
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(invalid_csv_content)
            csv_path = f.name
        
        try:
            # Read and validate CSV
            df = loader._read_csv_file(csv_path)
            report = loader.validate_data_integrity(df)
            
            assert report.total_rows == 3
            assert report.invalid_rows > 0
            assert len(report.errors) > 0
            assert report.success_rate < 100.0
            
            # Check for specific error types
            error_types = [error['type'] for error in report.errors]
            assert 'missing_required_field' in error_types
            assert 'field_too_long' in error_types
            assert 'invalid_amount_format' in error_types
            assert 'invalid_status' in error_types
            
        finally:
            # Clean up
            Path(csv_path).unlink()
    
    def test_row_conversion_integration(self, sample_csv_content, mock_db_connection):
        """Test converting CSV rows to RawTransaction objects."""
        loader = DataLoader(db_connection=mock_db_connection)
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_content)
            csv_path = f.name
        
        try:
            # Read CSV and convert rows
            df = loader._read_csv_file(csv_path)
            
            for _, row in df.iterrows():
                transaction = loader._row_to_raw_transaction(row)
                
                assert transaction.id is not None
                assert transaction.company_id is not None
                assert transaction.status in DataLoader.VALID_STATUSES
                
                if transaction.amount is not None:
                    assert float(transaction.amount) > 0
                    
        finally:
            # Clean up
            Path(csv_path).unlink()
    
    def test_load_csv_to_database_integration(self, sample_csv_content, mock_db_connection):
        """Test complete CSV loading workflow."""
        loader = DataLoader(db_connection=mock_db_connection)
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(sample_csv_content)
            csv_path = f.name
        
        try:
            # Mock successful database operations
            mock_db_connection.get_transaction.return_value.__enter__.return_value.flush = Mock()
            
            # Load CSV to database
            report = loader.load_csv_to_database(csv_path, batch_size=2, validate_data=True)
            
            assert report.file_path == csv_path
            assert report.total_rows_processed == 3
            assert report.validation_report.total_rows == 3
            assert report.execution_time_seconds > 0
            
            # Verify database operations were called
            assert mock_db_connection.get_transaction.called
            
        finally:
            # Clean up
            Path(csv_path).unlink()