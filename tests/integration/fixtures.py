"""
Test fixtures and utilities for integration tests.

This module provides reusable test fixtures, data generators, and cleanup
utilities for integration testing of the complete data pipeline.
"""

import pytest
import tempfile
import shutil
import os
import random
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Generator
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.database.connection import DatabaseConnection
from src.database.manager import DatabaseManager
from src.database.models import Base, RawTransaction, Company, Charge
from src.config import app_config


class TestDataGenerator:
    """Generates test data for integration tests."""
    
    @staticmethod
    def generate_csv_data(
        num_rows: int = 100,
        companies: Optional[List[Dict[str, str]]] = None,
        date_range_days: int = 365,
        base_date: Optional[datetime] = None
    ) -> str:
        """Generate CSV data for testing.
        
        Args:
            num_rows: Number of rows to generate
            companies: List of company dictionaries with 'name' and 'id' keys
            date_range_days: Range of days for random date generation
            base_date: Base date for date generation (defaults to 2019-01-01)
            
        Returns:
            CSV data as string
        """
        if companies is None:
            companies = [
                {"name": "MiPasajefy", "id": "cbf1c8b09cd5b549416d49d220a40cbd317f952e"},
                {"name": "Muebles chidos", "id": "8f642dc67fccf861548dfe1c761ce22f795e91f0"},
                {"name": "Test Company A", "id": "a1b2c3d4e5f6789012345678901234567890abcd"},
                {"name": "Test Company B", "id": "b2c3d4e5f6789012345678901234567890abcdef"},
            ]
        
        if base_date is None:
            base_date = datetime(2019, 1, 1)
        
        statuses = ["paid", "pending_payment", "voided", "refunded"]
        rows = []
        
        for i in range(num_rows):
            company = random.choice(companies)
            status = random.choice(statuses)
            amount = round(random.uniform(1.0, 1000.0), 2)
            created_date = base_date + timedelta(days=random.randint(0, date_range_days))
            
            # Generate paid_at based on status
            paid_at = ""
            if status in ["paid", "refunded"]:
                paid_date = created_date + timedelta(days=random.randint(0, 30))
                paid_at = paid_date.strftime("%Y-%m-%d")
            
            row = f"test_id_{i:06d},{company['name']},{company['id']},{amount},{status},{created_date.strftime('%Y-%m-%d')},{paid_at}"
            rows.append(row)
        
        header = "id,name,company_id,amount,status,created_at,paid_at"
        return header + "\n" + "\n".join(rows)
    
    @staticmethod
    def generate_invalid_csv_data(num_rows: int = 50) -> str:
        """Generate CSV data with various validation errors.
        
        Args:
            num_rows: Number of rows to generate
            
        Returns:
            CSV data with validation errors as string
        """
        rows = []
        error_types = [
            "missing_id",
            "missing_company_id", 
            "invalid_amount",
            "invalid_status",
            "invalid_date",
            "field_too_long"
        ]
        
        for i in range(num_rows):
            error_type = random.choice(error_types)
            
            if error_type == "missing_id":
                row = f",Test Company,company_id_{i},100.00,paid,2019-01-01,"
            elif error_type == "missing_company_id":
                row = f"test_id_{i},Test Company,,100.00,paid,2019-01-01,"
            elif error_type == "invalid_amount":
                row = f"test_id_{i},Test Company,company_id_{i},not_a_number,paid,2019-01-01,"
            elif error_type == "invalid_status":
                row = f"test_id_{i},Test Company,company_id_{i},100.00,invalid_status,2019-01-01,"
            elif error_type == "invalid_date":
                row = f"test_id_{i},Test Company,company_id_{i},100.00,paid,not_a_date,"
            elif error_type == "field_too_long":
                long_name = "A" * 200  # Exceeds typical field length limits
                row = f"test_id_{i},{long_name},company_id_{i},100.00,paid,2019-01-01,"
            else:
                # Valid row as fallback
                row = f"test_id_{i},Test Company,company_id_{i},100.00,paid,2019-01-01,"
            
            rows.append(row)
        
        header = "id,name,company_id,amount,status,created_at,paid_at"
        return header + "\n" + "\n".join(rows)
    
    @staticmethod
    def generate_large_csv_data(num_rows: int = 10000) -> str:
        """Generate large CSV dataset for performance testing.
        
        Args:
            num_rows: Number of rows to generate
            
        Returns:
            Large CSV data as string
        """
        return TestDataGenerator.generate_csv_data(
            num_rows=num_rows,
            date_range_days=1000,  # Spread over ~3 years
            base_date=datetime(2018, 1, 1)
        )


