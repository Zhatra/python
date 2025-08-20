"""Unit tests for DataExtractor class."""

import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

import pandas as pd
from sqlalchemy.exc import SQLAlchemyError

from src.data_processing.extractor import (
    DataExtractor, ExtractionMetadata, ExtractionStatistics
)
from src.database.connection import DatabaseConnection


class TestDataExtractor:
    """Test cases for DataExtractor class."""
    
    @pytest.fixture
    def mock_db_connection(self):
        """Create a mock database connection."""
        mock_connection = Mock(spec=DatabaseConnection)
        mock_session = Mock()
        
        # Mock the context manager properly
        context_manager = Mock()
        context_manager.__enter__ = Mock(return_value=mock_session)
        context_manager.__exit__ = Mock(return_value=None)
        mock_connection.get_session.return_value = context_manager
        
        return mock_connection, mock_session
    
    @pytest.fixture
    def extractor(self, mock_db_connection):
        """Create DataExtractor instance with mock connection."""
        mock_connection, _ = mock_db_connection
        return DataExtractor(db_connection=mock_connection)
    
    @pytest.fixture
    def sample_dataframe(self):
        """Create sample DataFrame for testing."""
        return pd.DataFrame({
            'id': ['1', '2', '3'],
            'name': ['Company A', 'Company B', 'Company C'],
            'company_id': ['comp1', 'comp2', 'comp3'],
            'amount': [100.50, 200.75, 300.25],
            'status': ['paid', 'pending_payment', 'refunded'],
            'created_at': ['2023-01-01 10:00:00', '2023-01-02 11:00:00', '2023-01-03 12:00:00'],
            'paid_at': ['2023-01-01 10:30:00', None, '2023-01-03 12:30:00']
        })
    
    def test_init_with_connection(self):
        """Test DataExtractor initialization with provided connection."""
        mock_connection = Mock(spec=DatabaseConnection)
        extractor = DataExtractor(db_connection=mock_connection)
        assert extractor.db_connection == mock_connection
        assert extractor._extraction_history == []
    
    @patch('src.data_processing.extractor.db_connection')
    def test_init_without_connection(self, mock_global_connection):
        """Test DataExtractor initialization without provided connection."""
        extractor = DataExtractor()
        assert extractor.db_connection == mock_global_connection
    
    def test_validate_extraction_parameters_valid(self, extractor):
        """Test parameter validation with valid parameters."""
        # Should not raise any exception
        extractor._validate_extraction_parameters(
            output_path="test.csv",
            output_format="csv",
            table_name="test_table",
            schema="test_schema"
        )
    
    def test_validate_extraction_parameters_invalid_format(self, extractor):
        """Test parameter validation with invalid format."""
        with pytest.raises(ValueError, match="Unsupported format"):
            extractor._validate_extraction_parameters(
                output_path="test.txt",
                output_format="txt",
                table_name="test_table",
                schema="test_schema"
            )
    
    def test_validate_extraction_parameters_wrong_extension(self, extractor):
        """Test parameter validation with wrong file extension."""
        with pytest.raises(ValueError, match="should have .csv extension"):
            extractor._validate_extraction_parameters(
                output_path="test.txt",
                output_format="csv",
                table_name="test_table",
                schema="test_schema"
            )
    
    def test_validate_extraction_parameters_missing_params(self, extractor):
        """Test parameter validation with missing parameters."""
        with pytest.raises(ValueError, match="Output path is required"):
            extractor._validate_extraction_parameters("", "csv", "table", "schema")
        
        with pytest.raises(ValueError, match="Table name is required"):
            extractor._validate_extraction_parameters("test.csv", "csv", "", "schema")
        
        with pytest.raises(ValueError, match="Schema name is required"):
            extractor._validate_extraction_parameters("test.csv", "csv", "table", "")
    
    def test_get_table_row_count_no_filters(self, extractor, mock_db_connection):
        """Test getting table row count without filters."""
        _, mock_session = mock_db_connection
        mock_result = Mock()
        mock_result.scalar.return_value = 100
        mock_session.execute.return_value = mock_result
        
        count = extractor._get_table_row_count("test_table", "test_schema")
        
        assert count == 100
        mock_session.execute.assert_called_once()
        call_args = mock_session.execute.call_args[0][0]
        assert "SELECT COUNT(*) FROM test_schema.test_table" in str(call_args)
    
    def test_get_table_row_count_with_filters(self, extractor, mock_db_connection):
        """Test getting table row count with filters."""
        _, mock_session = mock_db_connection
        mock_result = Mock()
        mock_result.scalar.return_value = 50
        mock_session.execute.return_value = mock_result
        
        filters = {'status': 'paid', 'company_id': ['comp1', 'comp2']}
        count = extractor._get_table_row_count("test_table", "test_schema", filters)
        
        assert count == 50
        mock_session.execute.assert_called_once()
        call_args = str(mock_session.execute.call_args[0][0])
        assert "WHERE" in call_args
        assert "status = 'paid'" in call_args
        assert "company_id IN ('comp1','comp2')" in call_args
    
    def test_get_table_row_count_database_error(self, extractor, mock_db_connection):
        """Test getting table row count with database error."""
        _, mock_session = mock_db_connection
        mock_session.execute.side_effect = SQLAlchemyError("Database error")
        
        with pytest.raises(SQLAlchemyError):
            extractor._get_table_row_count("test_table", "test_schema")
    
    @patch('pandas.read_sql')
    def test_extract_single_chunk_success(self, mock_read_sql, extractor, mock_db_connection, sample_dataframe):
        """Test successful single chunk extraction."""
        _, mock_session = mock_db_connection
        mock_read_sql.return_value = sample_dataframe
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            with patch.object(extractor, '_write_dataframe_to_file') as mock_write:
                rows_extracted = extractor._extract_single_chunk(
                    output_path=tmp_path,
                    output_format="csv",
                    table_name="test_table",
                    schema="test_schema",
                    query_filters=None,
                    format_options={}
                )
            
            assert rows_extracted == 3
            mock_read_sql.assert_called_once()
            mock_write.assert_called_once_with(sample_dataframe, tmp_path, "csv", {})
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    @patch('pandas.read_sql')
    def test_extract_single_chunk_with_filters(self, mock_read_sql, extractor, mock_db_connection, sample_dataframe):
        """Test single chunk extraction with filters."""
        _, mock_session = mock_db_connection
        mock_read_sql.return_value = sample_dataframe
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            with patch.object(extractor, '_write_dataframe_to_file'):
                filters = {'status': ['paid', 'refunded']}
                extractor._extract_single_chunk(
                    output_path=tmp_path,
                    output_format="csv",
                    table_name="test_table",
                    schema="test_schema",
                    query_filters=filters,
                    format_options={}
                )
            
            # Check that the query includes the filter
            call_args = mock_read_sql.call_args[0][0]
            assert "WHERE" in call_args
            assert "status IN ('paid','refunded')" in call_args
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_write_dataframe_to_csv(self, extractor, sample_dataframe):
        """Test writing DataFrame to CSV file."""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            format_options = {
                'index': False,
                'include_header': True,
                'date_format': '%Y-%m-%d %H:%M:%S'
            }
            
            extractor._write_dataframe_to_file(
                sample_dataframe, tmp_path, "csv", format_options
            )
            
            # Verify file was created and has correct content
            assert Path(tmp_path).exists()
            
            # Read back and verify
            df_read = pd.read_csv(tmp_path)
            assert len(df_read) == 3
            assert list(df_read.columns) == list(sample_dataframe.columns)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_write_dataframe_to_parquet(self, extractor, sample_dataframe):
        """Test writing DataFrame to Parquet file."""
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            format_options = {
                'index': False,
                'compression': 'snappy'
            }
            
            extractor._write_dataframe_to_file(
                sample_dataframe, tmp_path, "parquet", format_options
            )
            
            # Verify file was created and has correct content
            assert Path(tmp_path).exists()
            
            # Read back and verify
            df_read = pd.read_parquet(tmp_path)
            assert len(df_read) == 3
            assert list(df_read.columns) == list(sample_dataframe.columns)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_write_dataframe_unsupported_format(self, extractor, sample_dataframe):
        """Test writing DataFrame with unsupported format."""
        with pytest.raises(ValueError, match="Unsupported output format"):
            extractor._write_dataframe_to_file(
                sample_dataframe, "test.txt", "txt", {}
            )
    
    @patch('src.data_processing.extractor.DataExtractor._get_table_row_count')
    @patch('src.data_processing.extractor.DataExtractor._extract_single_chunk')
    def test_extract_to_csv_small_dataset(self, mock_extract_single, mock_get_count, extractor):
        """Test CSV extraction for small dataset."""
        mock_get_count.return_value = 100
        mock_extract_single.return_value = 100
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Mock file creation
            Path(tmp_path).touch()
            Path(tmp_path).write_text("test,data\n1,2\n")
            
            metadata = extractor.extract_to_csv(
                output_path=tmp_path,
                table_name="test_table",
                schema="test_schema"
            )
            
            assert isinstance(metadata, ExtractionMetadata)
            assert metadata.output_format == "csv"
            assert metadata.total_rows == 100
            assert metadata.extracted_rows == 100
            assert metadata.source_table == "test_table"
            assert metadata.source_schema == "test_schema"
            
            # Check that it was added to history
            assert len(extractor._extraction_history) == 1
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    @patch('src.data_processing.extractor.DataExtractor._get_table_row_count')
    @patch('src.data_processing.extractor.DataExtractor._extract_in_chunks')
    def test_extract_to_csv_large_dataset(self, mock_extract_chunks, mock_get_count, extractor):
        """Test CSV extraction for large dataset."""
        mock_get_count.return_value = 50000
        mock_extract_chunks.return_value = 50000
        
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Mock file creation
            Path(tmp_path).touch()
            
            metadata = extractor.extract_to_csv(
                output_path=tmp_path,
                chunk_size=10000
            )
            
            assert metadata.total_rows == 50000
            assert metadata.extracted_rows == 50000
            mock_extract_chunks.assert_called_once()
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_extract_raw_transactions_csv(self, extractor):
        """Test extracting raw transactions to CSV."""
        with patch.object(extractor, 'extract_to_csv') as mock_extract:
            mock_metadata = Mock(spec=ExtractionMetadata)
            mock_extract.return_value = mock_metadata
            
            result = extractor.extract_raw_transactions(
                output_path="test.csv",
                output_format="csv",
                company_ids=["comp1", "comp2"],
                status_filter=["paid"]
            )
            
            assert result == mock_metadata
            mock_extract.assert_called_once_with(
                output_path="test.csv",
                table_name="raw_transactions",
                schema="raw_data",
                query_filters={'company_id': ["comp1", "comp2"], 'status': ["paid"]}
            )
    
    def test_extract_raw_transactions_parquet(self, extractor):
        """Test extracting raw transactions to Parquet."""
        with patch.object(extractor, 'extract_to_parquet') as mock_extract:
            mock_metadata = Mock(spec=ExtractionMetadata)
            mock_extract.return_value = mock_metadata
            
            result = extractor.extract_raw_transactions(
                output_path="test.parquet",
                output_format="parquet"
            )
            
            assert result == mock_metadata
            mock_extract.assert_called_once()
    
    def test_extract_raw_transactions_invalid_format(self, extractor):
        """Test extracting raw transactions with invalid format."""
        with pytest.raises(ValueError, match="Unsupported format"):
            extractor.extract_raw_transactions(
                output_path="test.txt",
                output_format="txt"
            )
    
    def test_extract_normalized_data_charges(self, extractor):
        """Test extracting normalized charges data."""
        with patch.object(extractor, 'extract_to_csv') as mock_extract:
            mock_metadata = Mock(spec=ExtractionMetadata)
            mock_extract.return_value = mock_metadata
            
            result = extractor.extract_normalized_data(
                output_path="charges.csv",
                table_name="charges",
                company_ids=["comp1"]
            )
            
            assert result == mock_metadata
            mock_extract.assert_called_once_with(
                output_path="charges.csv",
                table_name="charges",
                schema="normalized_data",
                query_filters={'company_id': ["comp1"]}
            )
    
    def test_extract_normalized_data_companies(self, extractor):
        """Test extracting normalized companies data."""
        with patch.object(extractor, 'extract_to_parquet') as mock_extract:
            mock_metadata = Mock(spec=ExtractionMetadata)
            mock_extract.return_value = mock_metadata
            
            result = extractor.extract_normalized_data(
                output_path="companies.parquet",
                output_format="parquet",
                table_name="companies"
            )
            
            assert result == mock_metadata
            mock_extract.assert_called_once()
    
    def test_extract_normalized_data_invalid_table(self, extractor):
        """Test extracting normalized data with invalid table name."""
        with pytest.raises(ValueError, match="table_name must be"):
            extractor.extract_normalized_data(
                output_path="test.csv",
                table_name="invalid_table"
            )
    
    def test_extract_daily_summary(self, extractor):
        """Test extracting daily summary data."""
        with patch.object(extractor, 'extract_to_csv') as mock_extract:
            mock_metadata = Mock(spec=ExtractionMetadata)
            mock_extract.return_value = mock_metadata
            
            result = extractor.extract_daily_summary("summary.csv")
            
            assert result == mock_metadata
            mock_extract.assert_called_once_with(
                output_path="summary.csv",
                table_name="daily_transaction_summary",
                schema="normalized_data"
            )
    
    def test_get_extraction_metadata_specific(self, extractor):
        """Test getting specific extraction metadata."""
        # Add some mock metadata to history
        metadata1 = ExtractionMetadata(
            extraction_id="ext_1",
            source_table="table1",
            source_schema="schema1",
            output_format="csv",
            output_path="test1.csv",
            total_rows=100,
            extracted_rows=100,
            execution_time_seconds=1.0,
            extraction_timestamp=datetime.now()
        )
        metadata2 = ExtractionMetadata(
            extraction_id="ext_2",
            source_table="table2",
            source_schema="schema2",
            output_format="parquet",
            output_path="test2.parquet",
            total_rows=200,
            extracted_rows=200,
            execution_time_seconds=2.0,
            extraction_timestamp=datetime.now()
        )
        
        extractor._extraction_history = [metadata1, metadata2]
        
        # Test getting specific metadata
        result = extractor.get_extraction_metadata("ext_1")
        assert result == metadata1
        
        # Test getting non-existent metadata
        with pytest.raises(ValueError, match="Extraction ID not found"):
            extractor.get_extraction_metadata("ext_999")
    
    def test_get_extraction_metadata_all(self, extractor):
        """Test getting all extraction metadata."""
        metadata1 = Mock(spec=ExtractionMetadata)
        metadata2 = Mock(spec=ExtractionMetadata)
        extractor._extraction_history = [metadata1, metadata2]
        
        result = extractor.get_extraction_metadata()
        assert len(result) == 2
        assert result == [metadata1, metadata2]
    
    def test_get_extraction_statistics_empty(self, extractor):
        """Test getting extraction statistics with no history."""
        stats = extractor.get_extraction_statistics()
        
        assert isinstance(stats, ExtractionStatistics)
        assert stats.total_extractions == 0
        assert stats.successful_extractions == 0
        assert stats.failed_extractions == 0
        assert stats.total_rows_extracted == 0
        assert stats.average_extraction_time == 0.0
    
    def test_get_extraction_statistics_with_data(self, extractor):
        """Test getting extraction statistics with history data."""
        metadata1 = ExtractionMetadata(
            extraction_id="ext_1",
            source_table="table1",
            source_schema="schema1",
            output_format="csv",
            output_path="test1.csv",
            total_rows=100,
            extracted_rows=100,
            execution_time_seconds=1.0,
            extraction_timestamp=datetime.now()
        )
        metadata2 = ExtractionMetadata(
            extraction_id="ext_2",
            source_table="table2",
            source_schema="schema2",
            output_format="parquet",
            output_path="test2.parquet",
            total_rows=200,
            extracted_rows=150,  # Partial extraction
            execution_time_seconds=2.0,
            extraction_timestamp=datetime.now()
        )
        
        extractor._extraction_history = [metadata1, metadata2]
        
        stats = extractor.get_extraction_statistics()
        
        assert stats.total_extractions == 2
        assert stats.successful_extractions == 1  # Only metadata1 has 100% success rate
        assert stats.failed_extractions == 1
        assert stats.total_rows_extracted == 250
        assert stats.total_execution_time_seconds == 3.0
        assert stats.average_extraction_time == 1.5
        assert stats.formats_used == {'csv': 1, 'parquet': 1}
        assert stats.largest_extraction_rows == 150
    
    def test_clear_extraction_history(self, extractor):
        """Test clearing extraction history."""
        extractor._extraction_history = [Mock(), Mock()]
        assert len(extractor._extraction_history) == 2
        
        extractor.clear_extraction_history()
        assert len(extractor._extraction_history) == 0
    
    def test_export_extraction_metadata(self, extractor):
        """Test exporting extraction metadata to JSON."""
        metadata = ExtractionMetadata(
            extraction_id="ext_1",
            source_table="table1",
            source_schema="schema1",
            output_format="csv",
            output_path="test1.csv",
            total_rows=100,
            extracted_rows=100,
            execution_time_seconds=1.0,
            extraction_timestamp=datetime.now()
        )
        extractor._extraction_history = [metadata]
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            extractor.export_extraction_metadata(tmp_path)
            
            # Verify file was created and has correct content
            assert Path(tmp_path).exists()
            
            with open(tmp_path, 'r') as f:
                data = json.load(f)
            
            assert 'extraction_history' in data
            assert 'statistics' in data
            assert 'export_timestamp' in data
            assert len(data['extraction_history']) == 1
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_validate_output_file_csv_valid(self, extractor, sample_dataframe):
        """Test validating a valid CSV output file."""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Create a valid CSV file
            sample_dataframe.to_csv(tmp_path, index=False)
            
            result = extractor.validate_output_file(tmp_path)
            
            assert result['valid'] is True
            assert result['file_format'] == 'csv'
            assert result['column_count'] == 7
            assert 'file_size_bytes' in result
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_validate_output_file_parquet_valid(self, extractor, sample_dataframe):
        """Test validating a valid Parquet output file."""
        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as tmp_file:
            tmp_path = tmp_file.name
        
        try:
            # Create a valid Parquet file
            sample_dataframe.to_parquet(tmp_path, index=False)
            
            result = extractor.validate_output_file(tmp_path)
            
            assert result['valid'] is True
            assert result['file_format'] == 'parquet'
            assert result['column_count'] == 7
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    
    def test_validate_output_file_not_exists(self, extractor):
        """Test validating a non-existent file."""
        result = extractor.validate_output_file("non_existent_file.csv")
        
        assert result['valid'] is False
        assert result['error'] == 'File does not exist'
    
    def test_validate_output_file_unsupported_format(self, extractor):
        """Test validating a file with unsupported format."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(b"test data")
        
        try:
            result = extractor.validate_output_file(tmp_path)
            
            assert result['valid'] is False
            assert result['error'] == 'Unsupported file format'
        finally:
            Path(tmp_path).unlink(missing_ok=True)


class TestExtractionMetadata:
    """Test cases for ExtractionMetadata class."""
    
    def test_extraction_success_rate_full_success(self):
        """Test success rate calculation with full success."""
        metadata = ExtractionMetadata(
            extraction_id="test",
            source_table="table",
            source_schema="schema",
            output_format="csv",
            output_path="test.csv",
            total_rows=100,
            extracted_rows=100,
            execution_time_seconds=1.0,
            extraction_timestamp=datetime.now()
        )
        
        assert metadata.extraction_success_rate == 100.0
    
    def test_extraction_success_rate_partial_success(self):
        """Test success rate calculation with partial success."""
        metadata = ExtractionMetadata(
            extraction_id="test",
            source_table="table",
            source_schema="schema",
            output_format="csv",
            output_path="test.csv",
            total_rows=100,
            extracted_rows=75,
            execution_time_seconds=1.0,
            extraction_timestamp=datetime.now()
        )
        
        assert metadata.extraction_success_rate == 75.0
    
    def test_extraction_success_rate_zero_rows(self):
        """Test success rate calculation with zero total rows."""
        metadata = ExtractionMetadata(
            extraction_id="test",
            source_table="table",
            source_schema="schema",
            output_format="csv",
            output_path="test.csv",
            total_rows=0,
            extracted_rows=0,
            execution_time_seconds=1.0,
            extraction_timestamp=datetime.now()
        )
        
        assert metadata.extraction_success_rate == 100.0
    
    def test_to_dict(self):
        """Test converting metadata to dictionary."""
        timestamp = datetime.now()
        metadata = ExtractionMetadata(
            extraction_id="test",
            source_table="table",
            source_schema="schema",
            output_format="csv",
            output_path="test.csv",
            total_rows=100,
            extracted_rows=100,
            execution_time_seconds=1.0,
            extraction_timestamp=timestamp,
            file_size_bytes=1024,
            compression_used="gzip",
            query_filters={'status': 'paid'}
        )
        
        result = metadata.to_dict()
        
        assert result['extraction_id'] == "test"
        assert result['source_table'] == "table"
        assert result['total_rows'] == 100
        assert result['file_size_bytes'] == 1024
        assert result['compression_used'] == "gzip"
        assert result['query_filters'] == {'status': 'paid'}
        assert result['extraction_timestamp'] == timestamp.isoformat()
        assert result['extraction_success_rate'] == 100.0


class TestExtractionStatistics:
    """Test cases for ExtractionStatistics class."""
    
    def test_str_representation(self):
        """Test string representation of ExtractionStatistics."""
        stats = ExtractionStatistics(
            total_extractions=10,
            successful_extractions=8,
            failed_extractions=2,
            total_rows_extracted=1000,
            total_execution_time_seconds=50.0,
            formats_used={'csv': 6, 'parquet': 4},
            average_extraction_time=5.0,
            largest_extraction_rows=200
        )
        
        str_repr = str(stats)
        assert "total=10" in str_repr
        assert "successful=8" in str_repr
        assert "avg_time=5.00s" in str_repr