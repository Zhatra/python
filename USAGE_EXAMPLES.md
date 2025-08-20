# Usage Examples and Tutorials

## Overview

This document provides comprehensive usage examples, tutorials, and practical guides for the Prueba Técnica Python project. It covers both the data processing pipeline and the Missing Number API with real-world scenarios and best practices.

## Table of Contents

- [Quick Start Examples](#quick-start-examples)
- [Data Processing Pipeline](#data-processing-pipeline)
- [Missing Number API](#missing-number-api)
- [Integration Examples](#integration-examples)
- [Advanced Usage](#advanced-usage)
- [Best Practices](#best-practices)
- [Common Workflows](#common-workflows)
- [Performance Optimization](#performance-optimization)

## Quick Start Examples

### 1. Complete System Setup

```bash
# Clone and setup the project
git clone <repository-url>
cd prueba-tecnica-python

# Quick deployment with Docker
./scripts/deploy.sh

# Verify everything is running
curl http://localhost:8000/health
```

### 2. Basic API Usage

```bash
# Extract a number
curl -X POST "http://localhost:8000/extract/42"

# Find the missing number
curl -X GET "http://localhost:8000/missing"

# Reset for next use
curl -X POST "http://localhost:8000/reset"
```

### 3. Data Processing Pipeline

```bash
# Run complete ETL pipeline
python scripts/run_complete_pipeline.py

# Or step by step
python scripts/demo_data_loader.py
python scripts/demo_data_extractor.py
python scripts/demo_data_transformer.py
python scripts/demo_schema_creation.py
```

## Data Processing Pipeline

### Complete ETL Workflow

#### Step 1: Data Loading

```python
# Load CSV data into raw database
from src.data_processing.loader import DataLoader
from src.database.connection import DatabaseConnection

# Initialize components
db_connection = DatabaseConnection()
loader = DataLoader(db_connection)

# Load CSV file
csv_path = "data/input/data_prueba_técnica.csv"
result = loader.load_csv_to_database(csv_path)

print(f"Loaded {result.total_rows} rows")
print(f"Success rate: {result.success_rate:.2f}%")

# Check for validation errors
if result.invalid_rows > 0:
    print(f"Found {result.invalid_rows} invalid rows")
    for error in result.errors[:5]:  # Show first 5 errors
        print(f"Row {error['row']}: {error['message']}")
```

#### Step 2: Data Extraction

```python
# Extract data to different formats
from src.data_processing.extractor import DataExtractor

extractor = DataExtractor(db_connection)

# Extract to CSV
csv_output = extractor.extract_to_csv("data/output/extracted_data.csv")
print(f"Extracted to CSV: {csv_output}")

# Extract to Parquet for better performance
parquet_output = extractor.extract_to_parquet("data/output/extracted_data.parquet")
print(f"Extracted to Parquet: {parquet_output}")

# Get extraction metadata
metadata = extractor.get_extraction_metadata()
print(f"Extracted {metadata['total_rows']} rows in {metadata['execution_time']:.2f}s")
```

#### Step 3: Data Transformation

```python
# Transform data to target schema
from src.data_processing.transformer import DataTransformer

transformer = DataTransformer("data/output/extracted_data.csv")

# Apply transformations
transformed_data = transformer.transform_to_schema()
print(f"Transformed {len(transformed_data)} records")

# Validate transformed data
validation_report = transformer.validate_transformed_data()
print(f"Validation success rate: {validation_report.success_rate:.2f}%")

# Apply business rules
cleaned_data = transformer.apply_business_rules()
print(f"Applied business rules to {len(cleaned_data)} records")
```

#### Step 4: Schema Creation and Data Loading

```python
# Create normalized schema and load data
from src.database.manager import DatabaseManager

db_manager = DatabaseManager(db_connection)

# Create normalized schema
schema_created = db_manager.create_normalized_schema()
print(f"Schema creation: {'Success' if schema_created else 'Failed'}")

# Load transformed data
load_result = db_manager.load_transformed_data(transformed_data)
print(f"Data loading: {'Success' if load_result else 'Failed'}")

# Create reporting views
view_created = db_manager.create_reporting_view()
print(f"Reporting view: {'Created' if view_created else 'Failed'}")
```

### Advanced Data Processing Examples

#### Batch Processing Large Files

```python
# Process large CSV files in batches
from src.data_processing.loader import DataLoader

loader = DataLoader(db_connection, batch_size=5000)

# Process with progress tracking
def progress_callback(processed, total):
    percentage = (processed / total) * 100
    print(f"Progress: {processed}/{total} ({percentage:.1f}%)")

result = loader.load_csv_to_database(
    csv_path="data/input/large_dataset.csv",
    progress_callback=progress_callback
)
```

#### Data Quality Analysis

```python
# Analyze data quality
from src.data_processing.analyzer import DataQualityAnalyzer

analyzer = DataQualityAnalyzer(db_connection)

# Generate data quality report
quality_report = analyzer.analyze_raw_data()

print("Data Quality Report:")
print(f"Total records: {quality_report.total_records}")
print(f"Complete records: {quality_report.complete_records}")
print(f"Duplicate records: {quality_report.duplicate_records}")
print(f"Invalid amounts: {quality_report.invalid_amounts}")
print(f"Invalid dates: {quality_report.invalid_dates}")

# Get detailed error breakdown
error_breakdown = analyzer.get_error_breakdown()
for error_type, count in error_breakdown.items():
    print(f"{error_type}: {count} occurrences")
```

#### Custom Transformation Rules

```python
# Define custom transformation rules
from src.data_processing.transformer import DataTransformer

class CustomTransformer(DataTransformer):
    def apply_custom_rules(self, data):
        """Apply custom business rules."""
        # Convert status to lowercase
        data['status'] = data['status'].str.lower()

        # Standardize company names
        data['company_name'] = data['company_name'].str.title()

        # Handle special amount cases
        data.loc[data['amount'] < 0, 'status'] = 'refunded'
        data['amount'] = data['amount'].abs()

        # Add derived fields
        data['amount_category'] = pd.cut(
            data['amount'],
            bins=[0, 100, 1000, 10000, float('inf')],
            labels=['small', 'medium', 'large', 'enterprise']
        )

        return data

# Use custom transformer
transformer = CustomTransformer("data/output/extracted_data.csv")
transformed_data = transformer.apply_custom_rules(transformer.data)
```

## Missing Number API

### Basic API Operations

#### Python Client Example

```python
import requests
import json
from typing import Optional, Dict, Any

class MissingNumberClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()

    def extract_number(self, number: int) -> Dict[str, Any]:
        """Extract a number from the set."""
        response = self.session.post(f"{self.base_url}/extract/{number}")
        response.raise_for_status()
        return response.json()

    def find_missing(self) -> Dict[str, Any]:
        """Find the missing number."""
        response = self.session.get(f"{self.base_url}/missing")
        response.raise_for_status()
        return response.json()

    def reset_set(self) -> Dict[str, Any]:
        """Reset the number set."""
        response = self.session.post(f"{self.base_url}/reset")
        response.raise_for_status()
        return response.json()

    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        response = self.session.get(f"{self.base_url}/status")
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

# Usage example
def demonstrate_api():
    client = MissingNumberClient()

    try:
        # Check initial status
        status = client.get_status()
        print(f"Initial status: {status['remaining_count']} numbers remaining")

        # Extract a number
        result = client.extract_number(42)
        print(f"Extracted: {result['extracted_number']}")

        # Check status after extraction
        status = client.get_status()
        print(f"After extraction: {status['remaining_count']} numbers remaining")

        # Find missing number
        missing = client.find_missing()
        print(f"Missing number: {missing['missing_number']}")
        print(f"Calculation time: {missing['execution_time_ms']:.2f}ms")

        # Reset for next use
        reset_result = client.reset_set()
        print(f"Reset: {reset_result['message']}")

    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e.response.json()}")

if __name__ == "__main__":
    demonstrate_api()
```

#### JavaScript/Node.js Client Example

```javascript
const axios = require("axios");

class MissingNumberClient {
  constructor(baseUrl = "http://localhost:8000") {
    this.baseUrl = baseUrl;
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: 5000,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  async extractNumber(number) {
    try {
      const response = await this.client.post(`/extract/${number}`);
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async findMissing() {
    try {
      const response = await this.client.get("/missing");
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async resetSet() {
    try {
      const response = await this.client.post("/reset");
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async getStatus() {
    try {
      const response = await this.client.get("/status");
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  async healthCheck() {
    try {
      const response = await this.client.get("/health");
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }

  handleError(error) {
    if (error.response) {
      return new Error(
        `API Error: ${error.response.data.message || error.response.statusText}`
      );
    } else if (error.request) {
      return new Error("Network Error: No response received");
    } else {
      return new Error(`Request Error: ${error.message}`);
    }
  }
}

// Usage example
async function demonstrateAPI() {
  const client = new MissingNumberClient();

  try {
    // Check health
    const health = await client.healthCheck();
    console.log(`API Status: ${health.status}`);

    // Get initial status
    let status = await client.getStatus();
    console.log(`Initial: ${status.remaining_count} numbers remaining`);

    // Extract multiple numbers
    const numbersToExtract = [15, 42, 73];
    for (const number of numbersToExtract) {
      const result = await client.extractNumber(number);
      console.log(`Extracted ${result.extracted_number}: ${result.message}`);
    }

    // Check status
    status = await client.getStatus();
    console.log(
      `Extracted ${status.extracted_count} numbers: ${status.extracted_numbers}`
    );

    // Try to find missing (should fail with multiple extractions)
    try {
      await client.findMissing();
    } catch (error) {
      console.log(`Expected error: ${error.message}`);
    }

    // Reset and try single extraction
    await client.resetSet();
    await client.extractNumber(99);

    const missing = await client.findMissing();
    console.log(`Missing number: ${missing.missing_number}`);
  } catch (error) {
    console.error("Demo failed:", error.message);
  }
}

// Run the demo
demonstrateAPI();
```

### Advanced API Usage

#### Batch Operations Simulation

```python
# Simulate batch operations for testing
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def batch_extract_test(client, numbers_to_extract):
    """Test extracting multiple numbers."""
    results = []

    for number in numbers_to_extract:
        try:
            result = client.extract_number(number)
            results.append({
                'number': number,
                'success': True,
                'result': result
            })
        except Exception as e:
            results.append({
                'number': number,
                'success': False,
                'error': str(e)
            })

    return results

def performance_test(client, num_operations=100):
    """Test API performance."""
    times = []

    for i in range(num_operations):
        # Reset for each test
        client.reset_set()

        # Extract random number
        number = random.randint(1, 100)
        start_time = time.time()

        try:
            client.extract_number(number)
            client.find_missing()
            end_time = time.time()
            times.append(end_time - start_time)
        except Exception as e:
            print(f"Error in iteration {i}: {e}")

    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)

        print(f"Performance Test Results ({num_operations} operations):")
        print(f"Average time: {avg_time:.3f}s")
        print(f"Min time: {min_time:.3f}s")
        print(f"Max time: {max_time:.3f}s")

# Run performance test
client = MissingNumberClient()
performance_test(client, 50)
```

#### Error Handling Examples

```python
def robust_api_client():
    """Example of robust API client with error handling."""
    client = MissingNumberClient()

    def safe_extract(number, max_retries=3):
        """Extract with retry logic."""
        for attempt in range(max_retries):
            try:
                return client.extract_number(number)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 409:  # Already extracted
                    print(f"Number {number} already extracted")
                    return None
                elif e.response.status_code == 400:  # Out of range
                    print(f"Number {number} is out of range")
                    return None
                elif attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(0.5)
                else:
                    print(f"Failed after {max_retries} attempts")
                    raise
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"Network error, retrying... ({e})")
                    time.sleep(1)
                else:
                    raise

    def safe_find_missing():
        """Find missing with proper error handling."""
        try:
            return client.find_missing()
        except requests.exceptions.HTTPError as e:
            error_data = e.response.json()
            if error_data.get('error') == 'NO_NUMBERS_EXTRACTED':
                print("No numbers have been extracted yet")
                return None
            elif error_data.get('error') == 'MULTIPLE_NUMBERS_EXTRACTED':
                print(f"Multiple numbers extracted: {error_data['details']['extracted_numbers']}")
                return None
            else:
                raise

    # Example usage
    numbers = [15, 42, 150, 42, 73]  # Include invalid and duplicate

    for number in numbers:
        result = safe_extract(number)
        if result:
            print(f"Successfully extracted {number}")

    missing = safe_find_missing()
    if missing:
        print(f"Missing number: {missing['missing_number']}")

robust_api_client()
```

## Integration Examples

### Web Application Integration

#### Flask Web App Example

```python
from flask import Flask, render_template, request, jsonify, flash
import requests

app = Flask(__name__)
app.secret_key = 'your-secret-key'

class APIClient:
    def __init__(self):
        self.base_url = "http://localhost:8000"

    def extract_number(self, number):
        response = requests.post(f"{self.base_url}/extract/{number}")
        return response.json(), response.status_code

    def find_missing(self):
        response = requests.get(f"{self.base_url}/missing")
        return response.json(), response.status_code

    def get_status(self):
        response = requests.get(f"{self.base_url}/status")
        return response.json(), response.status_code

    def reset_set(self):
        response = requests.post(f"{self.base_url}/reset")
        return response.json(), response.status_code

api_client = APIClient()

@app.route('/')
def index():
    status, _ = api_client.get_status()
    return render_template('index.html', status=status)

@app.route('/extract', methods=['POST'])
def extract():
    number = request.form.get('number', type=int)

    if not number or number < 1 or number > 100:
        flash('Please enter a number between 1 and 100', 'error')
        return redirect('/')

    result, status_code = api_client.extract_number(number)

    if status_code == 200:
        flash(f'Successfully extracted number {number}', 'success')
    else:
        flash(result.get('message', 'Error extracting number'), 'error')

    return redirect('/')

@app.route('/missing')
def missing():
    result, status_code = api_client.find_missing()

    if status_code == 200:
        return jsonify(result)
    else:
        return jsonify(result), status_code

@app.route('/reset', methods=['POST'])
def reset():
    result, _ = api_client.reset_set()
    flash('Number set has been reset', 'info')
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

#### React Frontend Example

```jsx
import React, { useState, useEffect } from "react";
import axios from "axios";

const MissingNumberApp = () => {
  const [status, setStatus] = useState(null);
  const [inputNumber, setInputNumber] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  const API_BASE = "http://localhost:8000";

  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE}/status`);
      setStatus(response.data);
    } catch (error) {
      setMessage("Error fetching status");
    }
  };

  const extractNumber = async () => {
    if (!inputNumber || inputNumber < 1 || inputNumber > 100) {
      setMessage("Please enter a number between 1 and 100");
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/extract/${inputNumber}`);
      setMessage(`Successfully extracted ${inputNumber}`);
      setInputNumber("");
      fetchStatus();
    } catch (error) {
      const errorMsg =
        error.response?.data?.message || "Error extracting number";
      setMessage(errorMsg);
    }
    setLoading(false);
  };

  const findMissing = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API_BASE}/missing`);
      setMessage(`Missing number is: ${response.data.missing_number}`);
    } catch (error) {
      const errorMsg =
        error.response?.data?.message || "Error finding missing number";
      setMessage(errorMsg);
    }
    setLoading(false);
  };

  const resetSet = async () => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/reset`);
      setMessage("Number set has been reset");
      fetchStatus();
    } catch (error) {
      setMessage("Error resetting set");
    }
    setLoading(false);
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-3xl font-bold mb-6">Missing Number API Demo</h1>

      {status && (
        <div className="bg-blue-100 p-4 rounded mb-4">
          <h2 className="text-xl font-semibold mb-2">Current Status</h2>
          <p>Remaining numbers: {status.remaining_count}</p>
          <p>Extracted numbers: {status.extracted_numbers.join(", ")}</p>
        </div>
      )}

      <div className="mb-4">
        <input
          type="number"
          min="1"
          max="100"
          value={inputNumber}
          onChange={(e) => setInputNumber(e.target.value)}
          placeholder="Enter number (1-100)"
          className="border p-2 mr-2"
        />
        <button
          onClick={extractNumber}
          disabled={loading}
          className="bg-blue-500 text-white px-4 py-2 rounded disabled:opacity-50"
        >
          Extract Number
        </button>
      </div>

      <div className="mb-4">
        <button
          onClick={findMissing}
          disabled={loading}
          className="bg-green-500 text-white px-4 py-2 rounded mr-2 disabled:opacity-50"
        >
          Find Missing
        </button>
        <button
          onClick={resetSet}
          disabled={loading}
          className="bg-red-500 text-white px-4 py-2 rounded disabled:opacity-50"
        >
          Reset Set
        </button>
      </div>

      {message && (
        <div className="bg-yellow-100 p-4 rounded">
          <p>{message}</p>
        </div>
      )}
    </div>
  );
};

