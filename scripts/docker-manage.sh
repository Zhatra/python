#!/bin/bash

# Docker management script for Prueba Técnica Python
# Provides common Docker operations and utilities

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

# Function to show usage
show_usage() {
    echo "Docker Management Script for Prueba Técnica Python"
    echo ""
    echo "Usage: $0 COMMAND [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start [PROFILE]          Start services with specified profile (dev|api|data-processing)"
    echo "  stop [PROFILE]           Stop services with specified profile"
    echo "  restart [PROFILE]        Restart services with specified profile"
    echo "  logs [SERVICE]           Show logs for all services or specific service"
    echo "  shell SERVICE            Open shell in running service container"
    echo "  build [--no-cache]       Build all images"
    echo "  clean                    Clean up containers, images, and volumes"
    echo "  status                   Show status of all services"
    echo "  health                   Check health of API service"
    echo "  backup                   Backup database data"
    echo "  restore FILE             Restore database from backup file"
    echo "  init-db                  Initialize database with sample data"
    echo ""
    echo "Examples:"
    echo "  $0 start dev             # Start development environment"
    echo "  $0 logs api              # Show API service logs"
    echo "  $0 shell database        # Open shell in database container"
    echo "  $0 clean                 # Clean up all Docker resources"
}

# Default values
COMPOSE_FILE="docker-compose.yml"
PROFILE="dev"

# Parse command
COMMAND="$1"
shift || true

case "$COMMAND" in
    start)
        PROFILE="${1:-dev}"
        print_status "Starting services with profile: $PROFILE"
        docker-compose -f $COMPOSE_FILE --profile $PROFILE up -d
        print_success "Services started successfully"
        ;;
        
    stop)
        PROFILE="${1:-dev}"
        print_status "Stopping services with profile: $PROFILE"
        docker-compose -f $COMPOSE_FILE --profile $PROFILE down
        print_success "Services stopped successfully"
        ;;
        
    restart)
        PROFILE="${1:-dev}"
        print_status "Restarting services with profile: $PROFILE"
        docker-compose -f $COMPOSE_FILE --profile $PROFILE restart
        print_success "Services restarted successfully"
        ;;
        
    logs)
        SERVICE="$1"
        if [[ -n "$SERVICE" ]]; then
            print_status "Showing logs for service: $SERVICE"
            docker-compose -f $COMPOSE_FILE logs -f "$SERVICE"
        else
            print_status "Showing logs for all services"
            docker-compose -f $COMPOSE_FILE logs -f
        fi
        ;;
        
    shell)
        SERVICE="$1"
        if [[ -z "$SERVICE" ]]; then
            print_error "Service name is required for shell command"
            echo "Available services: database, api, data-processor, dev"
            exit 1
        fi
        
        print_status "Opening shell in service: $SERVICE"
        if docker-compose -f $COMPOSE_FILE exec "$SERVICE" /bin/bash; then
            print_success "Shell session ended"
        else
            print_warning "Bash not available, trying sh..."
            docker-compose -f $COMPOSE_FILE exec "$SERVICE" /bin/sh
        fi
        ;;
        
    build)
        BUILD_ARGS=""
        if [[ "$1" == "--no-cache" ]]; then
            BUILD_ARGS="--no-cache"
            print_status "Building images with no cache"
        else
            print_status "Building images"
        fi
        
        docker-compose -f $COMPOSE_FILE build $BUILD_ARGS
        print_success "Images built successfully"
        ;;
        
    clean)
        print_warning "This will remove all containers, images, and volumes. Are you sure? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            print_status "Stopping all services..."
            docker-compose -f $COMPOSE_FILE down -v --remove-orphans
            
            print_status "Removing images..."
            docker-compose -f $COMPOSE_FILE down --rmi all
            
            print_status "Cleaning up Docker system..."
            docker system prune -f
            
            print_success "Cleanup completed"
        else
            print_status "Cleanup cancelled"
        fi
        ;;
        
    status)
        print_status "Service status:"
        docker-compose -f $COMPOSE_FILE ps
        
        echo ""
        print_status "Docker system info:"
        docker system df
        ;;
        
    health)
        print_status "Checking API health..."
        
        # Get API port from .env file
        API_PORT=$(grep API_PORT .env 2>/dev/null | cut -d '=' -f2 | tr -d ' ' || echo "8000")
        
        if curl -f http://localhost:$API_PORT/health 2>/dev/null; then
            print_success "API is healthy"
        else
            print_error "API health check failed"
            print_status "Checking if API container is running..."
            docker-compose -f $COMPOSE_FILE ps api
            exit 1
        fi
        ;;
        
    backup)
        print_status "Creating database backup..."
        
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
        
        if docker-compose -f $COMPOSE_FILE exec -T database pg_dump -U testuser prueba_tecnica > "backups/$BACKUP_FILE"; then
            print_success "Database backup created: backups/$BACKUP_FILE"
        else
            print_error "Database backup failed"
            exit 1
        fi
        ;;
        
    restore)
        BACKUP_FILE="$1"
        if [[ -z "$BACKUP_FILE" ]]; then
            print_error "Backup file is required for restore command"
            exit 1
        fi
        
        if [[ ! -f "$BACKUP_FILE" ]]; then
            print_error "Backup file not found: $BACKUP_FILE"
            exit 1
        fi
        
        print_warning "This will overwrite the current database. Are you sure? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            print_status "Restoring database from: $BACKUP_FILE"
            
            if docker-compose -f $COMPOSE_FILE exec -T database psql -U testuser -d prueba_tecnica < "$BACKUP_FILE"; then
                print_success "Database restored successfully"
            else
                print_error "Database restore failed"
                exit 1
            fi
        else
            print_status "Restore cancelled"
        fi
        ;;
        
    init-db)
        print_status "Initializing database with sample data..."
        
        # Check if database is running
        if ! docker-compose -f $COMPOSE_FILE ps database | grep -q "Up"; then
            print_error "Database service is not running. Start it first with: $0 start"
            exit 1
        fi
        
        # Run initialization script
        if docker-compose -f $COMPOSE_FILE exec data-processor python scripts/init_database.py; then
            print_success "Database initialized successfully"
        else
            print_error "Database initialization failed"
            exit 1
        fi
        ;;
        
    *)
        if [[ -z "$COMMAND" ]]; then
            show_usage
        else
            print_error "Unknown command: $COMMAND"
            show_usage
            exit 1
        fi
        ;;
esac