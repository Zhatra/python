"""
FastAPI application for the Missing Number API.

This module implements a REST API that solves the missing number problem
from a set of the first 100 natural numbers using the NumberSet class.
"""

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, validator
from typing import Optional
import time
import logging
from datetime import datetime

from .number_set import NumberSet
from src.exceptions import (
    TechnicalTestError, NumberSetError, NumberAlreadyExtractedError,
    NumberOutOfRangeError, NoNumbersExtractedError, MultipleNumbersExtractedError
)
from src.validation import APIInputValidator

# Configure logging
from src.logging_config import setup_api_logging, log_error_with_context

# Set up logging for API
setup_api_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Missing Number API",
    description="API for finding missing numbers from the first 100 natural numbers",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global NumberSet instance
number_set = NumberSet(max_number=100)


# Pydantic models for API responses
class ExtractResponse(BaseModel):
    """Response model for extract endpoint."""
    success: bool
    message: str
    extracted_number: int
    remaining_count: int


class MissingNumberResponse(BaseModel):
    """Response model for missing number endpoint."""
    missing_number: int
    calculation_method: str = "mathematical_sum"
    execution_time_ms: float
    extracted_numbers: list[int]


class ResetResponse(BaseModel):
    """Response model for reset endpoint."""
    success: bool
    message: str
    total_numbers: int


class ErrorResponse(BaseModel):
    """Response model for error cases."""
    error: str
    detail: str
    status_code: int
