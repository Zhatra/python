#!/bin/bash

# Deployment script for Prueba Técnica Python
# This script handles deployment for different environments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
PROFILE="dev"
COMPOSE_FILE="docker-compose.yml"
BUILD_FRESH=false
SKIP_TESTS=false

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

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENV    Set environment (development|production) [default: development]"
    echo "  -p, --profile PROFILE    Set docker-compose profile (dev|api|data-processing) [default: dev]"
    echo "  -f, --fresh              Force fresh build (no cache)"
    echo "  -s, --skip-tests         Skip running tests"
    echo "  -h, --help               Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Deploy development environment"
    echo "  $0 -e production -p api               # Deploy production API"
    echo "  $0 -e development -p data-processing  # Deploy data processing service"
    echo "  $0 -f -s                              # Fresh build, skip tests"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -p|--profile)
            PROFILE="$2"
            shift 2
            ;;
        -f|--fresh)
            BUILD_FRESH=true
            shift
            ;;
        -s|--skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "development" && "$ENVIRONMENT" != "production" ]]; then
    print_error "Invalid environment: $ENVIRONMENT. Must be 'development' or 'production'"
    exit 1
fi

# Set compose file based on environment
if [[ "$ENVIRONMENT" == "production" ]]; then
    COMPOSE_FILE="docker-compose.prod.yml"
fi

print_status "Starting deployment for $ENVIRONMENT environment with profile: $PROFILE"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install docker-compose and try again."
    exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data/input data/output logs secrets

# Check for environment file
if [[ ! -f .env ]]; then
    if [[ -f .env.example ]]; then
        print_warning ".env file not found. Copying from .env.example"
        cp .env.example .env
        print_warning "Please review and update .env file with appropriate values"
    else
        print_error ".env.example file not found. Cannot create .env file."
        exit 1
    fi
fi

# Create secrets for production
if [[ "$ENVIRONMENT" == "production" ]]; then
    print_status "Setting up production secrets..."
    
    if [[ ! -f secrets/db_password.txt ]]; then
        print_warning "Creating default database password. Please update secrets/db_password.txt with a secure password."
        echo "secure_password_change_me" > secrets/db_password.txt
        chmod 600 secrets/db_password.txt
    fi
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose -f $COMPOSE_FILE --profile $PROFILE down

# Build images
BUILD_ARGS=""
if [[ "$BUILD_FRESH" == true ]]; then
    BUILD_ARGS="--no-cache"
    print_status "Building images with fresh cache..."
else
    print_status "Building images..."
fi

docker-compose -f $COMPOSE_FILE build $BUILD_ARGS

# Run tests if not skipped
if [[ "$SKIP_TESTS" == false && "$ENVIRONMENT" == "development" ]]; then
    print_status "Running tests..."
    
    # Start database for testing
    docker-compose -f $COMPOSE_FILE up -d database
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Run tests in container
    if docker-compose -f $COMPOSE_FILE run --rm dev python -m pytest tests/ -v; then
        print_success "All tests passed!"
    else
        print_error "Tests failed. Deployment aborted."
        docker-compose -f $COMPOSE_FILE down
        exit 1
    fi
    
    # Stop test database
    docker-compose -f $COMPOSE_FILE down
fi

# Start services
print_status "Starting services with profile: $PROFILE..."
docker-compose -f $COMPOSE_FILE --profile $PROFILE up -d

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 15

# Health check for API
if [[ "$PROFILE" == "api" || "$PROFILE" == "dev" ]]; then
    print_status "Performing health check..."
    
    API_PORT=$(grep API_PORT .env | cut -d '=' -f2 | tr -d ' ' || echo "8000")
    
    for i in {1..30}; do
        if curl -f http://localhost:$API_PORT/health > /dev/null 2>&1; then
            print_success "API is healthy and ready!"
            break
        else
            if [[ $i -eq 30 ]]; then
                print_error "API health check failed after 30 attempts"
                docker-compose -f $COMPOSE_FILE logs api
                exit 1
            fi
            print_status "Waiting for API to be ready... (attempt $i/30)"
            sleep 2
        fi
    done
fi

# Show running services
print_status "Deployment completed! Running services:"
docker-compose -f $COMPOSE_FILE ps

# Show useful information
echo ""
print_success "Deployment Summary:"
echo "  Environment: $ENVIRONMENT"
echo "  Profile: $PROFILE"
echo "  Compose file: $COMPOSE_FILE"

if [[ "$PROFILE" == "api" || "$PROFILE" == "dev" ]]; then
    API_PORT=$(grep API_PORT .env | cut -d '=' -f2 | tr -d ' ' || echo "8000")
    echo "  API URL: http://localhost:$API_PORT"
    echo "  API Docs: http://localhost:$API_PORT/docs"
    echo "  Health Check: http://localhost:$API_PORT/health"
fi

echo ""
print_status "Useful commands:"
echo "  View logs: docker-compose -f $COMPOSE_FILE logs -f"
echo "  Stop services: docker-compose -f $COMPOSE_FILE --profile $PROFILE down"
echo "  Restart services: docker-compose -f $COMPOSE_FILE --profile $PROFILE restart"
echo "  Shell access: docker-compose -f $COMPOSE_FILE exec <service> /bin/bash"

print_success "Deployment completed successfully!"