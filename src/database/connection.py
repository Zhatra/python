"""Database connection utilities with SQLAlchemy."""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, OperationalError, DatabaseError as SQLDatabaseError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from src.config import db_config
from src.exceptions import DatabaseConnectionError, DatabaseTransactionError

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database connections and sessions."""
    
    def __init__(self, connection_string: Optional[str] = None):
        """Initialize database connection.
        
        Args:
            connection_string: Database connection string. If None, uses config.
        """
        self.connection_string = connection_string or db_config.connection_string
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None
        
    @property
    def engine(self) -> Engine:
        """Get or create database engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.connection_string,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False  # Set to True for SQL debugging
            )
        return self._engine
    
    @property
    def session_factory(self) -> sessionmaker:
        """Get or create session factory."""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
        return self._session_factory
    
    def create_session(self) -> Session:
        """Create a new database session."""
        return self.session_factory()
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions with automatic cleanup."""
        session = None
        try:
            session = self.create_session()
            yield session
            session.commit()
        except OperationalError as e:
            if session:
                session.rollback()
            logger.error(f"Database operational error: {e}")
            raise DatabaseConnectionError(f"Database connection failed: {str(e)}")
        except SQLDatabaseError as e:
            if session:
                session.rollback()
            logger.error(f"Database error: {e}")
            raise DatabaseTransactionError(f"Database operation failed: {str(e)}")
        except Exception as e:
            if session:
                session.rollback()
            logger.error(f"Unexpected database session error: {e}")
            raise DatabaseTransactionError(f"Database session error: {str(e)}")
        finally:
            if session:
                session.close()
    
    @contextmanager
    def get_transaction(self) -> Generator[Session, None, None]:
        """Context manager for database transactions."""
        session = None
        transaction = None
        try:
            session = self.create_session()
            transaction = session.begin()
            yield session
            transaction.commit()
        except OperationalError as e:
            if transaction:
                transaction.rollback()
            logger.error(f"Database operational error in transaction: {e}")
            raise DatabaseConnectionError(f"Database connection failed: {str(e)}")
        except SQLDatabaseError as e:
            if transaction:
                transaction.rollback()
            logger.error(f"Database error in transaction: {e}")
            raise DatabaseTransactionError(f"Database transaction failed: {str(e)}")
        except Exception as e:
            if transaction:
                transaction.rollback()
            logger.error(f"Unexpected database transaction error: {e}")
            raise DatabaseTransactionError(f"Database transaction error: {str(e)}")
        finally:
            if session:
                session.close()
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
            return True
        except (DatabaseConnectionError, DatabaseTransactionError) as e:
            logger.error(f"Database connection test failed: {e.message}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during connection test: {e}")
            return False
    
    def close(self) -> None:
        """Close database engine and connections."""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connections closed")


# Global database connection instance
db_connection = DatabaseConnection()