"""
Configuration management for the Prueba Técnica Python application.

This module provides centralized configuration management using environment variables
with sensible defaults. It supports database, API, and application-level settings
that can be customized through environment variables or .env files.

Example:
    Basic usage:
        from src.config import db_config, api_config, app_config
        
        # Database connection
        connection_string = db_config.connection_string
        
        # API settings
        host = api_config.HOST
        port = api_config.PORT
        
        # Application settings
        log_level = app_config.LOG_LEVEL

Environment Variables:
    Database Configuration:
        DB_HOST: Database host (default: localhost)
        DB_PORT: Database port (default: 5432)
        DB_NAME: Database name (default: prueba_tecnica)
        DB_USER: Database user (default: testuser)
        DB_PASSWORD: Database password (default: testpass)
        DB_POOL_SIZE: Connection pool size (default: 10)
        DB_MAX_OVERFLOW: Max overflow connections (default: 20)
    
    API Configuration:
        API_HOST: API server host (default: 0.0.0.0)
        API_PORT: API server port (default: 8000)
        API_WORKERS: Number of API workers (default: 1)
        API_RELOAD: Enable hot reload (default: false)
    
    Application Configuration:
        LOG_LEVEL: Logging level (default: INFO)
        ENVIRONMENT: Environment name (default: development)
        BATCH_SIZE: Data processing batch size (default: 1000)
        MAX_WORKERS: Maximum worker threads (default: 4)
        INPUT_DATA_PATH: Input data directory (default: ./data/input)
        OUTPUT_DATA_PATH: Output data directory (default: ./data/output)
"""

import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """
    Database configuration settings.
    
    Manages PostgreSQL database connection parameters and connection pooling
    settings. All values can be overridden using environment variables.
    
    Attributes:
        HOST (str): Database server hostname or IP address
        PORT (int): Database server port number
        NAME (str): Database name to connect to
        USER (str): Database username for authentication
        PASSWORD (str): Database password for authentication
        POOL_SIZE (int): Number of connections to maintain in pool
        MAX_OVERFLOW (int): Maximum additional connections beyond pool size
    
    Example:
        >>> config = DatabaseConfig()
        >>> print(config.connection_string)
        postgresql://testuser:testpass@localhost:5432/prueba_tecnica
    """
    
    def __init__(self):
        """Initialize database configuration from environment variables."""
        self.HOST: str = os.getenv("DB_HOST", "localhost")
        self.PORT: int = int(os.getenv("DB_PORT", "5432"))
        self.NAME: str = os.getenv("DB_NAME", "prueba_tecnica")
        self.USER: str = os.getenv("DB_USER", "testuser")
        self.PASSWORD: str = os.getenv("DB_PASSWORD", "testpass")
        self.POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
        self.MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate database configuration parameters."""
        if not self.HOST:
            raise ValueError("Database host cannot be empty")
        if not (1 <= self.PORT <= 65535):
            raise ValueError(f"Invalid database port: {self.PORT}")
        if not self.NAME:
            raise ValueError("Database name cannot be empty")
        if not self.USER:
            raise ValueError("Database user cannot be empty")
        if self.POOL_SIZE < 1:
            raise ValueError(f"Pool size must be positive: {self.POOL_SIZE}")
        if self.MAX_OVERFLOW < 0:
            raise ValueError(f"Max overflow cannot be negative: {self.MAX_OVERFLOW}")
    
    @property
    def connection_string(self) -> str:
        """
        Get the PostgreSQL connection string.
        
        Returns:
            str: Complete PostgreSQL connection string for SQLAlchemy
            
        Example:
            postgresql://user:pass@localhost:5432/dbname
        """
        return f"postgresql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"
    
    @property
    def connection_string_safe(self) -> str:
        """
        Get connection string with masked password for logging.
        
        Returns:
            str: Connection string with password replaced by asterisks
        """
        return f"postgresql://{self.USER}:***@{self.HOST}:{self.PORT}/{self.NAME}"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary (excluding sensitive data).
        
        Returns:
            Dict[str, Any]: Configuration dictionary without password
        """
        return {
            "host": self.HOST,
            "port": self.PORT,
            "name": self.NAME,
            "user": self.USER,
            "pool_size": self.POOL_SIZE,
            "max_overflow": self.MAX_OVERFLOW
        }


