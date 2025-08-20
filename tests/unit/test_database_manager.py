"""Unit tests for database manager functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from decimal import Decimal
from sqlalchemy.exc import SQLAlchemyError

from src.database.manager import DatabaseManager


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""
    
    @patch('src.database.connection.db_connection')
    def test_init_with_default_connection(self, mock_global_conn):
        """Test initialization with default database connection."""
        manager = DatabaseManager()
        assert manager.db_connection is mock_global_conn
    
    def test_init_with_custom_connection(self):
        """Test initialization with custom database connection."""
        mock_conn = Mock()
        manager = DatabaseManager(mock_conn)
        assert manager.db_connection is mock_conn
    
    def test_create_schemas_success(self):
        """Test successful schema creation."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        manager = DatabaseManager(mock_conn)
        result = manager.create_schemas()
        
        assert result is True
        assert mock_session.execute.call_count == 4  # 2 CREATE SCHEMA + 2 GRANT
    
    def test_create_schemas_failure(self):
        """Test schema creation failure."""
        mock_conn = Mock()
        mock_conn.get_session.side_effect = SQLAlchemyError("Schema creation failed")
        
        manager = DatabaseManager(mock_conn)
        result = manager.create_schemas()
        
        assert result is False
    
    @patch('src.database.manager.Base')
    def test_create_tables_success(self, mock_base):
        """Test successful table creation."""
        mock_conn = Mock()
        mock_engine = Mock()
        mock_conn.engine = mock_engine
        
        manager = DatabaseManager(mock_conn)
        
        # Mock create_schemas to return True
        with patch.object(manager, 'create_schemas', return_value=True):
            result = manager.create_tables()
            
            assert result is True
            mock_base.metadata.create_all.assert_called_once_with(bind=mock_engine)
    
    @patch('src.database.manager.Base')
    def test_create_tables_schema_failure(self, mock_base):
        """Test table creation failure due to schema creation failure."""
        mock_conn = Mock()
        manager = DatabaseManager(mock_conn)
        
        # Mock create_schemas to return False
        with patch.object(manager, 'create_schemas', return_value=False):
            result = manager.create_tables()
            
            assert result is False
            mock_base.metadata.create_all.assert_not_called()
    
    @patch('src.database.manager.Base')
    def test_create_tables_failure(self, mock_base):
        """Test table creation failure."""
        mock_conn = Mock()
        mock_base.metadata.create_all.side_effect = SQLAlchemyError("Table creation failed")
        
        manager = DatabaseManager(mock_conn)
        
        # Mock create_schemas to return True
        with patch.object(manager, 'create_schemas', return_value=True):
            result = manager.create_tables()
            
            assert result is False
    
    def test_create_reporting_view_success(self):
        """Test successful reporting view creation."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        manager = DatabaseManager(mock_conn)
        result = manager.create_reporting_view()
        
        assert result is True
        # Should execute 2 statements: DROP VIEW and CREATE VIEW
        assert mock_session.execute.call_count == 2
    
    def test_create_reporting_view_failure(self):
        """Test reporting view creation failure."""
        mock_conn = Mock()
        mock_conn.get_session.side_effect = SQLAlchemyError("View creation failed")
        
        manager = DatabaseManager(mock_conn)
        result = manager.create_reporting_view()
        
        assert result is False
    
    @patch('src.database.manager.inspect')
    def test_table_exists_true(self, mock_inspect):
        """Test table_exists returns True when table exists."""
        mock_conn = Mock()
        mock_inspector = Mock()
        mock_inspector.get_table_names.return_value = ['table1', 'table2', 'test_table']
        mock_inspect.return_value = mock_inspector
        
        manager = DatabaseManager(mock_conn)
        result = manager.table_exists('test_table', 'public')
        
        assert result is True
        mock_inspect.assert_called_once_with(mock_conn.engine)
        mock_inspector.get_table_names.assert_called_once_with(schema='public')
    
    @patch('src.database.manager.inspect')
    def test_table_exists_false(self, mock_inspect):
        """Test table_exists returns False when table doesn't exist."""
        mock_conn = Mock()
        mock_inspector = Mock()
        mock_inspector.get_table_names.return_value = ['table1', 'table2']
        mock_inspect.return_value = mock_inspector
        
        manager = DatabaseManager(mock_conn)
        result = manager.table_exists('nonexistent_table', 'public')
        
        assert result is False
    
    def test_get_table_row_count_success(self):
        """Test successful row count retrieval."""
        mock_conn = Mock()
        mock_session = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = 42
        mock_session.execute.return_value = mock_result
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        manager = DatabaseManager(mock_conn)
        result = manager.get_table_row_count('test_table', 'public')
        
        assert result == 42
        mock_session.execute.assert_called_once()
    
    def test_get_table_row_count_failure(self):
        """Test row count retrieval failure."""
        mock_conn = Mock()
        mock_conn.get_session.side_effect = SQLAlchemyError("Query failed")
        
        manager = DatabaseManager(mock_conn)
        result = manager.get_table_row_count('test_table', 'public')
        
        assert result is None
    
    def test_initialize_database_success(self):
        """Test successful database initialization."""
        mock_conn = Mock()
        mock_conn.test_connection.return_value = True
        
        manager = DatabaseManager(mock_conn)
        
        with patch.object(manager, 'create_tables', return_value=True), \
             patch.object(manager, 'create_reporting_view', return_value=True):
            
            result = manager.initialize_database()
            
            assert result is True
            mock_conn.test_connection.assert_called_once()
    
    def test_initialize_database_connection_failure(self):
        """Test database initialization with connection failure."""
        mock_conn = Mock()
        mock_conn.test_connection.return_value = False
        
        manager = DatabaseManager(mock_conn)
        result = manager.initialize_database()
        
        assert result is False
    
    def test_initialize_database_table_creation_failure(self):
        """Test database initialization with table creation failure."""
        mock_conn = Mock()
        mock_conn.test_connection.return_value = True
        
        manager = DatabaseManager(mock_conn)
        
        with patch.object(manager, 'create_tables', return_value=False):
            result = manager.initialize_database()
            
            assert result is False
    
    def test_initialize_database_view_creation_failure(self):
        """Test database initialization with view creation failure."""
        mock_conn = Mock()
        mock_conn.test_connection.return_value = True
        
        manager = DatabaseManager(mock_conn)
        
        with patch.object(manager, 'create_tables', return_value=True), \
             patch.object(manager, 'create_reporting_view', return_value=False):
            
            result = manager.initialize_database()
            
            assert result is False