export default MissingNumberApp;
```

### Database Integration Examples

#### Direct Database Queries

```python
# Query the database directly for reporting
from src.database.connection import DatabaseConnection
import pandas as pd

def generate_business_report():
    """Generate comprehensive business report."""
    db_connection = DatabaseConnection()

    # Daily summary query
    daily_summary_query = """
    SELECT
        transaction_date,
        company_name,
        total_amount,
        transaction_count,
        success_rate_percent
    FROM normalized_data.daily_transaction_summary
    WHERE transaction_date >= CURRENT_DATE - INTERVAL '30 days'
    ORDER BY transaction_date DESC, total_amount DESC;
    """

    # Company performance query
    company_performance_query = """
    SELECT
        c.company_name,
        COUNT(ch.id) as total_transactions,
        SUM(ch.amount) as total_amount,
        AVG(ch.amount) as avg_amount,
        COUNT(CASE WHEN ch.status = 'paid' THEN 1 END) as paid_count,
        ROUND(
            (COUNT(CASE WHEN ch.status = 'paid' THEN 1 END)::DECIMAL / COUNT(*)) * 100,
            2
        ) as success_rate
    FROM normalized_data.companies c
    LEFT JOIN normalized_data.charges ch ON c.company_id = ch.company_id
    GROUP BY c.company_id, c.company_name
    ORDER BY total_amount DESC;
    """

    with db_connection.get_session() as session:
        # Execute queries
        daily_df = pd.read_sql(daily_summary_query, session.bind)
        company_df = pd.read_sql(company_performance_query, session.bind)

        # Generate report
        print("=== BUSINESS REPORT ===")
        print(f"\nDaily Summary (Last 30 days):")
        print(daily_df.head(10).to_string(index=False))

        print(f"\nCompany Performance:")
        print(company_df.to_string(index=False))

        # Export to files
        daily_df.to_csv('reports/daily_summary.csv', index=False)
        company_df.to_csv('reports/company_performance.csv', index=False)

        return daily_df, company_df