class APIConfig:
    """
    API server configuration settings.
    
    Manages FastAPI server configuration including host, port, and worker settings.
    All values can be overridden using environment variables.
    
    Attributes:
        HOST (str): Server bind address (0.0.0.0 for all interfaces)
        PORT (int): Server port number
        WORKERS (int): Number of worker processes
        RELOAD (bool): Enable automatic code reloading for development
    
    Example:
        >>> config = APIConfig()
        >>> print(f"API will run on {config.HOST}:{config.PORT}")
        API will run on 0.0.0.0:8000
    """
    
    def __init__(self):
        """Initialize API configuration from environment variables."""
        self.HOST: str = os.getenv("API_HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("API_PORT", "8000"))
        self.WORKERS: int = int(os.getenv("API_WORKERS", "1"))
        self.RELOAD: bool = os.getenv("API_RELOAD", "false").lower() == "true"
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate API configuration parameters."""
        if not (1 <= self.PORT <= 65535):
            raise ValueError(f"Invalid API port: {self.PORT}")
        if self.WORKERS < 1:
            raise ValueError(f"Worker count must be positive: {self.WORKERS}")
    
    @property
    def base_url(self) -> str:
        """
        Get the base URL for the API.
        
        Returns:
            str: Complete base URL for API access
        """
        host = "localhost" if self.HOST == "0.0.0.0" else self.HOST
        return f"http://{host}:{self.PORT}"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        return {
            "host": self.HOST,
            "port": self.PORT,
            "workers": self.WORKERS,
            "reload": self.RELOAD,
            "base_url": self.base_url
        }


class AppConfig:
    """
    General application configuration settings.
    
    Manages application-wide settings including logging, data processing,
    and file path configurations. All values can be overridden using
    environment variables.
    
    Attributes:
        LOG_LEVEL (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        ENVIRONMENT (str): Environment name (development, production, testing)
        BATCH_SIZE (int): Default batch size for data processing operations
        MAX_WORKERS (int): Maximum number of worker threads for parallel processing
        INPUT_DATA_PATH (str): Directory path for input data files
        OUTPUT_DATA_PATH (str): Directory path for output data files
        BACKUP_PATH (str): Directory path for backup files
        LOG_PATH (str): Directory path for log files
    
    Example:
        >>> config = AppConfig()
        >>> print(f"Processing batches of {config.BATCH_SIZE} records")
        Processing batches of 1000 records
    """
    
    def __init__(self):
        """Initialize application configuration from environment variables."""
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development").lower()
        self.BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "1000"))
        self.MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
        
        # File paths
        self.INPUT_DATA_PATH: str = os.getenv("INPUT_DATA_PATH", "./data/input")
        self.OUTPUT_DATA_PATH: str = os.getenv("OUTPUT_DATA_PATH", "./data/output")
        self.BACKUP_PATH: str = os.getenv("BACKUP_PATH", "./backups")
        self.LOG_PATH: str = os.getenv("LOG_PATH", "./logs")
        
        # Data processing settings
        self.VALIDATION_LEVEL: str = os.getenv("VALIDATION_LEVEL", "strict").lower()
        self.ERROR_THRESHOLD: float = float(os.getenv("ERROR_THRESHOLD", "0.05"))
        self.CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "10000"))
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate application configuration parameters."""
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.LOG_LEVEL not in valid_log_levels:
            raise ValueError(f"Invalid log level: {self.LOG_LEVEL}")
        
        valid_environments = ["development", "production", "testing"]
        if self.ENVIRONMENT not in valid_environments:
            logger.warning(f"Unknown environment: {self.ENVIRONMENT}")
        
        if self.BATCH_SIZE < 1:
            raise ValueError(f"Batch size must be positive: {self.BATCH_SIZE}")
        
        if self.MAX_WORKERS < 1:
            raise ValueError(f"Max workers must be positive: {self.MAX_WORKERS}")
        
        if not (0.0 <= self.ERROR_THRESHOLD <= 1.0):
            raise ValueError(f"Error threshold must be between 0 and 1: {self.ERROR_THRESHOLD}")
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.ENVIRONMENT == "testing"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        return {
            "log_level": self.LOG_LEVEL,
            "environment": self.ENVIRONMENT,
            "batch_size": self.BATCH_SIZE,
            "max_workers": self.MAX_WORKERS,
            "input_data_path": self.INPUT_DATA_PATH,
            "output_data_path": self.OUTPUT_DATA_PATH,
            "backup_path": self.BACKUP_PATH,
            "log_path": self.LOG_PATH,
            "validation_level": self.VALIDATION_LEVEL,
            "error_threshold": self.ERROR_THRESHOLD,
            "chunk_size": self.CHUNK_SIZE
        }


def get_database_url() -> str:
    """
    Get database connection URL from configuration.
    
    Returns:
        str: Database connection URL
        
    Example:
        >>> url = get_database_url()
        >>> print(url)
        postgresql://testuser:testpass@localhost:5432/prueba_tecnica
    """
    return db_config.connection_string


def validate_all_configs() -> bool:
    """
    Validate all configuration settings.
    
    Returns:
        bool: True if all configurations are valid
        
    Raises:
        ValueError: If any configuration is invalid
    """
    try:
        # Configurations are validated in their __init__ methods
        db_config._validate_config()
        api_config._validate_config()
        app_config._validate_config()
        
        logger.info("All configurations validated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise


def print_config_summary() -> None:
    """Print a summary of current configuration settings."""
    print("=== Configuration Summary ===")
    print(f"Environment: {app_config.ENVIRONMENT}")
    print(f"Log Level: {app_config.LOG_LEVEL}")
    print(f"Database: {db_config.connection_string_safe}")
    print(f"API: {api_config.base_url}")
    print(f"Batch Size: {app_config.BATCH_SIZE}")
    print(f"Max Workers: {app_config.MAX_WORKERS}")
    print("============================")


# Global configuration instances
# These are initialized when the module is imported
try:
    db_config = DatabaseConfig()
    api_config = APIConfig()
    app_config = AppConfig()
    
    logger.info("Configuration loaded successfully")
    
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    raise