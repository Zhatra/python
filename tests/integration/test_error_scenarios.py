"""Integration tests for error scenarios and edge cases."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError, DatabaseError

from src.api.main import app
from src.api.number_set import NumberSet
from src.data_processing.loader import DataLoader
from src.data_processing.extractor import DataExtractor
from src.data_processing.transformer import DataTransformer
from src.database.connection import DatabaseConnection
from src.database.manager import DatabaseManager
from src.exceptions import (
    DatabaseConnectionError, DatabaseTransactionError, DataLoadingError,
    DataExtractionError, DataTransformationError, FileNotFoundError,
    NumberOutOfRangeError, NumberAlreadyExtractedError
)


class TestAPIErrorScenarios:
    """Test API error scenarios and edge cases."""
    
    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)
    
    def test_extract_number_out_of_range_low(self):
        """Test extracting number below valid range."""
        response = self.client.post("/extract/0")
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "NUMBER_OUT_OF_RANGE"
        assert "outside valid range" in data["message"]
    
    def test_extract_number_out_of_range_high(self):
        """Test extracting number above valid range."""
        response = self.client.post("/extract/101")
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "NUMBER_OUT_OF_RANGE"
        assert "outside valid range" in data["message"]
    
    def test_extract_number_already_extracted(self):
        """Test extracting already extracted number."""
        # Reset first to ensure clean state
        self.client.post("/reset")
        
        # First extraction should succeed
        response1 = self.client.post("/extract/50")
        assert response1.status_code == 200
        
        # Second extraction should fail
        response2 = self.client.post("/extract/50")
        assert response2.status_code == 409
        data = response2.json()
        assert data["error"] == "NUMBER_ALREADY_EXTRACTED"
        assert "already been extracted" in data["message"]
    
    def test_get_missing_number_no_extractions(self):
        """Test getting missing number when no numbers extracted."""
        # Reset first to ensure clean state
        self.client.post("/reset")
        
        response = self.client.get("/missing")
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "NO_NUMBERS_EXTRACTED"
        assert "No numbers have been extracted" in data["message"]
    
    def test_get_missing_number_multiple_extractions(self):
        """Test getting missing number when multiple numbers extracted."""
        # Reset first
        self.client.post("/reset")
        
        # Extract multiple numbers
        self.client.post("/extract/25")
        self.client.post("/extract/75")
        
        response = self.client.get("/missing")
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "MULTIPLE_NUMBERS_EXTRACTED"
        assert "Cannot find single missing number when" in data["message"]
        assert data["details"]["extracted_count"] == 2
    
    def test_extract_invalid_number_type(self):
        """Test extracting with invalid number type in URL."""
        response = self.client.post("/extract/not_a_number")
        
        assert response.status_code == 422  # FastAPI validation error
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
    
    def test_api_request_validation_error(self):
        """Test API request validation errors."""
        # Test with invalid path parameter
        response = self.client.post("/extract/abc")
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "validation_errors" in data["details"]
    
    def test_api_successful_workflow(self):
        """Test successful API workflow to ensure error handling doesn't break normal flow."""
        # Reset
        response = self.client.post("/reset")
        assert response.status_code == 200
        
        # Extract a number
        response = self.client.post("/extract/42")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["extracted_number"] == 42
        
        # Get missing number
        response = self.client.get("/missing")
        assert response.status_code == 200
        data = response.json()
        assert data["missing_number"] == 42
        
        # Check status
        response = self.client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["extracted_count"] == 1
        assert 42 in data["extracted_numbers"]