# Generate report
daily_data, company_data = generate_business_report()
```

## Advanced Usage

### Custom Extensions

#### Custom Data Validator

```python
# Create custom data validator
from src.validation import InputValidator, ValidationResult
from typing import Dict, Any

class CustomBusinessValidator(InputValidator):
    """Custom validator with business-specific rules."""

    @staticmethod
    def validate_business_transaction(record: Dict[str, Any]) -> ValidationResult:
        """Validate transaction with custom business rules."""
        errors = []
        warnings = []
        cleaned_record = record.copy()

        # Custom amount validation
        if 'amount' in record:
            amount = record['amount']
            if isinstance(amount, str):
                try:
                    amount = float(amount)
                    cleaned_record['amount'] = amount
                except ValueError:
                    errors.append("Invalid amount format")

            if amount and amount > 100000:
                warnings.append("Large transaction amount detected")
            elif amount and amount < 0.01:
                errors.append("Amount too small")

        # Custom status validation
        if 'status' in record:
            status = record['status'].lower() if record['status'] else ''
            valid_statuses = ['paid', 'pending', 'failed', 'refunded', 'cancelled']

            if status not in valid_statuses:
                errors.append(f"Invalid status: {status}")
            else:
                cleaned_record['status'] = status

        # Business rule: refunded amounts should be negative
        if (cleaned_record.get('status') == 'refunded' and
            cleaned_record.get('amount', 0) > 0):
            warnings.append("Refunded transaction with positive amount")

        # Weekend transaction warning
        if 'created_at' in record:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(record['created_at'].replace('Z', '+00:00'))
                if dt.weekday() >= 5:  # Saturday or Sunday
                    warnings.append("Weekend transaction")
            except:
                pass

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            cleaned_value=cleaned_record
        )

