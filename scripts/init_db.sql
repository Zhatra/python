-- Database initialization script for PostgreSQL
-- This script will be executed when the database container starts

-- Create database if it doesn't exist (handled by Docker environment variables)
-- CREATE DATABASE IF NOT EXISTS prueba_tecnica;

-- Create schemas for organizing tables
CREATE SCHEMA IF NOT EXISTS raw_data;
CREATE SCHEMA IF NOT EXISTS normalized_data;

-- Grant permissions to the application user
GRANT ALL PRIVILEGES ON SCHEMA raw_data TO testuser;
GRANT ALL PRIVILEGES ON SCHEMA normalized_data TO testuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw_data TO testuser;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA normalized_data TO testuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA raw_data TO testuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA normalized_data TO testuser;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA raw_data GRANT ALL ON TABLES TO testuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA normalized_data GRANT ALL ON TABLES TO testuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA raw_data GRANT ALL ON SEQUENCES TO testuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA normalized_data GRANT ALL ON SEQUENCES TO testuser;