# Integration Tests

This directory contains comprehensive integration tests for the complete data pipeline and API functionality.

## Overview

The integration tests verify the complete workflows and interactions between different components of the system:

1. **Complete Data Pipeline Tests** - End-to-end testing of CSV loading, transformation, and database operations
2. **API Workflow Tests** - Complete API workflows with NumberSet operations
3. **Performance Tests** - Performance testing with large datasets
4. **Error Scenarios** - Integration testing of error handling and recovery

## Test Structure

### Core Test Files

- `test_complete_pipeline.py` - End-to-end data pipeline integration tests
- `test_api_workflow.py` - Complete API workflow integration tests
- `test_api_integration.py` - Existing API integration tests
- `test_data_loader_integration.py` - Existing data loader integration tests
- `test_error_scenarios.py` - Existing error scenario tests

### Supporting Files

- `fixtures.py` - Reusable test fixtures and utilities
- `conftest.py` - Pytest configuration and shared fixtures
- `run_integration_tests.py` - Test runner script with various options

## Test Categories

### 1. Complete Pipeline Integration Tests

**File**: `test_complete_pipeline.py`

**Test Classes**:
- `TestCompletePipelineIntegration` - End-to-end pipeline tests
- `TestPipelinePerformance` - Performance tests for large datasets

**Key Tests**:
- `test_end_to_end_csv_to_normalized_database` - Complete CSV to normalized DB workflow
- `test_data_extraction_and_transformation_flow` - Data extraction and transformation
- `test_data_consistency_across_pipeline_stages` - Data consistency validation
- `test_pipeline_error_handling_and_recovery` - Error handling and recovery
- `test_pipeline_with_duplicate_data` - Duplicate data handling
- `test_pipeline_transaction_integrity` - Transaction integrity
- `test_pipeline_metadata_and_audit_trail` - Metadata and audit trail

**Performance Tests**:
- `test_large_dataset_loading_performance` - Loading performance with 1000+ rows
- `test_transformation_performance` - Transformation performance testing
- `test_extraction_performance` - Extraction performance testing
- `test_memory_usage_with_large_dataset` - Memory usage monitoring

### 2. API Workflow Integration Tests

**File**: `test_api_workflow.py`

**Test Classes**:
- `TestAPIWorkflowIntegration` - Complete API workflows
- `TestNumberSetIntegration` - NumberSet class integration
- `TestAPIIntegrationWithRealScenarios` - Real-world scenarios

**Key Tests**:
- `test_complete_single_number_workflow` - Single number extraction workflow
- `test_multiple_extractions_workflow` - Multiple number extractions
- `test_error_recovery_workflow` - Error recovery and continued functionality
- `test_boundary_values_workflow` - Boundary value testing
- `test_performance_workflow` - API performance testing
- `test_concurrent_api_access` - Concurrent access testing
- `test_api_state_persistence_across_requests` - State persistence
- `test_complete_user_scenario_workflow` - End-to-end user scenarios

**NumberSet Integration**:
- `test_number_set_mathematical_correctness` - Mathematical correctness
- `test_number_set_edge_cases` - Edge cases and boundary conditions
- `test_number_set_state_consistency` - State consistency
- `test_number_set_performance_characteristics` - Performance characteristics
- `test_number_set_memory_efficiency` - Memory efficiency

**Real Scenarios**:
- `test_demo_scenario_workflow` - Demo scenario as per requirements
- `test_multiple_demo_runs` - Multiple demo runs with different numbers
- `test_error_handling_in_demo_scenario` - Error handling in demos
- `test_api_robustness_under_stress` - Stress testing

### 3. Test Fixtures and Utilities

**File**: `fixtures.py`

**Key Components**:
- `TestDataGenerator` - Generates test data for various scenarios
- `DatabaseTestFixture` - Database setup and cleanup
- `FileTestFixture` - File operations and cleanup
- `IntegrationTestFixture` - Combined fixture for integration tests
- `TestMetrics` - Performance and metrics utilities
- `TestDataValidator` - Data validation utilities

**Pytest Fixtures**:
- `test_database` - In-memory database for testing
- `postgres_test_database` - PostgreSQL test database
- `file_fixture` - File operations fixture
- `integration_fixture` - Complete integration fixture
- `sample_csv_data` - Sample CSV data
- `large_csv_data` - Large CSV data for performance testing
- `temp_csv_file` - Temporary CSV file

### 4. Test Configuration

**File**: `conftest.py`

**Features**:
- Custom pytest markers (integration, performance, slow, database, api)
- Test environment setup
- Performance monitoring
- Error handling fixtures
- Custom assertions for integration tests

**Markers**:
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.performance` - Performance tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.database` - Database-dependent tests
- `@pytest.mark.api` - API tests

## Running Integration Tests

### Using the Test Runner

The `run_integration_tests.py` script provides various options for running tests:

```bash
# Run basic integration tests
python tests/integration/run_integration_tests.py

# Run all tests including performance
python tests/integration/run_integration_tests.py --all

# Run only performance tests
python tests/integration/run_integration_tests.py --performance

# Run only API tests
python tests/integration/run_integration_tests.py --api

# Run only pipeline tests
python tests/integration/run_integration_tests.py --pipeline

# Run with coverage report
python tests/integration/run_integration_tests.py --coverage

# Run with HTML report
python tests/integration/run_integration_tests.py --html-report

# Use PostgreSQL instead of SQLite
python tests/integration/run_integration_tests.py --postgres

# Run in parallel
python tests/integration/run_integration_tests.py --parallel 4
```

### Using Make Commands

```bash
# Run basic integration tests
make test-integration

# Run all integration tests including performance
make test-integration-full

# Run performance tests only
make test-integration-performance

# Run API integration tests only
make test-integration-api

# Run pipeline integration tests only
make test-integration-pipeline

# Run integration tests with coverage
make test-coverage-integration
```

### Using Pytest Directly

```bash
# Run all integration tests
pytest tests/integration/

# Run specific test file
pytest tests/integration/test_api_workflow.py

# Run with specific markers
pytest -m "integration and not slow"
pytest -m "performance"
pytest -m "api"

# Run with coverage
pytest tests/integration/ --cov=src --cov-report=html

# Run specific test
pytest tests/integration/test_api_workflow.py::TestAPIWorkflowIntegration::test_complete_single_number_workflow
```

## Test Data

### Sample Data Generation

The `TestDataGenerator` class provides methods to generate various types of test data:

- `generate_csv_data()` - Generate valid CSV data
- `generate_invalid_csv_data()` - Generate CSV data with validation errors
- `generate_large_csv_data()` - Generate large datasets for performance testing

### Test Database

Tests use either:
- **SQLite in-memory database** (default) - Fast, no setup required
- **PostgreSQL test database** - More realistic, requires setup

## Performance Testing

Performance tests are marked with `@pytest.mark.performance` and include:

- **Loading Performance** - CSV loading with large datasets
- **Transformation Performance** - Data transformation speed
- **Extraction Performance** - Data extraction speed
- **Memory Usage** - Memory consumption monitoring
- **API Performance** - API response times and throughput

Performance thresholds are configurable in `conftest.py`.

## Error Scenarios

Integration tests include comprehensive error scenario testing:

- **Database Connection Errors** - Connection failures and recovery
- **Data Validation Errors** - Invalid data handling
- **API Error Handling** - API error responses and recovery
- **File System Errors** - File operation failures
- **Concurrent Access** - Race conditions and thread safety

## Continuous Integration

The tests are designed to work in CI environments:

- **JUnit XML Reports** - For CI integration
- **Coverage Reports** - HTML and XML formats
- **Performance Metrics** - Execution time and memory usage
- **Parallel Execution** - Support for parallel test execution

## Configuration

### Environment Variables

- `TEST_DB_HOST` - Test database host (default: localhost)
- `TEST_DB_PORT` - Test database port (default: 5432)
- `TEST_DB_NAME` - Test database name (default: test_technical_test)
- `TEST_DB_USER` - Test database user (default: testuser)
- `TEST_DB_PASSWORD` - Test database password (default: testpass)
- `TESTING` - Set to "true" during test execution
- `LOG_LEVEL` - Log level during tests (default: WARNING)

### Test Configuration

The `test_config` fixture provides configuration for:

- **Database Settings** - Connection parameters
- **Performance Thresholds** - Maximum execution times and memory usage
- **Data Settings** - Dataset sizes for different test scenarios

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Ensure PostgreSQL is running if using `--postgres`
   - Check environment variables for database configuration
   - Use SQLite in-memory database for local testing

2. **Performance Test Failures**
   - Performance tests may fail on slower systems
   - Adjust thresholds in `conftest.py`
   - Use `--run-performance` flag to run performance tests

3. **Memory Issues**
   - Large dataset tests may consume significant memory
   - Monitor system resources during testing
   - Adjust dataset sizes if needed

### Debug Mode

Run tests with verbose output for debugging:

```bash
pytest tests/integration/ -v -s --tb=long
```

## Contributing

When adding new integration tests:

1. **Use Appropriate Fixtures** - Leverage existing fixtures from `fixtures.py`
2. **Add Proper Markers** - Use pytest markers for categorization
3. **Include Cleanup** - Ensure proper cleanup of resources
4. **Document Tests** - Add clear docstrings and comments
5. **Performance Considerations** - Mark slow tests appropriately
6. **Error Handling** - Test both success and failure scenarios

## Test Coverage

Integration tests aim to cover:

- **End-to-End Workflows** - Complete user scenarios
- **Component Interactions** - Integration between modules
- **Error Handling** - Error scenarios and recovery
- **Performance** - System performance under load
- **Data Integrity** - Data consistency across operations
- **State Management** - State persistence and transitions

The integration tests complement unit tests by focusing on system-level behavior and interactions rather than individual component functionality.