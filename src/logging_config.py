"""Comprehensive logging configuration for error tracking and monitoring."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import json
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'thread_name': record.threadName,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info) if record.exc_info else None
            }
        
        # Add extra fields from the log record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
                'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'message'
            }:
                extra_fields[key] = value
        
        if extra_fields:
            log_entry['extra'] = extra_fields
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class ErrorTrackingFilter(logging.Filter):
    """Filter to track and categorize errors."""
    
    def __init__(self):
        super().__init__()
        self.error_counts: Dict[str, int] = {}
        self.warning_counts: Dict[str, int] = {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter and track error/warning counts."""
        if record.levelno >= logging.ERROR:
            error_key = f"{record.module}.{record.funcName}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        elif record.levelno == logging.WARNING:
            warning_key = f"{record.module}.{record.funcName}"
            self.warning_counts[warning_key] = self.warning_counts.get(warning_key, 0) + 1
        
        return True
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of tracked errors and warnings."""
        return {
            'total_errors': sum(self.error_counts.values()),
            'total_warnings': sum(self.warning_counts.values()),
            'error_breakdown': dict(self.error_counts),
            'warning_breakdown': dict(self.warning_counts)
        }


class PerformanceLoggingFilter(logging.Filter):
    """Filter to add performance metrics to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add performance metrics to log records."""
        # Add memory usage if available
        try:
            import psutil
            process = psutil.Process()
            record.memory_usage_mb = process.memory_info().rss / 1024 / 1024
            record.cpu_percent = process.cpu_percent()
        except ImportError:
            pass
        
        return True


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_json_logging: bool = False,
    enable_error_tracking: bool = True,
    enable_performance_logging: bool = False,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> Dict[str, Any]:
    """Set up comprehensive logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (if None, logs to console only)
        enable_json_logging: Whether to use JSON formatting
        enable_error_tracking: Whether to enable error tracking
        enable_performance_logging: Whether to add performance metrics
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        
    Returns:
        Dictionary with logging configuration details
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if enable_json_logging:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    
    # Add filters
    filters = []
    
    if enable_error_tracking:
        error_filter = ErrorTrackingFilter()
        console_handler.addFilter(error_filter)
        filters.append(error_filter)
    
    if enable_performance_logging:
        perf_filter = PerformanceLoggingFilter()
        console_handler.addFilter(perf_filter)
        filters.append(perf_filter)
    
    root_logger.addHandler(console_handler)
    
    # Create file handler if log file specified
    file_handler = None
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        
        # Add same filters to file handler
        for filter_obj in filters:
            file_handler.addFilter(filter_obj)
        
        root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    configure_module_loggers(numeric_level)
    
    # Log configuration details
    config_details = {
        'log_level': log_level,
        'numeric_level': numeric_level,
        'log_file': log_file,
        'json_logging': enable_json_logging,
        'error_tracking': enable_error_tracking,
        'performance_logging': enable_performance_logging,
        'handlers': ['console'] + (['file'] if log_file else []),
        'filters': [f.__class__.__name__ for f in filters]
    }
    
    logging.info(f"Logging configured: {config_details}")
    return config_details


def configure_module_loggers(log_level: int) -> None:
    """Configure specific module loggers with appropriate levels."""
    
    # Application loggers
    app_loggers = [
        'src.api',
        'src.data_processing',
        'src.database',
        'src.validation',
        'src.exceptions'
    ]
    
    for logger_name in app_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(log_level)
    
    # Third-party loggers (usually more verbose)
    third_party_loggers = {
        'sqlalchemy.engine': logging.WARNING,  # Reduce SQL query noise
        'sqlalchemy.pool': logging.WARNING,
        'uvicorn.access': logging.INFO,
        'uvicorn.error': logging.INFO,
        'fastapi': logging.INFO,
        'pandas': logging.WARNING,
    }
    
    for logger_name, level in third_party_loggers.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)