# Usage
validator = CustomBusinessValidator()
record = {
    'amount': '1500.50',
    'status': 'PAID',
    'created_at': '2024-01-13T10:30:00Z'  # Saturday
}

result = validator.validate_business_transaction(record)
print(f"Valid: {result.is_valid}")
print(f"Warnings: {result.warnings}")
print(f"Cleaned: {result.cleaned_value}")
```

#### Custom API Middleware

```python
# Add custom middleware for API monitoring
from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
import time
import logging

class APIMonitoringMiddleware(BaseHTTPMiddleware):
    """Custom middleware for API monitoring and logging."""

    def __init__(self, app: FastAPI):
        super().__init__(app)
        self.logger = logging.getLogger("api.monitoring")

    async def dispatch(self, request: Request, call_next):
        # Start timing
        start_time = time.time()

        # Log request
        self.logger.info(f"Request: {request.method} {request.url.path}")

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        self.logger.info(
            f"Response: {response.status_code} "
            f"Duration: {duration:.3f}s "
            f"Path: {request.url.path}"
        )

        # Add custom headers
        response.headers["X-Process-Time"] = str(duration)
        response.headers["X-API-Version"] = "1.0.0"

        return response

# Add to FastAPI app
from src.api.main import app
app.add_middleware(APIMonitoringMiddleware)
```

### Performance Optimization Examples

#### Database Connection Pooling

```python
# Optimize database connections
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
from src.config import get_database_url

