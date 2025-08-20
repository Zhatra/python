"""Unit tests for database connection functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError

from src.database.connection import DatabaseConnection


class TestDatabaseConnection:
    """Test cases for DatabaseConnection class."""
    
    def test_init_with_default_connection_string(self):
        """Test initialization with default connection string."""
        db_conn = DatabaseConnection()
        assert db_conn.connection_string is not None
        assert "postgresql://" in db_conn.connection_string
    
    def test_init_with_custom_connection_string(self):
        """Test initialization with custom connection string."""
        custom_conn_str = "postgresql://user:pass@localhost:5432/testdb"
        db_conn = DatabaseConnection(custom_conn_str)
        assert db_conn.connection_string == custom_conn_str
    
    @patch('src.database.connection.create_engine')
    def test_engine_property_creates_engine_once(self, mock_create_engine):
        """Test that engine property creates engine only once."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        db_conn = DatabaseConnection()
        
        # Access engine multiple times
        engine1 = db_conn.engine
        engine2 = db_conn.engine
        
        # Should be the same instance
        assert engine1 is engine2
        assert engine1 is mock_engine
        
        # create_engine should be called only once
        mock_create_engine.assert_called_once()
    
    @patch('src.database.connection.sessionmaker')
    def test_session_factory_property(self, mock_sessionmaker):
        """Test session factory property."""
        mock_factory = Mock()
        mock_sessionmaker.return_value = mock_factory
        
        db_conn = DatabaseConnection()
        
        # Mock the engine by setting the private attribute
        mock_engine = Mock()
        db_conn._engine = mock_engine
        
        factory1 = db_conn.session_factory
        factory2 = db_conn.session_factory
        
        # Should be the same instance
        assert factory1 is factory2
        assert factory1 is mock_factory
        
        # sessionmaker should be called only once
        mock_sessionmaker.assert_called_once_with(
            bind=mock_engine,
            autocommit=False,
            autoflush=False
        )
    
    def test_create_session(self):
        """Test session creation."""
        db_conn = DatabaseConnection()
        
        # Mock the session factory by setting the private attribute
        mock_factory = Mock()
        mock_session = Mock()
        mock_factory.return_value = mock_session
        db_conn._session_factory = mock_factory
        
        session = db_conn.create_session()
        
        assert session is mock_session
        mock_factory.assert_called_once()
    
    def test_get_session_context_manager_success(self):
        """Test get_session context manager with successful operation."""
        db_conn = DatabaseConnection()
        mock_session = Mock()
        
        with patch.object(db_conn, 'create_session', return_value=mock_session):
            with db_conn.get_session() as session:
                assert session is mock_session
                # Simulate some operation
                session.query.return_value = "result"
            
            # Verify session was committed and closed
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
            mock_session.rollback.assert_not_called()
    
    def test_get_session_context_manager_with_exception(self):
        """Test get_session context manager with exception."""
        db_conn = DatabaseConnection()
        mock_session = Mock()
        
        with patch.object(db_conn, 'create_session', return_value=mock_session):
            with pytest.raises(ValueError):
                with db_conn.get_session() as session:
                    raise ValueError("Test exception")
            
            # Verify session was rolled back and closed
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            mock_session.commit.assert_not_called()
    
    def test_get_transaction_context_manager_success(self):
        """Test get_transaction context manager with successful operation."""
        db_conn = DatabaseConnection()
        mock_session = Mock()
        mock_transaction = Mock()
        mock_session.begin.return_value = mock_transaction
        
        with patch.object(db_conn, 'create_session', return_value=mock_session):
            with db_conn.get_transaction() as session:
                assert session is mock_session
            
            # Verify transaction was committed and session closed
            mock_session.begin.assert_called_once()
            mock_transaction.commit.assert_called_once()
            mock_session.close.assert_called_once()
            mock_transaction.rollback.assert_not_called()
    
    def test_get_transaction_context_manager_with_exception(self):
        """Test get_transaction context manager with exception."""
        db_conn = DatabaseConnection()
        mock_session = Mock()
        mock_transaction = Mock()
        mock_session.begin.return_value = mock_transaction
        
        with patch.object(db_conn, 'create_session', return_value=mock_session):
            with pytest.raises(ValueError):
                with db_conn.get_transaction() as session:
                    raise ValueError("Test exception")
            
            # Verify transaction was rolled back and session closed
            mock_transaction.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            mock_transaction.commit.assert_not_called()
    
    @patch('src.database.connection.text')
    def test_test_connection_success(self, mock_text):
        """Test successful connection test."""
        db_conn = DatabaseConnection()
        mock_session = Mock()
        
        with patch.object(db_conn, 'get_session') as mock_get_session:
            mock_get_session.return_value.__enter__.return_value = mock_session
            mock_get_session.return_value.__exit__.return_value = None
            
            result = db_conn.test_connection()
            
            assert result is True
            mock_session.execute.assert_called_once()
            mock_text.assert_called_once_with("SELECT 1")
    
    @patch('src.database.connection.text')
    def test_test_connection_failure(self, mock_text):
        """Test connection test failure."""
        db_conn = DatabaseConnection()
        
        with patch.object(db_conn, 'get_session') as mock_get_session:
            mock_get_session.side_effect = SQLAlchemyError("Connection failed")
            
            result = db_conn.test_connection()
            
            assert result is False
    
    def test_close_disposes_engine(self):
        """Test that close method disposes the engine."""
        db_conn = DatabaseConnection()
        mock_engine = Mock()
        
        # Set up the engine
        db_conn._engine = mock_engine
        db_conn._session_factory = Mock()
        
        db_conn.close()
        
        # Verify engine was disposed and references cleared
        mock_engine.dispose.assert_called_once()
        assert db_conn._engine is None
        assert db_conn._session_factory is None