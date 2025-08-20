# Missing Number API Documentation

## Overview

The Missing Number API is a REST API that solves the algorithmic problem of finding a missing number from the first 100 natural numbers. It uses an efficient mathematical approach with O(1) complexity and provides comprehensive error handling and validation.

## Table of Contents

- [API Overview](#api-overview)
- [Authentication](#authentication)
- [Base URL](#base-url)
- [Endpoints](#endpoints)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)
- [SDKs and Libraries](#sdks-and-libraries)

## API Overview

### Features
- **Mathematical Algorithm**: O(1) complexity using sum formula
- **State Management**: Persistent number set across API calls
- **Input Validation**: Comprehensive validation with detailed error messages
- **Error Handling**: Structured error responses with error codes
- **Performance Monitoring**: Request timing and metrics
- **Health Checks**: Service health and status monitoring
- **OpenAPI Documentation**: Automatic interactive documentation

### Technology Stack
- **Framework**: FastAPI with automatic OpenAPI generation
- **Validation**: Pydantic models with custom validators
- **Error Handling**: Custom exception hierarchy
- **Logging**: Structured logging with performance metrics
- **Testing**: Comprehensive test coverage

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

> **Note**: In a production environment, consider implementing API key authentication or OAuth2 for security.

## Base URL

### Development
```
http://localhost:8000
```

### Docker Deployment
```
http://localhost:8000
```

### Documentation URLs
- **Interactive Documentation (Swagger UI)**: `http://localhost:8000/docs`
- **Alternative Documentation (ReDoc)**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

## Endpoints

### Core API Endpoints

#### POST /extract/{number}

Extract (remove) a specific number from the set of 1-100 natural numbers.

**Parameters:**
- `number` (path parameter, required): Integer between 1 and 100

**Request:**
```http
POST /extract/42 HTTP/1.1
Host: localhost:8000
Content-Type: application/json
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Successfully extracted number 42",
  "extracted_number": 42,
  "remaining_count": 99
}
```

**Response (Error - 409):**
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

**Response (Error - 400):**
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

#### GET /missing

Calculate and return the missing number from the set. Requires exactly one number to be extracted.

**Request:**
```http
GET /missing HTTP/1.1
Host: localhost:8000
```

**Response (Success - 200):**
```json
{
  "missing_number": 42,
  "calculation_method": "mathematical_sum",
  "execution_time_ms": 0.15,
  "extracted_numbers": [42]
}
```

**Response (Error - 400):**
```json
{
  "error": "NO_NUMBERS_EXTRACTED",
  "message": "Cannot find missing number: no numbers have been extracted",
  "details": {
    "extracted_count": 0,
    "required_count": 1
  }
}
```

**Response (Error - 400):**
```json
{
  "error": "MULTIPLE_NUMBERS_EXTRACTED",
  "message": "Cannot find missing number: multiple numbers have been extracted",
  "details": {
    "extracted_count": 3,
    "extracted_numbers": [15, 42, 73],
    "required_count": 1
  }
}
```

#### POST /reset

Reset the number set to contain all numbers from 1 to 100.

**Request:**
```http
POST /reset HTTP/1.1
Host: localhost:8000
```

**Response (Success - 200):**
```json
{
  "success": true,
  "message": "Number set has been reset to contain all numbers from 1 to 100",
  "total_numbers": 100
}
```

#### GET /status

Get the current status and state of the number set.

**Request:**
```http
GET /status HTTP/1.1
Host: localhost:8000
```

**Response (Success - 200):**
```json
{
  "total_numbers": 100,
  "remaining_count": 97,
  "extracted_count": 3,
  "extracted_numbers": [15, 42, 73],
  "is_complete": false,
  "can_find_missing": false
}
```

### Health and Monitoring Endpoints

#### GET /health

Comprehensive health check endpoint that verifies API functionality and dependencies.

**Request:**
```http
GET /health HTTP/1.1
Host: localhost:8000
```

**Response (Healthy - 200):**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "checks": {
    "api": "healthy",
    "database": "healthy",
    "number_set": "healthy"
  },
  "uptime_seconds": 3600,
  "request_count": 1250
}
```

**Response (Unhealthy - 503):**
```json
{
  "status": "unhealthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "checks": {
    "api": "healthy",
    "database": "unhealthy",
    "number_set": "healthy"
  },
  "errors": [
    "Database connection failed"
  ]
}
```

#### GET /errors/summary

Get error statistics and monitoring information.

**Request:**
```http
GET /errors/summary HTTP/1.1
Host: localhost:8000
```

**Response (Success - 200):**
```json
{
  "total_errors": 15,
  "error_rate": 0.012,
  "errors_by_type": {
    "NUMBER_OUT_OF_RANGE": 8,
    "NUMBER_ALREADY_EXTRACTED": 5,
    "NO_NUMBERS_EXTRACTED": 2
  },
  "errors_by_endpoint": {
    "/extract/{number}": 13,
    "/missing": 2
  },
  "last_error": {
    "timestamp": "2024-01-15T10:25:00Z",
    "error": "NUMBER_OUT_OF_RANGE",
    "endpoint": "/extract/150"
  }
}
```

## Data Models

### Request Models

#### ExtractRequest (Path Parameter)
```python
{
  "number": int  # Range: 1-100, required
}
```

### Response Models

#### ExtractResponse
```python
{
  "success": bool,
  "message": str,
  "extracted_number": int,
  "remaining_count": int
}
```

#### MissingNumberResponse
```python
{
  "missing_number": int,
  "calculation_method": str,
  "execution_time_ms": float,
  "extracted_numbers": List[int]
}
```

#### ResetResponse
```python
{
  "success": bool,
  "message": str,
  "total_numbers": int
}
```

#### StatusResponse
```python
{
  "total_numbers": int,
  "remaining_count": int,
  "extracted_count": int,
  "extracted_numbers": List[int],
  "is_complete": bool,
  "can_find_missing": bool
}
```

#### HealthResponse
```python
{
  "status": str,  # "healthy" | "unhealthy"
  "timestamp": str,  # ISO 8601 format
  "version": str,
  "checks": Dict[str, str],
  "uptime_seconds": int,
  "request_count": int,
  "errors": Optional[List[str]]
}
```

#### ErrorResponse
```python
{
  "error": str,  # Error code
  "message": str,  # Human-readable message
  "details": Dict[str, Any]  # Additional context
}
```

## Error Handling

### Error Codes

The API uses structured error codes for consistent error handling:

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `NUMBER_OUT_OF_RANGE` | 400 | Number is not between 1 and 100 |
| `NUMBER_ALREADY_EXTRACTED` | 409 | Number has already been extracted |
| `NO_NUMBERS_EXTRACTED` | 400 | No numbers extracted when trying to find missing |
| `MULTIPLE_NUMBERS_EXTRACTED` | 400 | Multiple numbers extracted when trying to find missing |
| `INVALID_INPUT` | 422 | Request validation failed |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

### Error Response Format

All errors follow a consistent structure:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "additional_context": "value",
    "relevant_data": "value"
  }
}
```

### HTTP Status Codes

| Status Code | Description | When Used |
|-------------|-------------|-----------|
| 200 | OK | Successful operation |
| 400 | Bad Request | Invalid input or business logic violation |
| 409 | Conflict | Resource conflict (e.g., number already extracted) |
| 422 | Unprocessable Entity | Request validation failed |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | Health check failed |

## Rate Limiting

Currently, the API does not implement rate limiting. In a production environment, consider implementing:

- **Request Rate Limiting**: Limit requests per minute/hour per IP
- **Burst Protection**: Prevent rapid successive requests
- **Resource Protection**: Limit concurrent operations

Example implementation considerations:
```python
# Example rate limiting headers (not currently implemented)
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

## Examples

### Complete Workflow Example

```bash
# 1. Check initial status
curl -X GET "http://localhost:8000/status"
# Response: {"total_numbers": 100, "remaining_count": 100, "extracted_count": 0, ...}

# 2. Extract a number
curl -X POST "http://localhost:8000/extract/42"
# Response: {"success": true, "message": "Successfully extracted number 42", ...}

# 3. Check status after extraction
curl -X GET "http://localhost:8000/status"
# Response: {"total_numbers": 100, "remaining_count": 99, "extracted_count": 1, ...}

# 4. Find the missing number
curl -X GET "http://localhost:8000/missing"
# Response: {"missing_number": 42, "calculation_method": "mathematical_sum", ...}

# 5. Reset the set
curl -X POST "http://localhost:8000/reset"
# Response: {"success": true, "message": "Number set has been reset...", ...}
```

### Error Handling Examples

```bash
# Extract number out of range
curl -X POST "http://localhost:8000/extract/150"
# Response: {"error": "NUMBER_OUT_OF_RANGE", "message": "Number 150 is outside valid range (1-100)", ...}

# Extract same number twice
curl -X POST "http://localhost:8000/extract/42"  # First time - success
curl -X POST "http://localhost:8000/extract/42"  # Second time - error
# Response: {"error": "NUMBER_ALREADY_EXTRACTED", "message": "Number 42 has already been extracted", ...}

# Find missing without extractions
curl -X POST "http://localhost:8000/reset"  # Reset first
curl -X GET "http://localhost:8000/missing"
# Response: {"error": "NO_NUMBERS_EXTRACTED", "message": "Cannot find missing number: no numbers have been extracted", ...}
```

### Python Client Example

```python
import requests
import json

class MissingNumberClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def extract_number(self, number: int):
        """Extract a number from the set."""
        response = requests.post(f"{self.base_url}/extract/{number}")
        return response.json()
    
    def find_missing(self):
        """Find the missing number."""
        response = requests.get(f"{self.base_url}/missing")
        return response.json()
    
    def reset_set(self):
        """Reset the number set."""
        response = requests.post(f"{self.base_url}/reset")
        return response.json()
    
    def get_status(self):
        """Get current status."""
        response = requests.get(f"{self.base_url}/status")
        return response.json()
    
    def health_check(self):
        """Check API health."""
        response = requests.get(f"{self.base_url}/health")
        return response.json()

# Usage example
client = MissingNumberClient()

# Extract a number
result = client.extract_number(42)
print(f"Extracted: {result}")

# Find missing number
missing = client.find_missing()
print(f"Missing number: {missing['missing_number']}")

# Reset for next use
client.reset_set()
```

### JavaScript Client Example

```javascript
class MissingNumberClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async extractNumber(number) {
        const response = await fetch(`${this.baseUrl}/extract/${number}`, {
            method: 'POST'
        });
        return await response.json();
    }
    
    async findMissing() {
        const response = await fetch(`${this.baseUrl}/missing`);
        return await response.json();
    }
    
    async resetSet() {
        const response = await fetch(`${this.baseUrl}/reset`, {
            method: 'POST'
        });
        return await response.json();
    }
    
    async getStatus() {
        const response = await fetch(`${this.baseUrl}/status`);
        return await response.json();
    }
    
    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/health`);
        return await response.json();
    }
}

// Usage example
const client = new MissingNumberClient();

async function demonstrateAPI() {
    try {
        // Extract a number
        const extracted = await client.extractNumber(42);
        console.log('Extracted:', extracted);
        
        // Find missing number
        const missing = await client.findMissing();
        console.log('Missing number:', missing.missing_number);
        
        // Reset for next use
        await client.resetSet();
        
    } catch (error) {
        console.error('API Error:', error);
    }
}

demonstrateAPI();
```

## SDKs and Libraries

### Official SDKs
Currently, no official SDKs are available. The API can be consumed using standard HTTP clients.

### Recommended Libraries

#### Python
- **requests**: For simple HTTP requests
- **httpx**: For async HTTP requests
- **aiohttp**: For async applications

#### JavaScript/Node.js
- **fetch**: Built-in browser API
- **axios**: Popular HTTP client
- **node-fetch**: Node.js fetch implementation

#### Other Languages
- **curl**: Command-line testing
- **Postman**: API testing and documentation
- **Insomnia**: API client and testing

### OpenAPI Code Generation

Generate client SDKs using the OpenAPI specification:

```bash
# Download OpenAPI spec
curl http://localhost:8000/openapi.json > openapi.json

# Generate Python client
openapi-generator generate -i openapi.json -g python -o python-client

# Generate JavaScript client
openapi-generator generate -i openapi.json -g javascript -o js-client

# Generate Java client
openapi-generator generate -i openapi.json -g java -o java-client
```

## Performance Considerations

### Algorithm Complexity
- **Extract Operation**: O(1) - Constant time
- **Missing Number Calculation**: O(1) - Mathematical sum approach
- **Status Check**: O(1) - Direct property access
- **Reset Operation**: O(n) - Recreates the set

### Optimization Tips
1. **Batch Operations**: For multiple extractions, consider implementing batch endpoints
2. **Caching**: Status information is cached for performance
3. **Connection Pooling**: Database connections are pooled for efficiency
4. **Async Operations**: API uses async/await for better concurrency

### Monitoring
- Request timing is automatically logged
- Performance metrics are available via health endpoints
- Error rates and patterns are tracked

## Security Considerations

### Current Implementation
- Input validation prevents injection attacks
- Error messages don't expose sensitive information
- Request logging excludes sensitive data

### Production Recommendations
1. **Authentication**: Implement API key or OAuth2
2. **Rate Limiting**: Prevent abuse and DoS attacks
3. **HTTPS**: Use TLS encryption in production
4. **CORS**: Configure appropriate CORS policies
5. **Input Sanitization**: Additional input validation
6. **Audit Logging**: Log all API access for security monitoring

## Changelog

### Version 1.0.0
- Initial API implementation
- Core missing number functionality
- Comprehensive error handling
- Health check endpoints
- OpenAPI documentation

### Future Enhancements
- Authentication and authorization
- Rate limiting
- Batch operations
- WebSocket support for real-time updates
- Additional mathematical algorithms
- Performance optimizations