class TestDatabaseManagerNormalizedSchema:
    """Test cases for normalized schema creation and management."""
    
    def test_create_normalized_schema_success(self):
        """Test successful normalized schema creation."""
        mock_conn = Mock()
        mock_session = Mock()
        mock_engine = Mock()
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        mock_conn.engine = mock_engine
        
        manager = DatabaseManager(mock_conn)
        
        with patch('src.database.manager.Base') as mock_base:
            result = manager.create_normalized_schema()
            
            assert result is True
            # Should execute CREATE SCHEMA and GRANT statements
            assert mock_session.execute.call_count == 2
            # Should create tables for Company and Charge models
            mock_base.metadata.create_all.assert_called_once()
    
    def test_create_normalized_schema_failure(self):
        """Test normalized schema creation failure."""
        mock_conn = Mock()
        mock_conn.get_session.side_effect = SQLAlchemyError("Schema creation failed")
        
        manager = DatabaseManager(mock_conn)
        result = manager.create_normalized_schema()
        
        assert result is False
    
    @patch('src.database.manager.inspect')
    def test_validate_normalized_schema_success(self, mock_inspect):
        """Test successful normalized schema validation."""
        mock_conn = Mock()
        mock_session = Mock()
        mock_inspector = Mock()
        
        # Mock schema existence check
        mock_result = Mock()
        mock_result.fetchone.return_value = ('normalized_data',)
        mock_session.execute.return_value = mock_result
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        # Mock table existence
        mock_inspector.get_table_names.return_value = ['companies', 'charges']
        
        # Mock foreign key constraints
        mock_inspector.get_foreign_keys.return_value = [
            {
                'name': 'fk_charges_company_id',
                'constrained_columns': ['company_id'],
                'referred_table': 'companies',
                'referred_columns': ['company_id']
            }
        ]
        
        # Mock indexes
        mock_inspector.get_indexes.return_value = [
            {'name': 'idx_company_name', 'column_names': ['company_name']},
            {'name': 'idx_charge_company_id', 'column_names': ['company_id']}
        ]
        
        mock_inspect.return_value = mock_inspector
        
        manager = DatabaseManager(mock_conn)
        result = manager.validate_normalized_schema()
        
        assert result['is_valid'] is True
        assert result['schema_exists'] is True
        assert result['companies_table_exists'] is True
        assert result['charges_table_exists'] is True
        assert len(result['foreign_key_constraints']) == 1
        assert len(result['validation_errors']) == 0
    
    @patch('src.database.manager.inspect')
    def test_validate_normalized_schema_missing_schema(self, mock_inspect):
        """Test schema validation when normalized_data schema is missing."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock schema existence check - schema doesn't exist
        mock_result = Mock()
        mock_result.fetchone.return_value = None
        mock_session.execute.return_value = mock_result
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        manager = DatabaseManager(mock_conn)
        result = manager.validate_normalized_schema()
        
        assert result['is_valid'] is False
        assert result['schema_exists'] is False
        assert 'normalized_data schema does not exist' in result['validation_errors']
    
    @patch('src.database.manager.inspect')
    def test_validate_normalized_schema_missing_tables(self, mock_inspect):
        """Test schema validation when tables are missing."""
        mock_conn = Mock()
        mock_session = Mock()
        mock_inspector = Mock()
        
        # Mock schema existence check - schema exists
        mock_result = Mock()
        mock_result.fetchone.return_value = ('normalized_data',)
        mock_session.execute.return_value = mock_result
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        # Mock table existence - only companies table exists
        mock_inspector.get_table_names.return_value = ['companies']
        # Mock indexes to return empty list
        mock_inspector.get_indexes.return_value = []
        mock_inspect.return_value = mock_inspector
        
        manager = DatabaseManager(mock_conn)
        result = manager.validate_normalized_schema()
        
        assert result['is_valid'] is False
        assert result['companies_table_exists'] is True
        assert result['charges_table_exists'] is False
        assert 'charges table does not exist' in result['validation_errors']


class TestDatabaseManagerDataDistribution:
    """Test cases for data distribution functionality."""
    
    @patch('src.data_processing.transformer.DataTransformer')
    def test_distribute_data_to_normalized_tables_success(self, mock_transformer_class):
        """Test successful data distribution to normalized tables."""
        mock_conn = Mock()
        mock_transformer = Mock()
        mock_transformer_class.return_value = mock_transformer
        
        # Mock transformation report
        mock_report = Mock()
        mock_report.total_raw_rows = 100
        mock_report.transformed_rows = 95
        mock_report.skipped_rows = 5
        mock_report.companies_created = 2
        mock_report.charges_created = 95
        mock_report.transformation_success_rate = 95.0
        mock_report.execution_time_seconds = 2.5
        mock_report.transformation_errors = []
        mock_report.data_quality_issues = []
        
        mock_transformer.transform_to_schema.return_value = mock_report
        mock_transformer.get_transformation_statistics.return_value = {
            'companies_count': 2,
            'charges_count': 95
        }
        mock_transformer.validate_transformation_integrity.return_value = {
            'is_valid': True,
            'integrity_score': 100.0
        }
        
        manager = DatabaseManager(mock_conn)
        result = manager.distribute_data_to_normalized_tables()
        
        assert result['success'] is True
        assert result['transformation_report']['total_raw_rows'] == 100
        assert result['transformation_report']['transformed_rows'] == 95
        assert result['transformation_report']['companies_created'] == 2
        assert result['transformation_report']['charges_created'] == 95
        assert result['transformation_report']['success_rate'] == 95.0
        
        # Verify transformer was initialized with correct connection
        mock_transformer_class.assert_called_once_with(mock_conn)
        mock_transformer.transform_to_schema.assert_called_once_with(
            source_table="raw_transactions",
            batch_size=1000,
            validate_data=True,
            apply_business_rules=True
        )
    
    @patch('src.data_processing.transformer.DataTransformer')
    def test_distribute_data_to_normalized_tables_failure(self, mock_transformer_class):
        """Test data distribution failure."""
        mock_conn = Mock()
        mock_transformer_class.side_effect = Exception("Transformation failed")
        
        manager = DatabaseManager(mock_conn)
        result = manager.distribute_data_to_normalized_tables()
        
        assert result['success'] is False
        assert 'Transformation failed' in result['error']
        assert result['transformation_report'] is None
    
    def test_get_data_distribution_statistics_success(self):
        """Test successful retrieval of data distribution statistics."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock query results
        mock_session.query.return_value.count.side_effect = [2, 95, 100]  # companies, charges, raw
        
        # Mock company statistics
        mock_company_stat = Mock()
        mock_company_stat.company_name = 'Test Company'
        mock_company_stat.charge_count = 50
        mock_company_stat.total_amount = 1000.00
        mock_session.query.return_value.join.return_value.group_by.return_value.all.return_value = [mock_company_stat]
        
        # Mock status distribution
        mock_status_stat = Mock()
        mock_status_stat.status = 'paid'
        mock_status_stat.count = 80
        mock_status_stat.total_amount = 2000.00
        
        # Mock date range
        mock_date_range = Mock()
        mock_date_range.earliest = datetime(2023, 1, 1)
        mock_date_range.latest = datetime(2023, 12, 31)
        
        # Configure mock session to return different results for different queries
        def mock_query_side_effect(*args):
            mock_query = Mock()
            if hasattr(args[0], '__name__') and 'Company' in str(args[0]):
                mock_query.count.return_value = 2
            elif hasattr(args[0], '__name__') and 'Charge' in str(args[0]):
                if 'outerjoin' in str(mock_query):
                    mock_query.outerjoin.return_value.filter.return_value.count.return_value = 0
                else:
                    mock_query.count.return_value = 95
                    mock_query.group_by.return_value.all.return_value = [mock_status_stat]
            elif hasattr(args[0], '__name__') and 'RawTransaction' in str(args[0]):
                mock_query.count.return_value = 100
            else:
                # For func queries
                mock_query.first.return_value = mock_date_range
            return mock_query
        
        mock_session.query.side_effect = mock_query_side_effect
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        manager = DatabaseManager(mock_conn)
        
        with patch.object(mock_session, 'query') as mock_query_method:
            # Setup different return values for different query types
            mock_queries = []
            
            # Companies count query
            mock_company_query = Mock()
            mock_company_query.count.return_value = 2
            mock_queries.append(mock_company_query)
            
            # Charges count query
            mock_charge_query = Mock()
            mock_charge_query.count.return_value = 95
            mock_queries.append(mock_charge_query)
            
            # Raw transactions count query
            mock_raw_query = Mock()
            mock_raw_query.count.return_value = 100
            mock_queries.append(mock_raw_query)
            
            # Company statistics query
            mock_company_stats_query = Mock()
            mock_company_stats_query.join.return_value.group_by.return_value.all.return_value = [mock_company_stat]
            mock_queries.append(mock_company_stats_query)
            
            # Status distribution query
            mock_status_query = Mock()
            mock_status_query.group_by.return_value.all.return_value = [mock_status_stat]
            mock_queries.append(mock_status_query)
            
            # Date range query
            mock_date_query = Mock()
            mock_date_query.first.return_value = mock_date_range
            mock_queries.append(mock_date_query)
            
            # Orphaned charges query
            mock_orphaned_query = Mock()
            mock_orphaned_query.outerjoin.return_value.filter.return_value.count.return_value = 0
            mock_queries.append(mock_orphaned_query)
            
            # Companies without charges query
            mock_companies_no_charges_query = Mock()
            mock_companies_no_charges_query.outerjoin.return_value.filter.return_value.count.return_value = 0
            mock_queries.append(mock_companies_no_charges_query)
            
            mock_query_method.side_effect = mock_queries
            
            result = manager.get_data_distribution_statistics()
            
            assert 'record_counts' in result
            assert result['record_counts']['companies'] == 2
            assert result['record_counts']['charges'] == 95
            assert result['record_counts']['raw_transactions'] == 100
            assert result['record_counts']['transformation_rate'] == 95.0
            
            assert 'company_statistics' in result
            assert len(result['company_statistics']) == 1
            assert result['company_statistics'][0]['company_name'] == 'Test Company'
            
            assert 'status_distribution' in result
            assert len(result['status_distribution']) == 1
            assert result['status_distribution'][0]['status'] == 'paid'
            
            assert 'date_range' in result
            assert result['date_range']['earliest'] == '2023-01-01T00:00:00'
            
            assert 'data_integrity' in result
            assert result['data_integrity']['orphaned_charges'] == 0
            assert result['data_integrity']['integrity_score'] == 100
    
    def test_get_data_distribution_statistics_failure(self):
        """Test data distribution statistics retrieval failure."""
        mock_conn = Mock()
        mock_conn.get_session.side_effect = SQLAlchemyError("Query failed")
        
        manager = DatabaseManager(mock_conn)
        result = manager.get_data_distribution_statistics()
        
        assert 'error' in result
        assert 'Query failed' in result['error']