def log_error_with_context(
    logger: logging.Logger,
    message: str,
    exception: Optional[Exception] = None,
    context: Optional[Dict[str, Any]] = None,
    error_code: Optional[str] = None
) -> None:
    """Log error with additional context information.
    
    Args:
        logger: Logger instance to use
        message: Error message
        exception: Exception object (if any)
        context: Additional context information
        error_code: Error code for categorization
    """
    extra_info = {}
    
    if context:
        extra_info.update(context)
    
    if error_code:
        extra_info['error_code'] = error_code
    
    if exception:
        extra_info['exception_type'] = type(exception).__name__
        extra_info['exception_message'] = str(exception)
        
        # Add custom exception details if available
        if hasattr(exception, 'error_code'):
            extra_info['custom_error_code'] = exception.error_code
        if hasattr(exception, 'details'):
            extra_info['error_details'] = exception.details
    
    if extra_info:
        logger.error(message, extra=extra_info, exc_info=exception is not None)
    else:
        logger.error(message, exc_info=exception is not None)


def log_performance_metric(
    logger: logging.Logger,
    operation: str,
    duration_seconds: float,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """Log performance metrics for operations.
    
    Args:
        logger: Logger instance to use
        operation: Name of the operation
        duration_seconds: Duration in seconds
        context: Additional context information
    """
    extra_info = {
        'operation': operation,
        'duration_seconds': duration_seconds,
        'performance_metric': True
    }
    
    if context:
        extra_info.update(context)
    
    logger.info(f"Performance: {operation} completed in {duration_seconds:.3f}s", extra=extra_info)


def get_error_summary() -> Dict[str, Any]:
    """Get summary of tracked errors from all error tracking filters.
    
    Returns:
        Dictionary with error summary information
    """
    summary = {
        'total_errors': 0,
        'total_warnings': 0,
        'error_breakdown': {},
        'warning_breakdown': {}
    }
    
    # Find all error tracking filters
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        for filter_obj in handler.filters:
            if isinstance(filter_obj, ErrorTrackingFilter):
                filter_summary = filter_obj.get_error_summary()
                summary['total_errors'] += filter_summary['total_errors']
                summary['total_warnings'] += filter_summary['total_warnings']
                
                # Merge breakdowns
                for key, count in filter_summary['error_breakdown'].items():
                    summary['error_breakdown'][key] = summary['error_breakdown'].get(key, 0) + count
                
                for key, count in filter_summary['warning_breakdown'].items():
                    summary['warning_breakdown'][key] = summary['warning_breakdown'].get(key, 0) + count
    
    return summary


def setup_api_logging() -> None:
    """Set up logging specifically for the API application."""
    setup_logging(
        log_level="INFO",
        log_file="logs/api.log",
        enable_json_logging=False,
        enable_error_tracking=True,
        enable_performance_logging=True
    )


def setup_data_processing_logging() -> None:
    """Set up logging specifically for data processing operations."""
    setup_logging(
        log_level="INFO",
        log_file="logs/data_processing.log",
        enable_json_logging=True,
        enable_error_tracking=True,
        enable_performance_logging=True
    )


def setup_test_logging() -> None:
    """Set up logging for test environments."""
    setup_logging(
        log_level="DEBUG",
        log_file=None,  # Console only for tests
        enable_json_logging=False,
        enable_error_tracking=False,
        enable_performance_logging=False
    )


# Context manager for temporary logging configuration
class TemporaryLoggingConfig:
    """Context manager for temporary logging configuration changes."""
    
    def __init__(self, **kwargs):
        self.new_config = kwargs
        self.original_handlers = []
        self.original_level = None
    
    def __enter__(self):
        # Save original configuration
        root_logger = logging.getLogger()
        self.original_level = root_logger.level
        self.original_handlers = root_logger.handlers.copy()
        
        # Apply new configuration
        setup_logging(**self.new_config)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original configuration
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.handlers.extend(self.original_handlers)
        root_logger.setLevel(self.original_level)