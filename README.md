# Prueba Técnica Python

A comprehensive technical test solution demonstrating advanced data processing capabilities and REST API development skills. This project implements a complete ETL (Extract, Transform, Load) pipeline for transaction data processing and a mathematical algorithm API for solving the missing number problem.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [API Documentation](#api-documentation)
- [Data Processing Pipeline](#data-processing-pipeline)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Development](#development)
- [Docker Deployment](#docker-deployment)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project consists of two main components:

1. **Data Processing Pipeline**: A complete ETL system that processes transaction data from CSV files, transforms it according to business requirements, and stores it in a normalized PostgreSQL database with reporting capabilities.

2. **Missing Number API**: A REST API that implements an efficient algorithm to find missing numbers from the first 100 natural numbers using mathematical sum approach (O(1) complexity).

The solution demonstrates proficiency in:
- Data engineering and ETL processes
- Database design and normalization
- REST API development with FastAPI
- Comprehensive error handling and validation
- Docker containerization and deployment
- Test-driven development with extensive coverage
- Production-ready code with monitoring and logging

## Features

### Data Processing Pipeline
- **CSV Data Loading**: Robust CSV file ingestion with validation and error handling
- **Data Extraction**: Export data to multiple formats (CSV, Parquet) with metadata
- **Data Transformation**: Schema transformation with business rule validation
- **Database Normalization**: Proper relational database design with foreign keys
- **Reporting Views**: SQL views for business analytics and reporting
- **Batch Processing**: Configurable batch sizes for large dataset handling
- **Error Recovery**: Comprehensive error handling with detailed reporting

### Missing Number API
- **Mathematical Algorithm**: O(1) complexity using sum formula approach
- **REST API**: FastAPI with automatic OpenAPI documentation
- **Input Validation**: Comprehensive validation with detailed error messages
- **State Management**: Persistent number set state across API calls
- **Error Handling**: Custom exception hierarchy with structured responses
- **Performance Monitoring**: Request timing and performance metrics
- **Health Checks**: Comprehensive health monitoring endpoints

### Infrastructure & DevOps
- **Docker Containerization**: Multi-service Docker setup with profiles
- **Database Management**: PostgreSQL with connection pooling and transactions
- **Comprehensive Testing**: Unit and integration tests with coverage reporting
- **Logging & Monitoring**: Structured logging with error tracking
- **Documentation**: Extensive documentation with usage examples
- **CI/CD Ready**: Pre-commit hooks and automated testing

## Project Structure

```
prueba-tecnica-python/
├── src/
│   ├── api/                    # FastAPI application
│   ├── data_processing/        # Data processing pipeline
│   ├── database/              # Database utilities
│   └── config.py              # Configuration management
├── tests/
│   ├── unit/                  # Unit tests
│   └── integration/           # Integration tests
├── data/
│   ├── input/                 # Input data files
│   └── output/                # Output data files
├── scripts/                   # Utility scripts
├── docker-compose.yml         # Docker services configuration
├── Dockerfile                 # Container configuration
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Features

### Data Processing Pipeline
- CSV data loading into PostgreSQL database
- Data extraction to CSV and Parquet formats
- Data transformation to match business schema
- Normalized database structure with proper relationships
- SQL reporting views for business analytics

### Missing Number API
- REST API to solve the missing number problem
- Efficient algorithm using mathematical approach (O(1) complexity)
- Input validation and comprehensive error handling
- FastAPI with automatic OpenAPI documentation
- Complete test coverage with unit and integration tests

## Quick Start

### Prerequisites
- Python 3.9+
- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd prueba-tecnica-python
   ```

2. **Set up Python virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

### Running with Docker (Recommended)

1. **Validate Docker setup**
   ```bash
   ./scripts/validate-docker.sh
   ```

2. **Deploy development environment**
   ```bash
   ./scripts/deploy.sh
   ```

3. **Access the application**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

#### Alternative Docker Commands

For more control, use individual profiles:

```bash
# Start only API service
docker-compose --profile api up -d

# Start only data processing service
docker-compose --profile data-processing up -d

# Start development environment with hot reload
docker-compose --profile dev up -d
```

#### Docker Management

```bash
# Check service status
./scripts/docker-manage.sh status

# View logs
./scripts/docker-manage.sh logs api

# Stop services
./scripts/docker-manage.sh stop dev
```

For complete deployment documentation, see [DEPLOYMENT.md](DEPLOYMENT.md).

### Running Locally

1. **Start PostgreSQL database**
   ```bash
   docker-compose up database -d
   ```

2. **Run data processing**
   ```bash
   python -m src.data_processing.main
   ```

3. **Start the API**
   ```bash
   uvicorn src.api.main:app --reload
   ```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest tests/unit/
pytest tests/integration/
```

## Development

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

### Pre-commit Hooks
```bash
pre-commit install
pre-commit run --all-files
```

## API Documentation

### Starting the API Server

The Missing Number API can be started in several ways:

```bash
# Using the deployment script (recommended)
./scripts/deploy.sh --profile api

# Using Docker Compose directly
docker-compose --profile api up -d

# For development with hot reload
docker-compose --profile dev up -d

# Running locally (requires PostgreSQL)
python scripts/run_api.py

# Using make commands
make dev-api

# Direct uvicorn command
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### API Access Points

Once running, the API is available at:
- **API Base URL**: http://localhost:8000
- **Interactive Documentation (Swagger)**: http://localhost:8000/docs
- **Alternative Documentation (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health
- **API Status**: http://localhost:8000/status

### API Endpoints

The Missing Number API provides the following endpoints:

#### Core Functionality

#### Missing Number API

**POST /extract/{number}**
- Extract (remove) a specific number from the set of 1-100
- **Parameters**: `number` (path parameter, integer 1-100)
- **Response**: Success status, extracted number, remaining count
- **Example**:
  ```bash
  curl -X POST "http://localhost:8000/extract/42"
  ```
  ```json
  {
    "success": true,
    "message": "Successfully extracted number 42",
    "extracted_number": 42,
    "remaining_count": 99
  }
  ```

**GET /missing**
- Calculate and return the missing number from the set
- **Requirements**: Exactly one number must be extracted
- **Response**: Missing number, calculation method, execution time
- **Example**:
  ```bash
  curl "http://localhost:8000/missing"
  ```
  ```json
  {
    "missing_number": 42,
    "calculation_method": "mathematical_sum",
    "execution_time_ms": 0.15,
    "extracted_numbers": [42]
  }
  ```

**POST /reset**
- Reset the number set to contain all numbers 1-100
- **Response**: Success status and total count
- **Example**:
  ```bash
  curl -X POST "http://localhost:8000/reset"
  ```
  ```json
  {
    "success": true,
    "message": "Number set has been reset to contain all numbers from 1 to 100",
    "total_numbers": 100
  }
  ```

**GET /status**
- Get current status of the number set
- **Response**: Current state information
- **Example**:
  ```bash
  curl "http://localhost:8000/status"
  ```
  ```json
  {
    "total_numbers": 100,
    "remaining_count": 99,
    "extracted_count": 1,
    "extracted_numbers": [42],
    "is_complete": false
  }
  ```

**GET /health**
- Health check endpoint
- **Response**: Service health status

### API Demo Scripts

```bash
# Interactive CLI demo (no API server required)
python scripts/cli_demo.py --interactive

# CLI demo with specific extraction
python scripts/cli_demo.py --extract 42

# Full API demo (requires running API server)
python scripts/demo_api.py

# Using make commands
make demo-cli          # Interactive CLI
make demo-cli-extract  # CLI with extraction
make demo-api          # Full API demo
```

### Error Handling

The API provides comprehensive error handling with structured responses:

- **400 Bad Request**: Invalid input (number out of range, invalid format)
- **409 Conflict**: Business logic violations (number already extracted)
- **422 Unprocessable Entity**: Request validation errors
- **500 Internal Server Error**: Unexpected server errors

Example error responses:
```json
{
  "error": "NUMBER_OUT_OF_RANGE",
  "message": "Number 150 is outside valid range (1-100)",
  "details": {
    "provided_number": 150,
    "valid_range": "1-100"
  }
}
```

```json
{
  "error": "NUMBER_ALREADY_EXTRACTED",
  "message": "Number 42 has already been extracted",
  "details": {
    "extracted_number": 42,
    "extraction_time": "2024-01-15T10:30:00Z"
  }
}
```

## Data Processing Pipeline

The data processing pipeline implements a complete ETL (Extract, Transform, Load) system for transaction data.

### Pipeline Components

#### 1. Data Loader (`src/data_processing/loader.py`)
Handles CSV file ingestion with comprehensive validation:

```bash
# Load CSV data into database
python scripts/demo_data_loader.py

# Using the data loader directly
from src.data_processing.loader import DataLoader
loader = DataLoader()
result = loader.load_csv_to_database("data/input/data_prueba_técnica.csv")
```

**Features:**
- CSV format validation and parsing
- Data type validation and conversion
- Duplicate detection and handling
- Comprehensive error reporting
- Batch processing for large files
- Transaction safety with rollback

#### 2. Data Extractor (`src/data_processing/extractor.py`)
Exports data from database to various formats:

```bash
# Extract data to CSV
python scripts/demo_data_extractor.py --format csv

# Extract data to Parquet
python scripts/demo_data_extractor.py --format parquet

# Using the extractor directly
from src.data_processing.extractor import DataExtractor
extractor = DataExtractor()
extractor.extract_to_csv("data/output/extracted_data.csv")
extractor.extract_to_parquet("data/output/extracted_data.parquet")
```

**Features:**
- Multiple export formats (CSV, Parquet)
- Query optimization for large datasets
- Metadata generation and statistics
- Configurable batch processing
- Data integrity verification

#### 3. Data Transformer (`src/data_processing/transformer.py`)
Transforms data to match target business schema:

```bash
# Transform data to target schema
python scripts/demo_data_transformer.py

# Using the transformer directly
from src.data_processing.transformer import DataTransformer
transformer = DataTransformer("data/output/extracted_data.csv")
transformed_data = transformer.transform_to_schema()
```

**Features:**
- Schema transformation and validation
- Data type conversion (varchar, decimal, timestamp)
- Business rule application
- Data cleaning and normalization
- Quality validation and reporting

#### 4. Database Manager (`src/database/manager.py`)
Manages database schema and data distribution:

```bash
# Create normalized schema
python scripts/demo_schema_creation.py

# Create reporting views
python scripts/demo_reporting_views.py

# Using the database manager
from src.database.manager import DatabaseManager
db_manager = DatabaseManager()
db_manager.create_normalized_schema()
db_manager.create_reporting_view()
```

**Features:**
- Normalized schema creation
- Data distribution to related tables
- Foreign key relationship management
- Reporting view creation
- Index optimization

### Pipeline Execution

#### Complete Pipeline Run
```bash
# Run complete ETL pipeline
python scripts/run_complete_pipeline.py

# Or using make
make run-pipeline

# Step by step execution
make load-data
make extract-data
make transform-data
make create-schema
make create-views
```

#### Pipeline Configuration
Configure pipeline behavior via environment variables:
```env
# Data processing settings
BATCH_SIZE=1000
MAX_WORKERS=4
VALIDATION_LEVEL=strict
ERROR_THRESHOLD=0.05

# File paths
INPUT_DATA_PATH=data/input/data_prueba_técnica.csv
OUTPUT_DATA_PATH=data/output/
```

### Data Quality and Validation

The pipeline includes comprehensive data quality checks:

- **Format Validation**: CSV structure and encoding
- **Type Validation**: Data type consistency and conversion
- **Business Rules**: Amount ranges, status values, date consistency
- **Referential Integrity**: Foreign key relationships
- **Duplicate Detection**: Identification and handling of duplicates
- **Completeness Checks**: Required field validation

## Database Schema

### Architecture Overview

The database uses a two-schema approach:
- **raw_data**: Initial data loading and staging
- **normalized_data**: Business-ready normalized tables

### Raw Data Schema (`raw_data`)

#### `raw_transactions` Table
Initial staging table for CSV data ingestion:

```sql
CREATE TABLE raw_data.raw_transactions (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(130),
    company_id VARCHAR(64),
    amount DECIMAL(16,2),
    status VARCHAR(50),
    created_at VARCHAR(50),
    paid_at VARCHAR(50),
    loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Normalized Schema (`normalized_data`)

#### `companies` Table
Master table for company information:

```sql
CREATE TABLE normalized_data.companies (
    company_id VARCHAR(24) PRIMARY KEY,
    company_name VARCHAR(130) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes
    INDEX idx_company_name (company_name),
    INDEX idx_company_created (created_at)
);
```

#### `charges` Table
Transaction charges with proper relationships:

```sql
CREATE TABLE normalized_data.charges (
    id VARCHAR(24) PRIMARY KEY,
    company_id VARCHAR(24) NOT NULL,
    amount DECIMAL(16,2) NOT NULL,
    status VARCHAR(30) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NULL,
    
    -- Foreign key constraints
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    
    -- Indexes
    INDEX idx_charges_company (company_id),
    INDEX idx_charges_status (status),
    INDEX idx_charges_created (created_at),
    INDEX idx_charges_amount (amount)
);
```

#### `daily_transaction_summary` View
Business reporting view for analytics:

```sql
CREATE VIEW normalized_data.daily_transaction_summary AS
SELECT 
    DATE(c.created_at) as transaction_date,
    comp.company_name,
    comp.company_id,
    SUM(c.amount) as total_amount,
    COUNT(*) as transaction_count,
    AVG(c.amount) as average_amount,
    MIN(c.amount) as min_amount,
    MAX(c.amount) as max_amount,
    COUNT(CASE WHEN c.status = 'paid' THEN 1 END) as paid_count,
    COUNT(CASE WHEN c.status = 'refunded' THEN 1 END) as refunded_count
FROM normalized_data.charges c
JOIN normalized_data.companies comp ON c.company_id = comp.company_id
WHERE c.status IN ('paid', 'refunded')
GROUP BY DATE(c.created_at), comp.company_id, comp.company_name
ORDER BY transaction_date DESC, total_amount DESC;
```

### Database Design Decisions

#### PostgreSQL Selection Rationale
- **ACID Compliance**: Strong transaction guarantees for financial data
- **JSON Support**: Flexible data handling for future requirements
- **Performance**: Excellent analytical query performance
- **Indexing**: Advanced indexing capabilities for reporting
- **Scalability**: Horizontal and vertical scaling options
- **Community**: Strong ecosystem and community support

#### Normalization Strategy
- **Third Normal Form (3NF)**: Eliminates data redundancy
- **Foreign Key Constraints**: Ensures referential integrity
- **Proper Indexing**: Optimized for both OLTP and OLAP workloads
- **View-Based Reporting**: Simplified business intelligence queries

#### Data Types and Constraints
- **VARCHAR with Limits**: Prevents data overflow and ensures consistency
- **DECIMAL for Money**: Precise financial calculations without floating-point errors
- **TIMESTAMP with Timezone**: Proper temporal data handling
- **NOT NULL Constraints**: Data quality enforcement
- **Check Constraints**: Business rule validation at database level

## Configuration

### Environment Variables

The application uses environment variables for configuration. Copy `.env.example` to `.env` and modify as needed:

```bash
cp .env.example .env
```

#### Database Configuration
```env
# PostgreSQL Database Settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=prueba_tecnica
DB_USER=testuser
DB_PASSWORD=testpass
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

#### API Configuration
```env
# FastAPI Server Settings
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
API_RELOAD=true
```

#### Application Settings
```env
# General Application Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development
DEBUG=false
```

#### Data Processing Settings
```env
# ETL Pipeline Configuration
BATCH_SIZE=1000
MAX_WORKERS=4
VALIDATION_LEVEL=strict
ERROR_THRESHOLD=0.05
CHUNK_SIZE=10000
```

#### File Paths
```env
# Data File Locations
INPUT_DATA_PATH=data/input/data_prueba_técnica.csv
OUTPUT_DATA_PATH=data/output/
BACKUP_PATH=backups/
LOG_PATH=logs/
```

#### Docker Configuration
```env
# Docker-specific Settings
COMPOSE_PROJECT_NAME=prueba_tecnica
POSTGRES_DB=prueba_tecnica
POSTGRES_USER=testuser
POSTGRES_PASSWORD=testpass
```

### Configuration Validation

Validate your configuration before running:

```bash
# Validate environment configuration
python scripts/validate_config.py

# Check database connectivity
python scripts/check_database.py

# Validate Docker setup
./scripts/validate-docker.sh
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Issues

**Problem**: Cannot connect to PostgreSQL database
```
DatabaseConnectionError: could not connect to server: Connection refused
```

**Solutions**:
```bash
# Check if PostgreSQL is running
docker-compose ps database

# Restart database service
docker-compose restart database

# Check database logs
docker-compose logs database

# Verify connection parameters
python scripts/check_database.py

# Test connection manually
psql -h localhost -p 5432 -U testuser -d prueba_tecnica
```

#### 2. Port Already in Use

**Problem**: API port 8000 is already in use
```
OSError: [Errno 48] Address already in use
```

**Solutions**:
```bash
# Find process using the port
lsof -i :8000

# Kill the process (replace PID)
kill -9 <PID>

# Use different port
echo "API_PORT=8001" >> .env

# Or use Docker which handles port conflicts
./scripts/deploy.sh
```

#### 3. CSV File Not Found

**Problem**: Input CSV file cannot be found
```
FileNotFoundError: data/input/data_prueba_técnica.csv not found
```

**Solutions**:
```bash
# Check file exists
ls -la data/input/

# Download sample data (if available)
curl -o data/input/data_prueba_técnica.csv <data-url>

# Use custom file path
export INPUT_DATA_PATH=/path/to/your/file.csv
python scripts/demo_data_loader.py
```

#### 4. Docker Build Failures

**Problem**: Docker build fails with dependency errors
```
ERROR: Could not find a version that satisfies the requirement
```

**Solutions**:
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
./scripts/deploy.sh --fresh

# Check Docker version
docker --version
docker-compose --version

# Update base images
docker-compose pull
```

#### 5. Permission Denied Errors

**Problem**: Permission denied when accessing files or directories
```
PermissionError: [Errno 13] Permission denied
```

**Solutions**:
```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Make scripts executable
chmod +x scripts/*.sh

# Fix data directory permissions
chmod -R 755 data/
```

#### 6. Memory or Performance Issues

**Problem**: Application runs slowly or runs out of memory
```
MemoryError: Unable to allocate memory
```

**Solutions**:
```bash
# Reduce batch size
echo "BATCH_SIZE=500" >> .env

# Limit workers
echo "MAX_WORKERS=2" >> .env

# Monitor resource usage
docker stats

# Increase Docker memory limits (Docker Desktop)
# Settings > Resources > Memory > Increase limit
```

### Debugging Commands

#### Application Debugging
```bash
# Run with debug logging
LOG_LEVEL=DEBUG python scripts/run_api.py

# Check application health
curl http://localhost:8000/health

# View error summary
curl http://localhost:8000/errors/summary

# Monitor API logs
tail -f logs/api.log
```

#### Database Debugging
```bash
# Connect to database
docker-compose exec database psql -U testuser -d prueba_tecnica

# Check table contents
docker-compose exec database psql -U testuser -d prueba_tecnica -c "SELECT COUNT(*) FROM raw_data.raw_transactions;"

# View database logs
docker-compose logs database

# Check database performance
docker-compose exec database psql -U testuser -d prueba_tecnica -c "SELECT * FROM pg_stat_activity;"
```

#### Docker Debugging
```bash
# Check container status
docker-compose ps

# View all logs
docker-compose logs -f

# Execute commands in container
docker-compose exec api bash

# Check container resource usage
docker stats

# Inspect container configuration
docker inspect prueba_tecnica_api_1
```

### Performance Optimization

#### Database Optimization
```sql
-- Create additional indexes for better performance
CREATE INDEX CONCURRENTLY idx_charges_created_status ON normalized_data.charges(created_at, status);
CREATE INDEX CONCURRENTLY idx_charges_amount_desc ON normalized_data.charges(amount DESC);

-- Analyze tables for query optimization
ANALYZE normalized_data.charges;
ANALYZE normalized_data.companies;
```

#### Application Optimization
```env
# Optimize for production
ENVIRONMENT=production
LOG_LEVEL=WARNING
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
BATCH_SIZE=2000
MAX_WORKERS=8
```

### Getting Help

If you encounter issues not covered here:

1. **Check Logs**: Always start by checking application and container logs
2. **Validate Configuration**: Ensure all environment variables are set correctly
3. **Test Components**: Use the demo scripts to test individual components
4. **Check Dependencies**: Verify all prerequisites are installed and up to date
5. **Review Documentation**: Check the specific component documentation
6. **Create Issue**: If the problem persists, create an issue with:
   - Error messages and stack traces
   - Environment details (OS, Docker version, etc.)
   - Steps to reproduce the issue
   - Configuration files (without sensitive data)

### Monitoring and Maintenance

#### Health Monitoring
```bash
# Check API health
curl http://localhost:8000/health

# Monitor error rates
curl http://localhost:8000/errors/summary

# Check database connectivity
python scripts/check_database.py
```

#### Log Management
```bash
# Rotate logs
find logs/ -name "*.log" -mtime +7 -delete

# Monitor log size
du -sh logs/

# View recent errors
tail -n 100 logs/api.log | grep ERROR
```

#### Backup and Recovery
```bash
# Backup database
./scripts/docker-manage.sh backup

# List available backups
ls -la backups/

# Restore from backup
./scripts/docker-manage.sh restore backups/backup_20240115_120000.sql
```

## Contributing

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone <your-fork-url>
   cd prueba-tecnica-python
   ```

2. **Set Up Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Install Pre-commit Hooks**
   ```bash
   pre-commit install
   ```

4. **Run Tests**
   ```bash
   pytest --cov=src --cov-report=html
   ```

### Code Standards

- **Python Style**: Follow PEP 8 with Black formatting
- **Type Hints**: Use type hints for all function signatures
- **Docstrings**: Google-style docstrings for all modules, classes, and functions
- **Testing**: Maintain >90% test coverage
- **Error Handling**: Use custom exceptions with proper error messages
- **Logging**: Use structured logging with appropriate levels

### Submitting Changes

1. Create a feature branch
2. Make your changes with tests
3. Run the full test suite
4. Update documentation if needed
5. Submit a pull request with clear description

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- FastAPI for the excellent web framework
- PostgreSQL for robust database capabilities
- Docker for containerization support
- pytest for comprehensive testing framework