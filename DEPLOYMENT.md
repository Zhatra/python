# Deployment Guide

This document provides comprehensive instructions for deploying the Prueba Técnica Python application using Docker containers.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [Deployment Options](#deployment-options)
- [Service Profiles](#service-profiles)
- [Production Deployment](#production-deployment)
- [Health Checks](#health-checks)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

## Prerequisites

Before deploying the application, ensure you have the following installed:

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 2.0 or higher)
- **Git** (for cloning the repository)
- **curl** (for health checks)

### Verify Prerequisites

```bash
# Check Docker version
docker --version

# Check Docker Compose version
docker-compose --version

# Verify Docker is running
docker info
```

## Quick Start

The fastest way to get the application running:

```bash
# Clone the repository
git clone <repository-url>
cd prueba-tecnica-python

# Validate Docker setup (recommended)
./scripts/validate-docker.sh

# Deploy development environment
./scripts/deploy.sh

# Or use the Docker management script
./scripts/docker-manage.sh start dev
```

This will start:
- PostgreSQL database
- API service with hot reload
- All necessary volumes and networks

Access the application:
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Environment Configuration

### Environment Variables

The application uses environment variables for configuration. Copy `.env.example` to `.env` and modify as needed:

```bash
cp .env.example .env
```

Key configuration options:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=prueba_tecnica
DB_USER=testuser
DB_PASSWORD=testpass

# API Configuration
API_PORT=8000
API_HOST=0.0.0.0

# Application Configuration
LOG_LEVEL=INFO
ENVIRONMENT=development

# Data Processing Configuration
BATCH_SIZE=1000
MAX_WORKERS=4
```

### Docker Environment Variables

Additional Docker-specific variables:

```env
# Docker Configuration
COMPOSE_PROJECT_NAME=prueba_tecnica

# Health Check Configuration
HEALTH_CHECK_INTERVAL=30s
HEALTH_CHECK_TIMEOUT=10s
HEALTH_CHECK_RETRIES=3
```

## Deployment Options

### 1. Automated Deployment Script

The recommended way to deploy is using the deployment script:

```bash
# Development deployment (default)
./scripts/deploy.sh

# Production deployment
./scripts/deploy.sh --environment production --profile api

# Fresh build without cache
./scripts/deploy.sh --fresh

# Skip tests during deployment
./scripts/deploy.sh --skip-tests
```

#### Deployment Script Options

| Option | Description | Default |
|--------|-------------|---------|
| `-e, --environment` | Set environment (development\|production) | development |
| `-p, --profile` | Set docker-compose profile | dev |
| `-f, --fresh` | Force fresh build (no cache) | false |
| `-s, --skip-tests` | Skip running tests | false |
| `-h, --help` | Show help message | - |

### 2. Manual Docker Compose

For more control, use Docker Compose directly:

```bash
# Start development environment
docker-compose --profile dev up -d

# Start only API service
docker-compose --profile api up -d

# Start only data processing service
docker-compose --profile data-processing up -d

# Build and start
docker-compose --profile dev up -d --build
```

### 3. Docker Management Script

Use the management script for common operations:

```bash
# Start services
./scripts/docker-manage.sh start dev

# View logs
./scripts/docker-manage.sh logs api

# Open shell in container
./scripts/docker-manage.sh shell database

# Check service status
./scripts/docker-manage.sh status

# Health check
./scripts/docker-manage.sh health
```

### 4. Docker Validation Script

Validate your Docker setup before deployment:

```bash
# Validate Docker configuration
./scripts/validate-docker.sh
```

This script checks:
- Docker and Docker Compose installation
- Configuration file validity
- Required directories and permissions
- Environment variables
- Production secrets setup

## Service Profiles

The application uses Docker Compose profiles to manage different deployment scenarios:

### Development Profile (`dev`)

**Services**: Database + API with hot reload

```bash
docker-compose --profile dev up -d
```

**Features**:
- Hot reload for development
- Volume mounts for source code
- Debug logging enabled
- Development database settings

### API Profile (`api`)

**Services**: Database + Production API

```bash
docker-compose --profile api up -d
```

**Features**:
- Production-optimized API container
- No source code volume mounts
- Optimized logging
- Health checks enabled

### Data Processing Profile (`data-processing`)

**Services**: Database + Data Processing Service

```bash
docker-compose --profile data-processing up -d
```

**Features**:
- Dedicated data processing container
- Batch processing capabilities
- Data volume mounts
- Processing-specific environment variables

## Production Deployment

### 1. Production Configuration

For production deployments, use the production compose file:

```bash
# Deploy production environment
./scripts/deploy.sh --environment production --profile api
```

Or manually:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### 2. Secrets Management

Production deployments use Docker secrets for sensitive data:

```bash
# Create secrets directory
mkdir -p secrets

# Create database password file
echo "your_secure_password" > secrets/db_password.txt
chmod 600 secrets/db_password.txt
```

### 3. Production Features

- **Docker Secrets**: Secure handling of passwords and keys
- **Resource Limits**: Memory and CPU constraints
- **Health Checks**: Comprehensive service monitoring
- **Restart Policies**: Automatic container restart
- **Optimized Images**: Smaller, production-ready containers

### 4. Production Checklist

Before deploying to production:

- [ ] Update all default passwords
- [ ] Configure proper secrets management
- [ ] Set appropriate resource limits
- [ ] Configure log aggregation
- [ ] Set up monitoring and alerting
- [ ] Configure backup procedures
- [ ] Test disaster recovery procedures
- [ ] Review security settings

## Health Checks

### Application Health Checks

The application includes comprehensive health checks:

```bash
# Check API health
curl http://localhost:8000/health

# Detailed health information
curl http://localhost:8000/health | jq
```

### Docker Health Checks

Docker containers include built-in health checks:

```bash
# Check container health status
docker-compose ps

# View health check logs
docker inspect <container_name> | jq '.[0].State.Health'
```

### Health Check Endpoints

| Endpoint | Description |
|----------|-------------|
| `/health` | Basic health check |
| `/status` | NumberSet status |
| `/errors/summary` | Error monitoring |

## Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Check what's using the port
lsof -i :8000

# Change port in .env file
echo "API_PORT=8001" >> .env
```

#### 2. Database Connection Issues

```bash
# Check database logs
./scripts/docker-manage.sh logs database

# Restart database service
docker-compose restart database

# Check database connectivity
docker-compose exec database pg_isready -U testuser
```

#### 3. Container Build Failures

```bash
# Clean build with no cache
./scripts/docker-manage.sh build --no-cache

# Clean up Docker system
./scripts/docker-manage.sh clean
```

#### 4. Permission Issues

```bash
# Fix file permissions
sudo chown -R $USER:$USER .

# Fix script permissions
chmod +x scripts/*.sh
```

### Debugging Commands

```bash
# View all container logs
docker-compose logs -f

# Check container resource usage
docker stats

# Inspect container configuration
docker inspect <container_name>

# Execute commands in running container
docker-compose exec <service> <command>
```

### Log Locations

- **Application Logs**: `./logs/`
- **Container Logs**: `docker-compose logs <service>`
- **Database Logs**: `docker-compose logs database`

## Maintenance

### Regular Maintenance Tasks

#### 1. Database Backup

```bash
# Create backup
./scripts/docker-manage.sh backup

# Restore from backup
./scripts/docker-manage.sh restore backup_20240101_120000.sql
```

#### 2. Log Rotation

```bash
# Clean old logs
find ./logs -name "*.log" -mtime +30 -delete

# Rotate Docker logs
docker system prune -f
```

#### 3. Image Updates

```bash
# Pull latest base images
docker-compose pull

# Rebuild with latest dependencies
./scripts/deploy.sh --fresh
```

#### 4. System Cleanup

```bash
# Clean unused Docker resources
./scripts/docker-manage.sh clean

# Remove old images
docker image prune -a -f
```

### Monitoring

#### 1. Service Status

```bash
# Check all services
./scripts/docker-manage.sh status

# Health check
./scripts/docker-manage.sh health
```

#### 2. Resource Usage

```bash
# Container resource usage
docker stats

# System resource usage
docker system df
```

#### 3. Log Monitoring

```bash
# Follow all logs
docker-compose logs -f

# Follow specific service logs
./scripts/docker-manage.sh logs api
```

### Scaling

#### Horizontal Scaling

```bash
# Scale API service
docker-compose up -d --scale api=3

# Use load balancer (nginx, traefik, etc.)
```

#### Vertical Scaling

Update resource limits in `docker-compose.prod.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '1.0'
    reservations:
      memory: 256M
      cpus: '0.5'
```

## Security Considerations

### 1. Network Security

- Services communicate through isolated Docker network
- Only necessary ports are exposed
- Database is not directly accessible from outside

### 2. Container Security

- Non-root user in containers
- Minimal base images
- Regular security updates

### 3. Secrets Management

- Use Docker secrets for production
- Never commit secrets to version control
- Rotate secrets regularly

### 4. Access Control

- Implement proper authentication
- Use HTTPS in production
- Regular security audits

## Support

For issues and questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Review container logs
3. Check the project documentation
4. Create an issue in the project repository

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)