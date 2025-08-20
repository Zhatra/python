#!/usr/bin/env python3
"""
Script to run the Missing Number API server.

This script starts the FastAPI application using uvicorn with proper configuration.
"""

import uvicorn
import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def main():
    """Run the FastAPI application."""
    print("Starting Missing Number API server...")
    print("API Documentation will be available at: http://localhost:8000/docs")
    print("Alternative docs at: http://localhost:8000/redoc")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()