# Exception handlers
@app.exception_handler(TechnicalTestError)
async def technical_test_error_handler(request: Request, exc: TechnicalTestError):
    """Handle custom technical test exceptions."""
    log_error_with_context(
        logger,
        f"Technical test error: {exc.message}",
        exception=exc,
        context={
            'request_url': str(request.url),
            'request_method': request.method,
            'error_code': exc.error_code
        }
    )
    
    # Map specific exceptions to appropriate HTTP status codes
    status_code = status.HTTP_400_BAD_REQUEST
    if isinstance(exc, NumberAlreadyExtractedError):
        status_code = status.HTTP_409_CONFLICT
    elif isinstance(exc, (NoNumbersExtractedError, MultipleNumbersExtractedError)):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    
    return JSONResponse(
        status_code=status_code,
        content=exc.to_dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors."""
    log_error_with_context(
        logger,
        "Request validation error",
        exception=exc,
        context={
            'request_url': str(request.url),
            'request_method': request.method,
            'validation_errors': exc.errors()
        },
        error_code='REQUEST_VALIDATION_ERROR'
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            'error': 'VALIDATION_ERROR',
            'message': 'Request validation failed',
            'details': {
                'validation_errors': exc.errors()
            }
        }
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    logger.error(f"Value error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="VALIDATION_ERROR",
            detail=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST
        ).dict()
    )


@app.exception_handler(TypeError)
async def type_error_handler(request: Request, exc: TypeError):
    """Handle TypeError exceptions."""
    logger.error(f"Type error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error="TYPE_ERROR",
            detail=str(exc),
            status_code=status.HTTP_400_BAD_REQUEST
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    log_error_with_context(
        logger,
        "Unexpected error occurred",
        exception=exc,
        context={
            'request_url': str(request.url),
            'request_method': request.method,
            'user_agent': request.headers.get('user-agent', 'unknown')
        },
        error_code='INTERNAL_SERVER_ERROR'
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            'error': 'INTERNAL_SERVER_ERROR',
            'message': 'An unexpected error occurred',
            'details': {}
        }
    )


# API Endpoints
@app.get("/", summary="Root endpoint")
async def root():
    """Root endpoint providing API information."""
    return {
        "message": "Missing Number API",
        "version": "1.0.0",
        "endpoints": {
            "extract": "POST /extract/{number}",
            "missing": "GET /missing",
            "reset": "POST /reset"
        }
    }


@app.post(
    "/extract/{number}",
    response_model=ExtractResponse,
    summary="Extract a number from the set",
    description="Remove a specific number from the set of natural numbers (1-100)"
)
async def extract_number(number: int) -> ExtractResponse:
    """
    Extract (remove) a specific number from the set.
    
    Args:
        number (int): The number to extract (must be between 1 and 100)
        
    Returns:
        ExtractResponse: Success status, message, extracted number, and remaining count
        
    Raises:
        TechnicalTestError: If number is invalid or already extracted
    """
    # Validate input using our validator
    validated_number = APIInputValidator.validate_extract_number_input(number)
    
    # Attempt to extract the number (this will raise appropriate exceptions)
    number_set.extract(validated_number)
    
    logger.info(f"Successfully extracted number: {validated_number}")
    
    return ExtractResponse(
        success=True,
        message=f"Successfully extracted number {validated_number}",
        extracted_number=validated_number,
        remaining_count=number_set.count_remaining()
    )


@app.get(
    "/missing",
    response_model=MissingNumberResponse,
    summary="Get the missing number",
    description="Calculate and return the missing number from the set"
)
async def get_missing_number() -> MissingNumberResponse:
    """
    Calculate and return the missing number from the set.
    
    Returns:
        MissingNumberResponse: The missing number, calculation method, execution time, and extracted numbers
        
    Raises:
        TechnicalTestError: If no numbers have been extracted or multiple numbers are missing
    """
    start_time = time.time()
    
    # Calculate missing number (this will raise appropriate exceptions)
    missing_number = number_set.find_missing_number()
    
    end_time = time.time()
    execution_time_ms = (end_time - start_time) * 1000
    
    logger.info(f"Calculated missing number: {missing_number} in {execution_time_ms:.2f}ms")
    
    return MissingNumberResponse(
        missing_number=missing_number,
        calculation_method="mathematical_sum",
        execution_time_ms=round(execution_time_ms, 2),
        extracted_numbers=number_set.get_extracted_numbers()
    )


@app.post(
    "/reset",
    response_model=ResetResponse,
    summary="Reset the number set",
    description="Reset the set to contain all numbers from 1 to 100"
)
async def reset_set() -> ResetResponse:
    """
    Reset the number set to its initial state (containing all numbers 1-100).
    
    Returns:
        ResetResponse: Success status, message, and total number count
    """
    number_set.reset()
    
    logger.info("Number set has been reset")
    
    return ResetResponse(
        success=True,
        message="Number set has been reset to contain all numbers from 1 to 100",
        total_numbers=number_set.count_remaining()
    )


@app.get("/status", summary="Get current status")
async def get_status():
    """Get the current status of the number set."""
    return {
        "total_numbers": number_set.max_number,
        "remaining_count": number_set.count_remaining(),
        "extracted_count": number_set.count_extracted(),
        "extracted_numbers": number_set.get_extracted_numbers(),
        "is_complete": number_set.is_complete()
    }


# Health check endpoint
@app.get("/health", summary="Health check")
async def health_check():
    """
    Comprehensive health check endpoint.
    
    Returns:
        dict: Health status including service status, database connectivity, and timestamp
    """
    health_status = {
        "status": "healthy",
        "service": "Missing Number API",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
    
    # Check NumberSet functionality
    try:
        # Test basic NumberSet operations
        test_set = NumberSet(max_number=10)
        test_set.extract(5)
        missing = test_set.find_missing_number()
        test_set.reset()
        
        health_status["number_set"] = {
            "status": "healthy",
            "test_result": "passed"
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["number_set"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check database connectivity (if database components are available)
    try:
        from src.database.connection import DatabaseConnection
        db_conn = DatabaseConnection()
        with db_conn.get_connection() as conn:
            # Simple query to test connectivity
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        health_status["database"] = {
            "status": "healthy",
            "connection": "active"
        }
    except ImportError:
        # Database components not available, skip check
        health_status["database"] = {
            "status": "not_configured",
            "message": "Database components not available"
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Set appropriate HTTP status code
    status_code = status.HTTP_200_OK
    if health_status["status"] == "unhealthy":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif health_status["status"] == "degraded":
        status_code = status.HTTP_200_OK  # Still functional but with issues
    
    return JSONResponse(
        status_code=status_code,
        content=health_status
    )


# Error monitoring endpoint
@app.get("/errors/summary", summary="Get error summary")
async def get_error_summary():
    """Get summary of tracked errors and warnings."""
    from src.logging_config import get_error_summary
    
    summary = get_error_summary()
    return {
        "error_summary": summary,
        "timestamp": datetime.now().isoformat(),
        "service": "Missing Number API"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)