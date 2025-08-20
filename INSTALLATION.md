# Installation Guide

## Overview

This guide provides comprehensive installation instructions for the Prueba Técnica Python project. The project can be installed and run in multiple ways: using Docker (recommended), local Python installation, or development setup.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start (Docker)](#quick-start-docker)
- [Local Installation](#local-installation)
- [Development Setup](#development-setup)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows 10/11
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: At least 2GB free disk space
- **Network**: Internet connection for downloading dependencies

### Required Software

#### For Docker Installation (Recommended)
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: For cloning the repository

#### For Local Installation
- **Python**: Version 3.9 or higher
- **PostgreSQL**: Version 12 or higher
- **Git**: For cloning the repository

### Installation of Prerequisites

#### Docker Installation

**Linux (Ubuntu/Debian):**
```bash
# Update package index
sudo apt update

# Install Docker
sudo apt install docker.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, then verify
docker --version
docker compose version
```

**macOS:**
```bash
# Using Homebrew
brew install --cask docker

# Or download Docker Desktop from https://docker.com
# Verify installation
docker --version
docker compose version
```

**Windows:**
```powershell
# Download and install Docker Desktop from https://docker.com
# After installation, verify in PowerShell:
docker --version
docker compose version
```

#### Python Installation

**Linux (Ubuntu/Debian):**
```bash
# Install Python 3.9+
sudo apt update
sudo apt install python3.9 python3.9-venv python3.9-dev python3-pip

# Verify installation
python3.9 --version
pip3 --version
```

**macOS:**
```bash
# Using Homebrew
brew install python@3.9

# Or download from https://python.org
# Verify installation
python3 --version
pip3 --version
```

**Windows:**
```powershell
# Download Python from https://python.org
# During installation, check "Add Python to PATH"
# Verify in PowerShell:
python --version
pip --version
```

#### PostgreSQL Installation (Local Setup Only)

**Linux (Ubuntu/Debian):**
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
CREATE DATABASE prueba_tecnica;
CREATE USER testuser WITH PASSWORD 'testpass';
GRANT ALL PRIVILEGES ON DATABASE prueba_tecnica TO testuser;
\q
```

**macOS:**
```bash
# Using Homebrew
brew install postgresql

# Start PostgreSQL service
brew services start postgresql

# Create database and user
psql postgres
CREATE DATABASE prueba_tecnica;
CREATE USER testuser WITH PASSWORD 'testpass';
GRANT ALL PRIVILEGES ON DATABASE prueba_tecnica TO testuser;
\q
```

**Windows:**
```powershell
# Download PostgreSQL from https://postgresql.org
# Follow installation wizard
# Use pgAdmin or psql to create database and user
```

## Quick Start (Docker)

This is the recommended installation method as it handles all dependencies automatically.

### Step 1: Clone Repository

```bash
# Clone the repository
git clone <repository-url>
cd prueba-tecnica-python

# Verify files
ls -la
```

### Step 2: Validate Docker Setup

```bash
# Run validation script
./scripts/validate-docker.sh

# If validation passes, continue to next step
```

### Step 3: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration if needed (optional)
nano .env
```

### Step 4: Deploy Application

```bash
# Deploy complete development environment
./scripts/deploy.sh

# Or deploy specific profile
./scripts/deploy.sh --profile api
```

### Step 5: Verify Installation

```bash
# Check service status
docker-compose ps

# Test API health
curl http://localhost:8000/health

# View logs
docker-compose logs api
```

### Alternative Docker Commands

```bash
# Start development environment with hot reload
docker-compose --profile dev up -d

# Start only API service
docker-compose --profile api up -d

# Start only data processing service
docker-compose --profile data-processing up -d

# View all services
docker-compose ps

# Stop all services
docker-compose down
```

## Local Installation

For development or when Docker is not available, you can install the project locally.

### Step 1: Clone Repository

```bash
git clone <repository-url>
cd prueba-tecnica-python
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Verify activation
which python  # Should show path to venv
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Verify installation
pip list
```

### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration for local setup
nano .env
```

Update the `.env` file with your local PostgreSQL settings:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=prueba_tecnica
DB_USER=testuser
DB_PASSWORD=testpass
API_HOST=localhost
API_PORT=8000
```

### Step 5: Initialize Database

```bash
# Run database initialization script
python scripts/init_database.py

# Verify database connection
python scripts/check_database.py
```

### Step 6: Run Application

```bash
# Start API server
python scripts/run_api.py

# Or use uvicorn directly
uvicorn src.api.main:app --reload --host localhost --port 8000
```

### Step 7: Test Installation

```bash
# Test API in another terminal
curl http://localhost:8000/health

# Run demo scripts
python scripts/demo_api.py
python scripts/cli_demo.py
```

## Development Setup

For contributors and developers who want to modify the code.

### Step 1: Complete Local Installation

Follow the [Local Installation](#local-installation) steps first.

### Step 2: Install Development Dependencies

```bash
# Install development and testing dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Step 3: Configure IDE

#### VS Code Configuration

Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true
    }
}
```

#### PyCharm Configuration

1. Open project in PyCharm
2. Go to File → Settings → Project → Python Interpreter
3. Select the virtual environment: `./venv/bin/python`
4. Configure code style to use Black formatter
5. Enable pytest as test runner

### Step 4: Verify Development Setup

```bash
# Run code formatting
black src/ tests/

# Run linting
flake8 src/ tests/

# Run type checking
mypy src/

# Run tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html
```

### Step 5: Development Workflow

```bash
# Start development environment
docker-compose --profile dev up -d

# Or run locally with hot reload
uvicorn src.api.main:app --reload

# Run tests continuously
pytest-watch

# Check code quality before commit
pre-commit run --all-files
```

## Configuration

### Environment Variables

The application uses environment variables for configuration. Create a `.env` file based on `.env.example`:

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
# General Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development
BATCH_SIZE=1000
MAX_WORKERS=4
```

#### File Paths
```env
# Data Directories
INPUT_DATA_PATH=data/input
OUTPUT_DATA_PATH=data/output
BACKUP_PATH=backups
LOG_PATH=logs
```

### Configuration Validation

```bash
# Validate configuration
python -c "from src.config import validate_all_configs; validate_all_configs()"

# Print configuration summary
python -c "from src.config import print_config_summary; print_config_summary()"
```

## Verification

### Health Checks

```bash
# API health check
curl http://localhost:8000/health

# Database connectivity
python scripts/check_database.py

# Docker services status
docker-compose ps
```

### Functional Tests

```bash
# Run API demo
python scripts/demo_api.py

# Run CLI demo
python scripts/cli_demo.py

# Run data processing demo
python scripts/demo_data_loader.py
python scripts/demo_data_extractor.py
python scripts/demo_data_transformer.py
```

### Test Suite

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test categories
pytest tests/unit/
pytest tests/integration/

# Run performance tests
pytest tests/performance/ -v
```

### Load Testing

```bash
# Install load testing tools
pip install locust

# Run load tests
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## Troubleshooting

### Common Issues

#### Docker Issues

**Problem**: Docker daemon not running
```bash
# Linux
sudo systemctl start docker

# macOS
open -a Docker

# Windows
# Start Docker Desktop application
```

**Problem**: Permission denied for Docker
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
# Log out and back in
```

**Problem**: Port already in use
```bash
# Find process using port
lsof -i :8000

# Kill process or change port in .env
echo "API_PORT=8001" >> .env
```

#### Python Issues

**Problem**: Python version too old
```bash
# Check Python version
python --version

# Install newer Python version
# Follow Python installation instructions above
```

**Problem**: Virtual environment issues
```bash
# Remove and recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Problem**: Package installation failures
```bash
# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Clear pip cache
pip cache purge

# Install with no cache
pip install --no-cache-dir -r requirements.txt
```

#### Database Issues

**Problem**: PostgreSQL connection refused
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# Start PostgreSQL
sudo systemctl start postgresql  # Linux
brew services start postgresql  # macOS
```

**Problem**: Authentication failed
```bash
# Reset PostgreSQL password
sudo -u postgres psql
ALTER USER testuser PASSWORD 'newpassword';
\q

# Update .env file with new password
```

**Problem**: Database does not exist
```bash
# Create database
sudo -u postgres createdb prueba_tecnica
# Or use psql
sudo -u postgres psql
CREATE DATABASE prueba_tecnica;
\q
```

### Getting Help

If you encounter issues not covered here:

1. **Check Logs**: 
   ```bash
   # Application logs
   tail -f logs/api.log
   
   # Docker logs
   docker-compose logs api
   docker-compose logs database
   ```

2. **Validate Setup**:
   ```bash
   # Run validation scripts
   ./scripts/validate-docker.sh
   python scripts/check_database.py
   ```

3. **Clean Installation**:
   ```bash
   # Docker cleanup
   docker-compose down -v
   docker system prune -a
   
   # Python cleanup
   rm -rf venv __pycache__ .pytest_cache
   ```

4. **Create Issue**: If problems persist, create an issue with:
   - Operating system and version
   - Python version
   - Docker version (if using Docker)
   - Complete error messages
   - Steps to reproduce

## Uninstallation

### Docker Installation

```bash
# Stop and remove containers
docker-compose down -v

# Remove images
docker rmi $(docker images -q prueba_tecnica*)

# Remove project directory
cd ..
rm -rf prueba-tecnica-python
```

### Local Installation

```bash
# Deactivate virtual environment
deactivate

# Remove project directory
cd ..
rm -rf prueba-tecnica-python

# Remove PostgreSQL database (optional)
sudo -u postgres psql
DROP DATABASE prueba_tecnica;
DROP USER testuser;
\q
```

### Development Setup

```bash
# Remove pre-commit hooks
pre-commit uninstall

# Follow local installation uninstallation steps
```

## Next Steps

After successful installation:

1. **Read Documentation**: Check out the [README.md](README.md) for usage instructions
2. **API Documentation**: Visit http://localhost:8000/docs for interactive API documentation
3. **Run Examples**: Try the examples in [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md)
4. **Explore Code**: Review the source code structure and implementation
5. **Run Tests**: Execute the test suite to understand the functionality

## Support

For additional support:
- Check the [Troubleshooting](#troubleshooting) section
- Review the [FAQ](FAQ.md) (if available)
- Create an issue in the project repository
- Check the project documentation