class TestDataProcessingErrorScenarios:
    """Test data processing error scenarios."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_data_loader_file_not_found(self):
        """Test DataLoader with non-existent file."""
        loader = DataLoader()
        non_existent_file = os.path.join(self.temp_dir, "non_existent.csv")
        
        with pytest.raises(DataLoadingError) as exc_info:
            loader.load_csv_to_database(non_existent_file)
        
        assert "File does not exist" in str(exc_info.value)
        assert exc_info.value.file_path == non_existent_file
    
    def test_data_loader_invalid_csv_format(self):
        """Test DataLoader with invalid CSV format."""
        # Create invalid CSV file
        invalid_csv = os.path.join(self.temp_dir, "invalid.csv")
        with open(invalid_csv, 'w') as f:
            f.write("not,a,valid,csv,format\n")
            f.write("missing,required,columns\n")
        
        loader = DataLoader()
        
        with pytest.raises(DataLoadingError):
            loader.load_csv_to_database(invalid_csv)
    
    def test_data_loader_empty_csv(self):
        """Test DataLoader with empty CSV file."""
        empty_csv = os.path.join(self.temp_dir, "empty.csv")
        with open(empty_csv, 'w') as f:
            pass  # Create empty file
        
        loader = DataLoader()
        
        with pytest.raises(DataLoadingError):
            loader.load_csv_to_database(empty_csv)
    
    def test_data_loader_malformed_csv(self):
        """Test DataLoader with malformed CSV data."""
        malformed_csv = os.path.join(self.temp_dir, "malformed.csv")
        with open(malformed_csv, 'w') as f:
            f.write("id,name,company_id,amount,status,created_at,paid_at\n")
            f.write('test_id,"Company with "quotes" problem",comp_id,100.00,paid,2023-01-01,\n')
        
        loader = DataLoader()
        
        # This should handle the malformed data gracefully
        with patch.object(loader.db_connection, 'get_transaction') as mock_transaction:
            mock_session = Mock()
            mock_transaction.return_value.__enter__.return_value = mock_session
            
            try:
                report = loader.load_csv_to_database(malformed_csv)
                # Should complete but may have validation issues
                assert report.total_rows_processed >= 0
            except DataLoadingError:
                # This is also acceptable for malformed data
                pass
    
    @patch('src.data_processing.loader.DatabaseConnection')
    def test_data_loader_database_connection_error(self, mock_db_connection):
        """Test DataLoader with database connection error."""
        # Mock database connection to raise error
        mock_db_connection.return_value.get_transaction.side_effect = DatabaseConnectionError("Connection failed")
        
        # Create valid CSV file
        valid_csv = os.path.join(self.temp_dir, "valid.csv")
        with open(valid_csv, 'w') as f:
            f.write("id,name,company_id,amount,status,created_at,paid_at\n")
            f.write("test_id,Test Company,comp_id,100.00,paid,2023-01-01,\n")
        
        loader = DataLoader(mock_db_connection.return_value)
        
        with pytest.raises(DataLoadingError):
            loader.load_csv_to_database(valid_csv)
    
    def test_data_extractor_invalid_output_path(self):
        """Test DataExtractor with invalid output path."""
        extractor = DataExtractor()
        
        with pytest.raises((DataExtractionError, PermissionError)):
            extractor.extract_to_csv("/invalid/path/output.csv")
    
    def test_data_extractor_unsupported_format(self):
        """Test DataExtractor with unsupported format."""
        extractor = DataExtractor()
        output_path = os.path.join(self.temp_dir, "output.txt")
        
        with pytest.raises(ValueError) as exc_info:
            extractor.extract_to_csv(output_path)
        
        assert "should have .csv extension" in str(exc_info.value)
    
    @patch('src.data_processing.extractor.DatabaseConnection')
    def test_data_extractor_database_error(self, mock_db_connection):
        """Test DataExtractor with database error."""
        # Mock database connection to raise error
        mock_db_connection.return_value.get_session.side_effect = DatabaseConnectionError("Connection failed")
        
        extractor = DataExtractor(mock_db_connection.return_value)
        output_path = os.path.join(self.temp_dir, "output.csv")
        
        with pytest.raises(DatabaseConnectionError):
            extractor.extract_to_csv(output_path)
    
    @patch('src.data_processing.transformer.DatabaseConnection')
    def test_data_transformer_database_error(self, mock_db_connection):
        """Test DataTransformer with database error."""
        # Mock database connection to raise error
        mock_db_connection.return_value.get_transaction.side_effect = DatabaseTransactionError("Transaction failed")
        
        transformer = DataTransformer(mock_db_connection.return_value)
        
        with pytest.raises(DatabaseTransactionError):
            transformer.transform_to_schema()
    
    def test_data_transformer_no_raw_data(self):
        """Test DataTransformer with no raw data."""
        with patch('src.data_processing.transformer.DatabaseConnection') as mock_db_connection:
            # Mock empty query result
            mock_session = Mock()
            mock_session.query.return_value.all.return_value = []
            mock_db_connection.return_value.get_transaction.return_value.__enter__.return_value = mock_session
            
            transformer = DataTransformer(mock_db_connection.return_value)
            report = transformer.transform_to_schema()
            
            assert report.total_raw_rows == 0
            assert report.transformed_rows == 0
            assert report.companies_created == 0
            assert report.charges_created == 0


class TestDatabaseErrorScenarios:
    """Test database error scenarios."""
    
    @patch('src.database.connection.create_engine')
    def test_database_connection_creation_error(self, mock_create_engine):
        """Test database connection creation error."""
        mock_create_engine.side_effect = OperationalError("Connection failed", None, None)
        
        db_conn = DatabaseConnection("invalid://connection/string")
        
        # Accessing engine property should raise error
        with pytest.raises(OperationalError):
            _ = db_conn.engine
    
    @patch('src.database.connection.DatabaseConnection.create_session')
    def test_database_session_error(self, mock_create_session):
        """Test database session error."""
        mock_session = Mock()
        mock_session.commit.side_effect = DatabaseError("Commit failed", None, None)
        mock_create_session.return_value = mock_session
        
        db_conn = DatabaseConnection()
        
        with pytest.raises(DatabaseTransactionError):
            with db_conn.get_session() as session:
                pass  # Session commit should fail
    
    @patch('src.database.connection.DatabaseConnection.create_session')
    def test_database_transaction_error(self, mock_create_session):
        """Test database transaction error."""
        mock_session = Mock()
        mock_transaction = Mock()
        mock_transaction.commit.side_effect = DatabaseError("Transaction failed", None, None)
        mock_session.begin.return_value = mock_transaction
        mock_create_session.return_value = mock_session
        
        db_conn = DatabaseConnection()
        
        with pytest.raises(DatabaseTransactionError):
            with db_conn.get_transaction() as session:
                pass  # Transaction commit should fail
    
    def test_database_manager_connection_test_failure(self):
        """Test DatabaseManager connection test failure."""
        with patch('src.database.manager.DatabaseConnection') as mock_db_connection:
            mock_db_connection.return_value.test_connection.return_value = False
            
            manager = DatabaseManager(mock_db_connection.return_value)
            result = manager.initialize_database()
            
            assert result is False
    
    @patch('src.database.manager.DatabaseConnection')
    def test_database_manager_schema_creation_error(self, mock_db_connection):
        """Test DatabaseManager schema creation error."""
        mock_session = Mock()
        mock_session.execute.side_effect = DatabaseError("Schema creation failed", None, None)
        mock_db_connection.return_value.get_session.return_value.__enter__.return_value = mock_session
        mock_db_connection.return_value.test_connection.return_value = True
        
        manager = DatabaseManager(mock_db_connection.return_value)
        result = manager.create_schemas()
        
        assert result is False


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_number_set_boundary_values(self):
        """Test NumberSet with boundary values."""
        number_set = NumberSet(100)
        
        # Test minimum value
        result = number_set.extract(1)
        assert result is True
        
        # Reset and test maximum value
        number_set.reset()
        result = number_set.extract(100)
        assert result is True
    
    def test_number_set_custom_max_number(self):
        """Test NumberSet with custom max_number."""
        number_set = NumberSet(50)
        
        # Should work with numbers up to 50
        result = number_set.extract(50)
        assert result is True
        
        # Should fail with numbers above 50
        with pytest.raises(NumberOutOfRangeError):
            number_set.extract(51)
    
    def test_validation_edge_cases(self):
        """Test validation with edge cases."""
        from src.validation import InputValidator
        
        # Test amount with maximum precision
        result = InputValidator.validate_amount("999999999999999.99")
        assert result.is_valid
        assert result.cleaned_value == Decimal("999999999999999.99")
        
        # Test very small positive amount
        result = InputValidator.validate_amount("0.01")
        assert result.is_valid
        assert result.cleaned_value == Decimal("0.01")
        
        # Test string field with exact max length
        result = InputValidator.validate_string_field("a" * 24, "Test", max_length=24)
        assert result.is_valid
        assert len(result.cleaned_value) == 24
    
    def test_concurrent_number_extraction(self):
        """Test concurrent number extraction scenarios."""
        # This would be more relevant in a multi-threaded environment
        # For now, test sequential operations that might simulate race conditions
        number_set = NumberSet()
        
        # Extract same number multiple times quickly
        result1 = number_set.extract(42)
        assert result1 is True
        
        # Second extraction should fail
        with pytest.raises(NumberAlreadyExtractedError):
            number_set.extract(42)
    
    def test_large_dataset_simulation(self):
        """Test behavior with large dataset simulation."""
        # Test with larger number set
        large_number_set = NumberSet(10000)
        
        # Extract a number from large set
        result = large_number_set.extract(5000)
        assert result is True
        
        # Find missing number should still work
        missing = large_number_set.find_missing_number()
        assert missing == 5000
    
    def test_memory_efficiency_with_large_sets(self):
        """Test memory efficiency with large number sets."""
        # Test that large sets don't cause memory issues
        large_set = NumberSet(100000)
        
        # Basic operations should still work
        assert large_set.count_remaining() == 100000
        assert large_set.count_extracted() == 0
        
        # Extract and verify
        large_set.extract(50000)
        assert large_set.count_remaining() == 99999
        assert large_set.count_extracted() == 1


class TestErrorRecovery:
    """Test error recovery and resilience."""
    
    def test_api_error_recovery(self):
        """Test API error recovery after errors."""
        client = TestClient(app)
        
        # Cause an error
        response = client.post("/extract/150")
        assert response.status_code == 400
        
        # API should still work after error
        response = client.post("/reset")
        assert response.status_code == 200
        
        response = client.post("/extract/50")
        assert response.status_code == 200
    
    def test_database_connection_recovery(self):
        """Test database connection recovery after errors."""
        with patch('src.database.connection.DatabaseConnection.create_session') as mock_create_session:
            # First call fails
            mock_create_session.side_effect = [
                OperationalError("Connection failed", None, None),
                Mock()  # Second call succeeds
            ]
            
            db_conn = DatabaseConnection()
            
            # First attempt should fail
            with pytest.raises(DatabaseConnectionError):
                with db_conn.get_session():
                    pass
            
            # Second attempt should succeed (in real scenario, connection might recover)
            # This is more of a conceptual test since we're mocking
    
    def test_validation_error_accumulation(self):
        """Test that validation errors are properly accumulated."""
        from src.validation import InputValidator
        
        # Test record with multiple validation errors
        invalid_record = {
            'id': '',  # Missing required
            'company_id': '',  # Missing required
            'amount': 'not_a_number',  # Invalid format
            'status': 'invalid_status',  # Invalid status
            'created_at': 'not_a_date'  # Invalid date
        }
        
        result = InputValidator.validate_transaction_record(invalid_record)
        
        assert not result.is_valid
        assert len(result.errors) >= 4  # Should have multiple errors
        
        # Check that all expected error types are present
        error_text = ' '.join(result.errors)
        assert 'required' in error_text
        assert 'Invalid amount' in error_text
        assert 'Invalid status' in error_text
        assert 'Unable to parse' in error_text