class DatabaseTestFixture:
    """Database fixture for integration tests."""
    
    def __init__(self, use_memory_db: bool = False):
        """Initialize database test fixture.
        
        Args:
            use_memory_db: If True, use in-memory SQLite database
        """
        self.use_memory_db = use_memory_db
        self.db_connection = None
        self.db_manager = None
        self.temp_db_file = None
        
    def setup(self) -> tuple[DatabaseConnection, DatabaseManager]:
        """Set up test database.
        
        Returns:
            Tuple of (DatabaseConnection, DatabaseManager)
        """
        if self.use_memory_db:
            # Use in-memory SQLite for fast testing
            engine = create_engine("sqlite:///:memory:", echo=False)
            Base.metadata.create_all(engine)
            
            # Create mock database connection
            class MockDatabaseConnection:
                def __init__(self, engine):
                    self.engine = engine
                    self.SessionLocal = sessionmaker(bind=engine)
                
                def get_session(self):
                    return self.SessionLocal()
                
                def get_transaction(self):
                    return self.SessionLocal()
                
                def test_connection(self):
                    return True
            
            self.db_connection = MockDatabaseConnection(engine)
            self.db_manager = DatabaseManager(self.db_connection)
            
        else:
            # Use PostgreSQL test database
            test_db_config = {
                'host': os.getenv('TEST_DB_HOST', 'localhost'),
                'port': int(os.getenv('TEST_DB_PORT', '5432')),
                'database': os.getenv('TEST_DB_NAME', 'test_technical_test'),
                'username': os.getenv('TEST_DB_USER', 'testuser'),
                'password': os.getenv('TEST_DB_PASSWORD', 'testpass')
            }
            
            connection_string = (
                f"postgresql://{test_db_config['username']}:{test_db_config['password']}"
                f"@{test_db_config['host']}:{test_db_config['port']}/{test_db_config['database']}"
            )
            
            self.db_connection = DatabaseConnection(connection_string)
            self.db_manager = DatabaseManager(self.db_connection)
            self.db_manager.initialize_database()
        
        return self.db_connection, self.db_manager
    
    def cleanup(self):
        """Clean up test database."""
        if self.db_connection and not self.use_memory_db:
            try:
                with self.db_connection.get_session() as session:
                    # Drop test schemas
                    session.execute(text("DROP SCHEMA IF EXISTS raw_data CASCADE"))
                    session.execute(text("DROP SCHEMA IF EXISTS normalized_data CASCADE"))
                    
                    # Drop test tables if they exist in public schema
                    session.execute(text("DROP TABLE IF EXISTS charges CASCADE"))
                    session.execute(text("DROP TABLE IF EXISTS companies CASCADE"))
                    session.execute(text("DROP TABLE IF EXISTS raw_transactions CASCADE"))
                    session.execute(text("DROP VIEW IF EXISTS daily_transaction_summary CASCADE"))
                    
            except Exception as e:
                print(f"Database cleanup warning: {e}")
        
        if self.temp_db_file and os.path.exists(self.temp_db_file):
            os.unlink(self.temp_db_file)


