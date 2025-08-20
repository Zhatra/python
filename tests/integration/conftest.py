"""
Configuration and fixtures for integration tests.

This module provides pytest configuration and shared fixtures for
integration testing of the complete data pipeline.
"""

import pytest
import os
import sys
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import fixtures from fixtures module
from tests.integration.fixtures import (
    test_database,
    postgres_test_database,
    file_fixture,
    integration_fixture,
    sample_csv_data,
    large_csv_data,
    invalid_csv_data,
    temp_csv_file,
    large_temp_csv_file,
    invalid_temp_csv_file
)


def pytest_configure(config):
    """Configure pytest for integration tests."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running test"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API integration test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add integration marker to all tests in integration directory
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add performance marker to performance tests
        if "performance" in item.name.lower():
            item.add_marker(pytest.mark.performance)
        
        # Add slow marker to tests that might be slow
        if any(keyword in item.name.lower() for keyword in ["large", "stress", "concurrent"]):
            item.add_marker(pytest.mark.slow)
        
        # Add database marker to tests that use database fixtures
        if any(fixture in item.fixturenames for fixture in ["test_database", "postgres_test_database", "integration_fixture"]):
            item.add_marker(pytest.mark.database)
        
        # Add api marker to API tests
        if "api" in item.name.lower() or "api" in str(item.fspath):
            item.add_marker(pytest.mark.api)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment for integration tests."""
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "WARNING"  # Reduce log noise during tests
    
    # Ensure test directories exist
    test_dirs = [
        "tests/integration/temp",
        "tests/integration/output",
        "data/test_output"
    ]
    
    for test_dir in test_dirs:
        Path(test_dir).mkdir(parents=True, exist_ok=True)
    
    yield
    
    # Cleanup test environment
    # Remove test environment variables
    os.environ.pop("TESTING", None)
    os.environ.pop("LOG_LEVEL", None)


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return {
        "database": {
            "test_host": os.getenv("TEST_DB_HOST", "localhost"),
            "test_port": int(os.getenv("TEST_DB_PORT", "5432")),
            "test_database": os.getenv("TEST_DB_NAME", "test_technical_test"),
            "test_username": os.getenv("TEST_DB_USER", "testuser"),
            "test_password": os.getenv("TEST_DB_PASSWORD", "testpass"),
        },
        "performance": {
            "max_load_time": 30.0,  # seconds
            "max_transform_time": 20.0,  # seconds
            "max_extract_time": 15.0,  # seconds
            "max_api_response_time": 1.0,  # seconds
            "max_memory_usage": 500,  # MB
        },
        "data": {
            "small_dataset_size": 100,
            "medium_dataset_size": 1000,
            "large_dataset_size": 10000,
        }
    }


@pytest.fixture(scope="function")
def cleanup_database_state():
    """Ensure clean database state for each test."""
    # This fixture runs before and after each test
    yield
    
    # Cleanup after test
    # This is handled by individual database fixtures


def pytest_runtest_setup(item):
    """Set up individual test runs."""
    # Skip performance tests if not explicitly requested
    if item.get_closest_marker("performance"):
        if not item.config.getoption("--run-performance", default=False):
            pytest.skip("Performance tests skipped (use --run-performance to run)")
    
    # Skip slow tests if not explicitly requested
    if item.get_closest_marker("slow"):
        if not item.config.getoption("--run-slow", default=False):
            pytest.skip("Slow tests skipped (use --run-slow to run)")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--run-performance",
        action="store_true",
        default=False,
        help="Run performance tests"
    )
    parser.addoption(
        "--run-slow",
        action="store_true", 
        default=False,
        help="Run slow tests"
    )
    parser.addoption(
        "--use-postgres",
        action="store_true",
        default=False,
        help="Use PostgreSQL for database tests instead of SQLite"
    )


@pytest.fixture(scope="function")
def api_client():
    """Provide FastAPI test client for API integration tests."""
    from fastapi.testclient import TestClient
    from src.api.main import app
    
    with TestClient(app) as client:
        # Reset API state before each test
        client.post("/reset")
        yield client


