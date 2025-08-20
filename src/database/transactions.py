"""Transaction management utilities."""

import logging
from contextlib import contextmanager
from typing import Any, Callable, Generator, Optional, TypeVar

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.database.connection import DatabaseConnection

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TransactionManager:
    """Manages database transactions with retry logic and error handling."""
    
    def __init__(self, db_connection: Optional[DatabaseConnection] = None):
        """Initialize transaction manager.
        
        Args:
            db_connection: Database connection instance. If None, uses global instance.
        """
        from src.database.connection import db_connection as global_db_connection
        self.db_connection = db_connection or global_db_connection
    
    @contextmanager
    def transaction(self, 
                   autocommit: bool = True,
                   rollback_on_error: bool = True) -> Generator[Session, None, None]:
        """Context manager for database transactions.
        
        Args:
            autocommit: Whether to automatically commit on success
            rollback_on_error: Whether to automatically rollback on error
        """
        session = self.db_connection.create_session()
        transaction = session.begin()
        
        try:
            yield session
            
            if autocommit:
                transaction.commit()
                logger.debug("Transaction committed successfully")
                
        except Exception as e:
            if rollback_on_error:
                transaction.rollback()
                logger.error(f"Transaction rolled back due to error: {e}")
            raise
            
        finally:
            session.close()
    
    def execute_with_retry(self,
                          operation: Callable[[Session], T],
                          max_retries: int = 3,
                          retry_on_exceptions: tuple = (SQLAlchemyError,)) -> Optional[T]:
        """Execute a database operation with retry logic.
        
        Args:
            operation: Function that takes a session and returns a result
            max_retries: Maximum number of retry attempts
            retry_on_exceptions: Tuple of exceptions to retry on
            
        Returns:
            Result of the operation or None if all retries failed
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                with self.transaction() as session:
                    result = operation(session)
                    return result
                    
            except retry_on_exceptions as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(f"Operation failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    continue
                else:
                    logger.error(f"Operation failed after {max_retries + 1} attempts: {e}")
                    break
                    
            except Exception as e:
                # Don't retry on non-specified exceptions
                logger.error(f"Operation failed with non-retryable error: {e}")
                raise
        
        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        
        return None
    
    def bulk_insert(self,
                   session: Session,
                   model_class: Any,
                   data: list,
                   batch_size: int = 1000) -> int:
        """Perform bulk insert operation.
        
        Args:
            session: Database session
            model_class: SQLAlchemy model class
            data: List of dictionaries with data to insert
            batch_size: Number of records to insert per batch
            
        Returns:
            Number of records inserted
        """
        total_inserted = 0
        
        try:
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                
                # Convert dictionaries to model instances if needed
                if batch and isinstance(batch[0], dict):
                    batch = [model_class(**item) for item in batch]
                
                session.bulk_save_objects(batch)
                total_inserted += len(batch)
                
                logger.debug(f"Inserted batch of {len(batch)} records "
                           f"({total_inserted}/{len(data)} total)")
            
            logger.info(f"Bulk insert completed: {total_inserted} records")
            return total_inserted
            
        except SQLAlchemyError as e:
            logger.error(f"Bulk insert failed: {e}")
            raise
    
    def bulk_update(self,
                   session: Session,
                   model_class: Any,
                   data: list,
                   batch_size: int = 1000) -> int:
        """Perform bulk update operation.
        
        Args:
            session: Database session
            model_class: SQLAlchemy model class
            data: List of dictionaries with data to update
            batch_size: Number of records to update per batch
            
        Returns:
            Number of records updated
        """
        total_updated = 0
        
        try:
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                session.bulk_update_mappings(model_class, batch)
                total_updated += len(batch)
                
                logger.debug(f"Updated batch of {len(batch)} records "
                           f"({total_updated}/{len(data)} total)")
            
            logger.info(f"Bulk update completed: {total_updated} records")
            return total_updated
            
        except SQLAlchemyError as e:
            logger.error(f"Bulk update failed: {e}")
            raise


# Global transaction manager instance
transaction_manager = TransactionManager()