def create_optimized_engine():
    """Create optimized database engine with connection pooling."""
    database_url = get_database_url()

    engine = create_engine(
        database_url,
        poolclass=QueuePool,
        pool_size=20,          # Number of connections to maintain
        max_overflow=30,       # Additional connections when needed
        pool_pre_ping=True,    # Validate connections before use
        pool_recycle=3600,     # Recycle connections every hour
        echo=False             # Set to True for SQL debugging
    )

    return engine

# Usage in application
engine = create_optimized_engine()
```

#### Async Data Processing

```python
# Async data processing for better performance
import asyncio
import aiofiles
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

async def async_data_processor():
    """Process data asynchronously for better performance."""

    async def load_csv_async(file_path: str) -> pd.DataFrame:
        """Load CSV file asynchronously."""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            df = await loop.run_in_executor(executor, pd.read_csv, file_path)
        return df

    async def process_chunk_async(chunk: pd.DataFrame) -> pd.DataFrame:
        """Process data chunk asynchronously."""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            # Simulate heavy processing
            processed = await loop.run_in_executor(
                executor,
                lambda: chunk.apply(lambda x: x.str.upper() if x.dtype == 'object' else x)
            )
        return processed

    # Load data
    df = await load_csv_async("data/input/data_prueba_técnica.csv")

    # Process in chunks
    chunk_size = 1000
    chunks = [df[i:i+chunk_size] for i in range(0, len(df), chunk_size)]

    # Process chunks concurrently
    tasks = [process_chunk_async(chunk) for chunk in chunks]
    processed_chunks = await asyncio.gather(*tasks)

    # Combine results
    result = pd.concat(processed_chunks, ignore_index=True)
    return result