@pytest.fixture(scope="function")
def performance_monitor():
    """Monitor performance metrics during tests."""
    import time
    import psutil
    import os
    
    # Get initial metrics
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    start_time = time.time()
    
    metrics = {
        "start_time": start_time,
        "initial_memory": initial_memory,
        "peak_memory": initial_memory,
        "execution_time": 0
    }
    
    def update_metrics():
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        metrics["peak_memory"] = max(metrics["peak_memory"], current_memory)
        metrics["execution_time"] = time.time() - start_time
        return metrics
    
    # Provide update function to test
    yield update_metrics
    
    # Final metrics update
    final_metrics = update_metrics()
    
    # Log performance metrics if test passes
    print(f"\nPerformance Metrics:")
    print(f"  Execution time: {final_metrics['execution_time']:.2f}s")
    print(f"  Initial memory: {final_metrics['initial_memory']:.2f}MB")
    print(f"  Peak memory: {final_metrics['peak_memory']:.2f}MB")
    print(f"  Memory increase: {final_metrics['peak_memory'] - final_metrics['initial_memory']:.2f}MB")


@pytest.fixture(scope="function")
def test_data_validator():
    """Provide test data validation utilities."""
    from tests.integration.fixtures import TestDataValidator
    return TestDataValidator()


@pytest.fixture(scope="function")
def test_metrics():
    """Provide test metrics utilities."""
    from tests.integration.fixtures import TestMetrics
    return TestMetrics()


# Error handling fixtures
@pytest.fixture(scope="function")
def capture_logs():
    """Capture logs during test execution."""
    import logging
    from io import StringIO
    
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.WARNING)
    
    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    original_level = root_logger.level
    root_logger.setLevel(logging.WARNING)
    
    yield log_capture
    
    # Cleanup
    root_logger.removeHandler(handler)
    root_logger.setLevel(original_level)


# Parametrized fixtures for different test scenarios
@pytest.fixture(params=[10, 100, 1000])
def dataset_sizes(request):
    """Parametrized fixture for different dataset sizes."""
    return request.param


@pytest.fixture(params=["sqlite", "postgres"])
def database_types(request):
    """Parametrized fixture for different database types."""
    if request.param == "postgres" and not request.config.getoption("--use-postgres"):
        pytest.skip("PostgreSQL tests skipped (use --use-postgres to run)")
    return request.param


# Cleanup fixtures
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts():
    """Clean up test artifacts after test session."""
    yield
    
    # Cleanup test directories
    import shutil
    test_cleanup_dirs = [
        "tests/integration/temp",
        "tests/integration/output",
        "data/test_output"
    ]
    
    for cleanup_dir in test_cleanup_dirs:
        if Path(cleanup_dir).exists():
            try:
                shutil.rmtree(cleanup_dir)
            except Exception as e:
                print(f"Warning: Could not cleanup {cleanup_dir}: {e}")


# Custom assertions for integration tests
class IntegrationAssertions:
    """Custom assertions for integration tests."""
    
    @staticmethod
    def assert_pipeline_success(load_report, transform_report, expected_rows):
        """Assert that pipeline completed successfully."""
        assert load_report.total_rows_processed == expected_rows
        assert load_report.validation_report.success_rate == 100.0
        assert transform_report.total_raw_rows == expected_rows
        assert transform_report.transformation_success_rate == 100.0
    
    @staticmethod
    def assert_data_consistency(db_connection, expected_companies, expected_charges):
        """Assert data consistency in database."""
        from src.database.models import Company, Charge
        
        with db_connection.get_session() as session:
            company_count = session.query(Company).count()
            charge_count = session.query(Charge).count()
            
            assert company_count == expected_companies
            assert charge_count == expected_charges
    
    @staticmethod
    def assert_api_response_format(response_data, expected_fields):
        """Assert API response has expected format."""
        for field in expected_fields:
            assert field in response_data, f"Missing field: {field}"
    
    @staticmethod
    def assert_performance_threshold(execution_time, max_time, operation_name):
        """Assert performance is within threshold."""
        assert execution_time <= max_time, (
            f"{operation_name} took {execution_time:.2f}s, "
            f"exceeding threshold of {max_time:.2f}s"
        )


@pytest.fixture(scope="function")
def integration_assertions():
    """Provide integration test assertions."""
    return IntegrationAssertions()