class FileTestFixture:
    """File fixture for integration tests."""
    
    def __init__(self):
        """Initialize file test fixture."""
        self.temp_dirs = []
        self.temp_files = []
    
    def create_temp_dir(self) -> str:
        """Create temporary directory.
        
        Returns:
            Path to temporary directory
        """
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        return temp_dir
    
    def create_temp_csv_file(self, csv_data: str, filename: str = "test_data.csv") -> str:
        """Create temporary CSV file.
        
        Args:
            csv_data: CSV data as string
            filename: Name of the CSV file
            
        Returns:
            Path to temporary CSV file
        """
        temp_dir = self.create_temp_dir()
        csv_file = os.path.join(temp_dir, filename)
        
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write(csv_data)
        
        self.temp_files.append(csv_file)
        return csv_file
    
    def create_sample_csv_file(self, num_rows: int = 100) -> str:
        """Create sample CSV file with generated data.
        
        Args:
            num_rows: Number of rows to generate
            
        Returns:
            Path to sample CSV file
        """
        csv_data = TestDataGenerator.generate_csv_data(num_rows)
        return self.create_temp_csv_file(csv_data, f"sample_{num_rows}_rows.csv")
    
    def create_invalid_csv_file(self, num_rows: int = 50) -> str:
        """Create CSV file with validation errors.
        
        Args:
            num_rows: Number of rows to generate
            
        Returns:
            Path to invalid CSV file
        """
        csv_data = TestDataGenerator.generate_invalid_csv_data(num_rows)
        return self.create_temp_csv_file(csv_data, f"invalid_{num_rows}_rows.csv")
    
    def create_large_csv_file(self, num_rows: int = 10000) -> str:
        """Create large CSV file for performance testing.
        
        Args:
            num_rows: Number of rows to generate
            
        Returns:
            Path to large CSV file
        """
        csv_data = TestDataGenerator.generate_large_csv_data(num_rows)
        return self.create_temp_csv_file(csv_data, f"large_{num_rows}_rows.csv")
    
    def cleanup(self):
        """Clean up temporary files and directories."""
        # Remove temporary files
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                print(f"File cleanup warning for {temp_file}: {e}")
        
        # Remove temporary directories
        for temp_dir in self.temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Directory cleanup warning for {temp_dir}: {e}")
        
        self.temp_files.clear()
        self.temp_dirs.clear()


class IntegrationTestFixture:
    """Combined fixture for integration tests."""
    
    def __init__(self, use_memory_db: bool = True):
        """Initialize integration test fixture.
        
        Args:
            use_memory_db: If True, use in-memory database for faster tests
        """
        self.db_fixture = DatabaseTestFixture(use_memory_db)
        self.file_fixture = FileTestFixture()
        self.db_connection = None
        self.db_manager = None
    
    def setup(self) -> tuple[DatabaseConnection, DatabaseManager, FileTestFixture]:
        """Set up integration test environment.
        
        Returns:
            Tuple of (DatabaseConnection, DatabaseManager, FileTestFixture)
        """
        self.db_connection, self.db_manager = self.db_fixture.setup()
        return self.db_connection, self.db_manager, self.file_fixture
    
    def cleanup(self):
        """Clean up integration test environment."""
        self.file_fixture.cleanup()
        self.db_fixture.cleanup()


# Pytest fixtures
@pytest.fixture(scope="function")
def test_database():
    """Pytest fixture for test database."""
    fixture = DatabaseTestFixture(use_memory_db=True)
    db_connection, db_manager = fixture.setup()
    
    yield db_connection, db_manager
    
    fixture.cleanup()


@pytest.fixture(scope="function")
def postgres_test_database():
    """Pytest fixture for PostgreSQL test database."""
    fixture = DatabaseTestFixture(use_memory_db=False)
    
    try:
        db_connection, db_manager = fixture.setup()
        yield db_connection, db_manager
    except Exception as e:
        pytest.skip(f"PostgreSQL test database not available: {e}")
    finally:
        fixture.cleanup()


@pytest.fixture(scope="function")
def file_fixture():
    """Pytest fixture for file operations."""
    fixture = FileTestFixture()
    
    yield fixture
    
    fixture.cleanup()