# Run async processing
async def main():
    result = await async_data_processor()
    print(f"Processed {len(result)} records asynchronously")

# asyncio.run(main())
```

## Best Practices

### Error Handling Best Practices

```python
# Comprehensive error handling example
import logging
from contextlib import contextmanager
from typing import Optional, Any

class RobustDataProcessor:
    """Data processor with comprehensive error handling."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_count = 0
        self.warning_count = 0

    @contextmanager
    def error_handling_context(self, operation_name: str):
        """Context manager for consistent error handling."""
        try:
            self.logger.info(f"Starting {operation_name}")
            yield
            self.logger.info(f"Completed {operation_name}")
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Error in {operation_name}: {str(e)}", exc_info=True)
            raise

    def process_with_recovery(self, data: Any, max_retries: int = 3) -> Optional[Any]:
        """Process data with retry logic and recovery."""
        for attempt in range(max_retries):
            try:
                with self.error_handling_context(f"Processing attempt {attempt + 1}"):
                    return self._process_data(data)
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error(f"All {max_retries} attempts failed")
                    return None

    def _process_data(self, data: Any) -> Any:
        """Actual data processing logic."""
        # Simulate processing that might fail
        if random.random() < 0.1:  # 10% failure rate
            raise Exception("Random processing error")
        return data

# Usage
processor = RobustDataProcessor()
result = processor.process_with_recovery(sample_data)
```

### Configuration Management

```python
# Centralized configuration management
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    host: str
    port: int
    name: str
    user: str
    password: str
    pool_size: int = 10
    max_overflow: int = 20

@dataclass
class APIConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    reload: bool = False

@dataclass
class ProcessingConfig:
    batch_size: int = 1000
    max_workers: int = 4
    validation_level: str = "strict"
    error_threshold: float = 0.05

@dataclass
class AppConfig:
    database: DatabaseConfig
    api: APIConfig
    processing: ProcessingConfig
    log_level: str = "INFO"
    environment: str = "development"

def load_config() -> AppConfig:
    """Load configuration from environment variables."""
    return AppConfig(
        database=DatabaseConfig(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            name=os.getenv("DB_NAME", "prueba_tecnica"),
            user=os.getenv("DB_USER", "testuser"),
            password=os.getenv("DB_PASSWORD", "testpass"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20"))
        ),
        api=APIConfig(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            workers=int(os.getenv("API_WORKERS", "1")),
            reload=os.getenv("API_RELOAD", "false").lower() == "true"
        ),
        processing=ProcessingConfig(
            batch_size=int(os.getenv("BATCH_SIZE", "1000")),
            max_workers=int(os.getenv("MAX_WORKERS", "4")),
            validation_level=os.getenv("VALIDATION_LEVEL", "strict"),
            error_threshold=float(os.getenv("ERROR_THRESHOLD", "0.05"))
        ),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        environment=os.getenv("ENVIRONMENT", "development")
    )

# Usage
config = load_config()
print(f"Database: {config.database.host}:{config.database.port}")
print(f"API: {config.api.host}:{config.api.port}")
```

## Common Workflows

### Complete Development Workflow

```bash
#!/bin/bash
# Complete development workflow script

echo "=== Prueba Técnica Python - Development Workflow ==="

# 1. Environment setup
echo "1. Setting up environment..."
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Database setup
echo "2. Setting up database..."
docker-compose up database -d
sleep 10  # Wait for database to start

# 3. Run data processing pipeline
echo "3. Running data processing pipeline..."
python scripts/demo_data_loader.py
python scripts/demo_data_extractor.py
python scripts/demo_data_transformer.py
python scripts/demo_schema_creation.py
python scripts/demo_reporting_views.py

# 4. Start API
echo "4. Starting API..."
python scripts/run_api.py &
API_PID=$!
sleep 5  # Wait for API to start

# 5. Run API tests
echo "5. Testing API..."
python scripts/demo_api.py

# 6. Run test suite
echo "6. Running tests..."
pytest --cov=src --cov-report=html

# 7. Generate documentation
echo "7. Generating documentation..."
# Documentation is already created

# 8. Cleanup
echo "8. Cleaning up..."
kill $API_PID
docker-compose down

echo "=== Workflow completed successfully ==="
```

### Production Deployment Workflow

```bash
#!/bin/bash
# Production deployment workflow

echo "=== Production Deployment Workflow ==="

# 1. Pre-deployment checks
echo "1. Running pre-deployment checks..."
./scripts/validate-docker.sh

# 2. Backup existing data
echo "2. Creating backup..."
./scripts/docker-manage.sh backup

# 3. Deploy production environment
echo "3. Deploying production environment..."
./scripts/deploy.sh --environment production --profile api

# 4. Health checks
echo "4. Running health checks..."
sleep 30  # Wait for services to start
curl -f http://localhost:8000/health || exit 1

# 5. Smoke tests
echo "5. Running smoke tests..."
python scripts/production_smoke_tests.py

# 6. Monitor deployment
echo "6. Monitoring deployment..."
./scripts/docker-manage.sh status
./scripts/docker-manage.sh health

echo "=== Production deployment completed ==="
```

This comprehensive usage guide provides practical examples and tutorials for effectively using the Prueba Técnica Python project in various scenarios, from basic operations to advanced integrations and production deployments.
