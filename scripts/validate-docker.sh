#!/bin/bash

# Docker validation script for Prueba Técnica Python
# Validates Docker setup and configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_status "Docker Configuration Validation"
echo "=================================="

# Check Docker installation
print_status "Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_success "Docker found: $DOCKER_VERSION"
else
    print_error "Docker is not installed"
    exit 1
fi

# Check Docker Compose installation
print_status "Checking Docker Compose installation..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    print_success "Docker Compose found: $COMPOSE_VERSION"
else
    print_error "Docker Compose is not installed"
    exit 1
fi

# Check if Docker is running
print_status "Checking if Docker daemon is running..."
if docker info > /dev/null 2>&1; then
    print_success "Docker daemon is running"
else
    print_error "Docker daemon is not running"
    exit 1
fi

# Validate Docker Compose files
print_status "Validating Docker Compose configurations..."

if docker-compose config --quiet; then
    print_success "docker-compose.yml is valid"
else
    print_error "docker-compose.yml has configuration errors"
    exit 1
fi

if docker-compose -f docker-compose.prod.yml config --quiet; then
    print_success "docker-compose.prod.yml is valid"
else
    print_error "docker-compose.prod.yml has configuration errors"
    exit 1
fi

# Check environment file
print_status "Checking environment configuration..."
if [[ -f .env ]]; then
    print_success ".env file exists"
    
    # Check required variables
    REQUIRED_VARS=("DB_NAME" "DB_USER" "DB_PASSWORD" "API_PORT")
    for var in "${REQUIRED_VARS[@]}"; do
        if grep -q "^${var}=" .env; then
            print_success "Required variable $var is set"
        else
            print_warning "Required variable $var is not set in .env"
        fi
    done
else
    print_warning ".env file not found. Using .env.example as reference"
    if [[ -f .env.example ]]; then
        print_status "Copying .env.example to .env"
        cp .env.example .env
        print_success ".env file created from example"
    else
        print_error ".env.example file not found"
        exit 1
    fi
fi

# Check Dockerfiles
print_status "Checking Dockerfiles..."
DOCKERFILES=("docker/Dockerfile.api" "docker/Dockerfile.data-processor")
for dockerfile in "${DOCKERFILES[@]}"; do
    if [[ -f "$dockerfile" ]]; then
        print_success "$dockerfile exists"
    else
        print_error "$dockerfile not found"
        exit 1
    fi
done

# Check required directories
print_status "Checking required directories..."
REQUIRED_DIRS=("data/input" "data/output" "logs" "secrets" "backups")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        print_success "Directory $dir exists"
    else
        print_status "Creating directory $dir"
        mkdir -p "$dir"
        print_success "Directory $dir created"
    fi
done

# Check scripts permissions
print_status "Checking script permissions..."
SCRIPTS=("scripts/deploy.sh" "scripts/docker-manage.sh")
for script in "${SCRIPTS[@]}"; do
    if [[ -x "$script" ]]; then
        print_success "$script is executable"
    else
        print_status "Making $script executable"
        chmod +x "$script"
        print_success "$script made executable"
    fi
done

# Check production secrets setup
print_status "Checking production secrets setup..."
if [[ -f "secrets/db_password.txt" ]]; then
    print_success "Production database password file exists"
    
    # Check file permissions
    PERMS=$(stat -c "%a" secrets/db_password.txt)
    if [[ "$PERMS" == "600" ]]; then
        print_success "Database password file has correct permissions (600)"
    else
        print_warning "Database password file permissions should be 600, currently $PERMS"
        print_status "Fixing permissions..."
        chmod 600 secrets/db_password.txt
        print_success "Permissions fixed"
    fi
else
    print_warning "Production database password file not found"
    print_status "Creating default password file (please update with secure password)"
    echo "secure_password_change_me" > secrets/db_password.txt
    chmod 600 secrets/db_password.txt
    print_success "Default password file created"
fi

# Test Docker Compose syntax
print_status "Testing Docker Compose build configuration..."
if docker-compose build --dry-run > /dev/null 2>&1; then
    print_success "Docker Compose build configuration is valid"
else
    print_warning "Docker Compose build test completed (some warnings may be normal)"
fi

# Summary
echo ""
print_success "Docker Configuration Validation Complete!"
echo ""
print_status "Next steps:"
echo "  1. Review and update .env file with your configuration"
echo "  2. Update secrets/db_password.txt with a secure password for production"
echo "  3. Run './scripts/deploy.sh' to start the development environment"
echo "  4. Run './scripts/deploy.sh --environment production --profile api' for production"
echo ""
print_status "Useful commands:"
echo "  ./scripts/docker-manage.sh status    # Check service status"
echo "  ./scripts/docker-manage.sh health    # Check API health"
echo "  ./scripts/docker-manage.sh logs api  # View API logs"