class TestDatabaseManagerReportingViews:
    """Test cases for reporting view functionality."""
    
    def test_create_reporting_view_enhanced_success(self):
        """Test successful creation of enhanced reporting view."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        manager = DatabaseManager(mock_conn)
        result = manager.create_reporting_view()
        
        assert result is True
        # Should execute 2 statements: DROP VIEW and CREATE VIEW
        assert mock_session.execute.call_count == 2
        
        # Verify the SQL contains enhanced aggregations (check the CREATE VIEW statement)
        create_call_args = mock_session.execute.call_args_list[1][0][0]  # Second call is CREATE VIEW
        sql_text = str(create_call_args)
        assert 'AVG(c.amount)' in sql_text
        assert 'MIN(c.amount)' in sql_text
        assert 'MAX(c.amount)' in sql_text
        assert 'paid_count' in sql_text
        assert 'refunded_count' in sql_text
    
    def test_query_daily_transaction_summary_no_filters(self):
        """Test querying daily transaction summary without filters."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock query result
        mock_result = Mock()
        mock_result.keys.return_value = ['transaction_date', 'company_name', 'total_amount']
        mock_result.fetchall.return_value = [
            ('2023-01-01', 'Test Company', Decimal('1000.00')),
            ('2023-01-02', 'Test Company', Decimal('1500.00'))
        ]
        mock_session.execute.return_value = mock_result
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        manager = DatabaseManager(mock_conn)
        result = manager.query_daily_transaction_summary()
        
        assert len(result) == 2
        assert result[0]['transaction_date'] == '2023-01-01'
        assert result[0]['company_name'] == 'Test Company'
        assert result[0]['total_amount'] == 1000.00  # Converted from Decimal
        mock_session.execute.assert_called_once()
    
    def test_query_daily_transaction_summary_with_filters(self):
        """Test querying daily transaction summary with filters."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock query result
        mock_result = Mock()
        mock_result.keys.return_value = ['transaction_date', 'company_name', 'total_amount']
        mock_result.fetchall.return_value = [
            ('2023-01-01', 'Test Company', Decimal('1000.00'))
        ]
        mock_session.execute.return_value = mock_result
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        manager = DatabaseManager(mock_conn)
        result = manager.query_daily_transaction_summary(
            start_date='2023-01-01',
            end_date='2023-01-31',
            company_id='comp123',
            limit=10
        )
        
        assert len(result) == 1
        mock_session.execute.assert_called_once()
        
        # Verify filters were applied in the query
        call_args = mock_session.execute.call_args
        query_text = str(call_args[0][0])
        params = call_args[0][1]
        
        assert 'start_date' in params
        assert 'end_date' in params
        assert 'company_id' in params
        assert 'limit' in params
        assert 'LIMIT' in query_text
    
    def test_query_daily_transaction_summary_failure(self):
        """Test daily transaction summary query failure."""
        mock_conn = Mock()
        mock_conn.get_session.side_effect = SQLAlchemyError("Query failed")
        
        manager = DatabaseManager(mock_conn)
        result = manager.query_daily_transaction_summary()
        
        assert result == []
    
    def test_get_company_transaction_totals_success(self):
        """Test successful retrieval of company transaction totals."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock query result
        mock_result = Mock()
        mock_result.keys.return_value = ['company_name', 'company_id', 'total_amount', 'total_transactions']
        mock_result.fetchall.return_value = [
            ('Company A', 'comp_a', Decimal('5000.00'), 50),
            ('Company B', 'comp_b', Decimal('3000.00'), 30)
        ]
        mock_session.execute.return_value = mock_result
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        manager = DatabaseManager(mock_conn)
        result = manager.get_company_transaction_totals()
        
        assert len(result) == 2
        assert result[0]['company_name'] == 'Company A'
        assert result[0]['total_amount'] == 5000.00
        assert result[1]['total_transactions'] == 30
    
    def test_get_company_transaction_totals_with_date_filter(self):
        """Test company transaction totals with date filters."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock query result
        mock_result = Mock()
        mock_result.keys.return_value = ['company_name', 'total_amount']
        mock_result.fetchall.return_value = [('Company A', Decimal('2000.00'))]
        mock_session.execute.return_value = mock_result
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        manager = DatabaseManager(mock_conn)
        result = manager.get_company_transaction_totals(
            start_date='2023-01-01',
            end_date='2023-01-31'
        )
        
        assert len(result) == 1
        
        # Verify date filters were applied
        call_args = mock_session.execute.call_args
        params = call_args[0][1]
        assert 'start_date' in params
        assert 'end_date' in params
    
    def test_get_daily_transaction_trends_success(self):
        """Test successful retrieval of daily transaction trends."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock query result
        mock_result = Mock()
        mock_result.keys.return_value = ['transaction_date', 'daily_total', 'daily_count', 'active_companies']
        mock_result.fetchall.return_value = [
            (datetime(2023, 1, 1).date(), Decimal('1000.00'), 10, 2),
            (datetime(2023, 1, 2).date(), Decimal('1200.00'), 12, 2)
        ]
        mock_session.execute.return_value = mock_result
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        manager = DatabaseManager(mock_conn)
        result = manager.get_daily_transaction_trends(days=7)
        
        assert len(result) == 2
        assert result[0]['transaction_date'] == '2023-01-01'
        assert result[0]['daily_total'] == 1000.00
        assert result[1]['daily_count'] == 12
    
    def test_get_daily_transaction_trends_with_company_filter(self):
        """Test daily transaction trends with company filter."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock query result
        mock_result = Mock()
        mock_result.keys.return_value = ['transaction_date', 'daily_total']
        mock_result.fetchall.return_value = [(datetime(2023, 1, 1).date(), Decimal('500.00'))]
        mock_session.execute.return_value = mock_result
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        manager = DatabaseManager(mock_conn)
        result = manager.get_daily_transaction_trends(days=30, company_id='comp123')
        
        assert len(result) == 1
        
        # Verify company filter was applied
        call_args = mock_session.execute.call_args
        params = call_args[0][1]
        assert 'company_id' in params
        assert params['company_id'] == 'comp123'
    
    def test_create_reporting_indexes_success(self):
        """Test successful creation of reporting indexes."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        manager = DatabaseManager(mock_conn)
        result = manager.create_reporting_indexes()
        
        assert result is True
        # Should execute 4 index creation statements
        assert mock_session.execute.call_count == 4
    
    def test_create_reporting_indexes_failure(self):
        """Test reporting indexes creation failure."""
        mock_conn = Mock()
        mock_conn.get_session.side_effect = SQLAlchemyError("Index creation failed")
        
        manager = DatabaseManager(mock_conn)
        result = manager.create_reporting_indexes()
        
        assert result is False
    
    def test_analyze_view_performance_success(self):
        """Test successful view performance analysis."""
        mock_conn = Mock()
        mock_session = Mock()
        
        # Mock execution plan result
        mock_explain_result = Mock()
        mock_explain_result.fetchone.return_value = ([{"Plan": {"Node Type": "Aggregate"}}],)
        
        # Mock statistics result
        mock_stats_result = Mock()
        mock_stats_result.fetchone.return_value = (
            100,  # total_rows
            2,    # unique_companies
            30,   # unique_dates
            datetime(2023, 1, 1).date(),  # earliest_date
            datetime(2023, 1, 30).date(), # latest_date
            Decimal('50000.00'),  # grand_total
            Decimal('1666.67')    # avg_daily_total
        )
        
        # Mock index usage result
        mock_index_result = Mock()
        mock_index_result.keys.return_value = ['schemaname', 'tablename', 'indexname', 'idx_scan']
        mock_index_result.fetchall.return_value = [
            ('normalized_data', 'charges', 'idx_charges_date_company_status', 100)
        ]
        
        # Configure session to return different results for different queries
        def mock_execute_side_effect(query, *args):
            query_str = str(query)
            if 'EXPLAIN' in query_str:
                return mock_explain_result
            elif 'COUNT(*)' in query_str and 'daily_transaction_summary' in query_str:
                return mock_stats_result
            elif 'pg_stat_user_indexes' in query_str:
                return mock_index_result
            return Mock()
        
        mock_session.execute.side_effect = mock_execute_side_effect
        
        # Mock the context manager properly
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=None)
        mock_conn.get_session.return_value = mock_context
        
        manager = DatabaseManager(mock_conn)
        result = manager.analyze_view_performance()
        
        assert 'execution_plan' in result
        assert 'view_statistics' in result
        assert 'index_usage' in result
        assert 'recommendations' in result
        
        # Check view statistics
        stats = result['view_statistics']
        assert stats['total_rows'] == 100
        assert stats['unique_companies'] == 2
        assert stats['grand_total'] == 50000.00
    
    def test_analyze_view_performance_failure(self):
        """Test view performance analysis failure."""
        mock_conn = Mock()
        mock_conn.get_session.side_effect = SQLAlchemyError("Analysis failed")
        
        manager = DatabaseManager(mock_conn)
        result = manager.analyze_view_performance()
        
        assert 'error' in result
        assert 'Analysis failed' in result['error']
    
    def test_generate_performance_recommendations(self):
        """Test performance recommendations generation."""
        mock_conn = Mock()
        manager = DatabaseManager(mock_conn)
        
        # Test with sequential scan in execution plan
        execution_plan = [{"Plan": {"Node Type": "Seq Scan"}}]
        index_stats = [
            {'indexname': 'unused_index', 'idx_scan': 0},
            {'indexname': 'used_index', 'idx_scan': 100}
        ]
        
        recommendations = manager._generate_performance_recommendations(execution_plan, index_stats)
        
        assert len(recommendations) > 0
        assert any('sequential scans' in rec for rec in recommendations)
        assert any('unused indexes' in rec for rec in recommendations)
        assert any('ANALYZE command' in rec for rec in recommendations)