@pytest.fixture(scope="function")
def integration_fixture():
    """Pytest fixture for complete integration testing."""
    fixture = IntegrationTestFixture(use_memory_db=True)
    db_connection, db_manager, file_fixture = fixture.setup()
    
    yield db_connection, db_manager, file_fixture
    
    fixture.cleanup()


@pytest.fixture(scope="function")
def sample_csv_data():
    """Pytest fixture for sample CSV data."""
    return TestDataGenerator.generate_csv_data(num_rows=10)


@pytest.fixture(scope="function")
def large_csv_data():
    """Pytest fixture for large CSV data."""
    return TestDataGenerator.generate_large_csv_data(num_rows=1000)


@pytest.fixture(scope="function")
def invalid_csv_data():
    """Pytest fixture for invalid CSV data."""
    return TestDataGenerator.generate_invalid_csv_data(num_rows=20)


@pytest.fixture(scope="function")
def temp_csv_file(sample_csv_data, file_fixture):
    """Pytest fixture for temporary CSV file."""
    return file_fixture.create_temp_csv_file(sample_csv_data)


@pytest.fixture(scope="function")
def large_temp_csv_file(large_csv_data, file_fixture):
    """Pytest fixture for large temporary CSV file."""
    return file_fixture.create_temp_csv_file(large_csv_data, "large_test_data.csv")


@pytest.fixture(scope="function")
def invalid_temp_csv_file(invalid_csv_data, file_fixture):
    """Pytest fixture for invalid temporary CSV file."""
    return file_fixture.create_temp_csv_file(invalid_csv_data, "invalid_test_data.csv")


# Performance test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


# Test utilities
class TestMetrics:
    """Utilities for collecting test metrics."""
    
    @staticmethod
    def measure_execution_time(func, *args, **kwargs):
        """Measure function execution time.
        
        Args:
            func: Function to measure
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Tuple of (result, execution_time_seconds)
        """
        import time
        
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        return result, execution_time
    
    @staticmethod
    def measure_memory_usage():
        """Measure current memory usage.
        
        Returns:
            Memory usage in MB
        """
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            return memory_info.rss / 1024 / 1024  # Convert to MB
        except ImportError:
            return None
    
    @staticmethod
    def assert_performance_threshold(
        execution_time: float,
        max_time: float,
        operation_name: str = "Operation"
    ):
        """Assert that execution time is within threshold.
        
        Args:
            execution_time: Actual execution time
            max_time: Maximum allowed time
            operation_name: Name of the operation for error message
        """
        assert execution_time <= max_time, (
            f"{operation_name} took {execution_time:.2f}s, "
            f"which exceeds the maximum allowed time of {max_time:.2f}s"
        )


class TestDataValidator:
    """Utilities for validating test data."""
    
    @staticmethod
    def validate_csv_structure(csv_file: str, expected_columns: List[str]) -> bool:
        """Validate CSV file structure.
        
        Args:
            csv_file: Path to CSV file
            expected_columns: List of expected column names
            
        Returns:
            True if structure is valid
        """
        try:
            df = pd.read_csv(csv_file)
            return list(df.columns) == expected_columns
        except Exception:
            return False
    
    @staticmethod
    def validate_database_state(
        db_connection: DatabaseConnection,
        expected_raw_count: int,
        expected_company_count: int,
        expected_charge_count: int
    ) -> bool:
        """Validate database state.
        
        Args:
            db_connection: Database connection
            expected_raw_count: Expected raw transaction count
            expected_company_count: Expected company count
            expected_charge_count: Expected charge count
            
        Returns:
            True if state is valid
        """
        try:
            with db_connection.get_session() as session:
                raw_count = session.query(RawTransaction).count()
                company_count = session.query(Company).count()
                charge_count = session.query(Charge).count()
                
                return (
                    raw_count == expected_raw_count and
                    company_count == expected_company_count and
                    charge_count == expected_charge_count
                )
        except Exception:
            return False