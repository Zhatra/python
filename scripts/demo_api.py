#!/usr/bin/env python3
"""
Demo script for the Missing Number API.

This script demonstrates the functionality of the FastAPI application
by making requests to all endpoints and showing the responses.
"""

import requests
import json
import time
import sys
from typing import Dict, Any


class APIDemo:
    """Demo class for the Missing Number API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the demo with the API base URL."""
        self.base_url = base_url
        self.session = requests.Session()
    
    def print_response(self, endpoint: str, response: requests.Response) -> None:
        """Print a formatted response."""
        print(f"\n{'='*60}")
        print(f"Endpoint: {endpoint}")
        print(f"Status Code: {response.status_code}")
        print(f"Response:")
        try:
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print(response.text)
        print('='*60)
    
    def check_api_health(self) -> bool:
        """Check if the API is running and healthy."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ API is healthy and running")
                return True
            else:
                print(f"❌ API health check failed with status {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to API: {e}")
            print("Make sure the API server is running on http://localhost:8000")
            print("You can start it with: python scripts/run_api.py")
            return False
    
    def demo_basic_functionality(self) -> None:
        """Demonstrate basic API functionality."""
        print("\n🚀 Starting Missing Number API Demo")
        print("This demo will showcase all API endpoints and functionality")
        
        # 1. Get API information
        print("\n1. Getting API information...")
        response = self.session.get(f"{self.base_url}/")
        self.print_response("GET /", response)
        
        # 2. Check initial status
        print("\n2. Checking initial status...")
        response = self.session.get(f"{self.base_url}/status")
        self.print_response("GET /status", response)
        
        # 3. Extract a number
        print("\n3. Extracting number 42...")
        response = self.session.post(f"{self.base_url}/extract/42")
        self.print_response("POST /extract/42", response)
        
        # 4. Check status after extraction
        print("\n4. Checking status after extraction...")
        response = self.session.get(f"{self.base_url}/status")
        self.print_response("GET /status", response)
        
        # 5. Get missing number
        print("\n5. Getting the missing number...")
        response = self.session.get(f"{self.base_url}/missing")
        self.print_response("GET /missing", response)
        
        # 6. Reset the set
        print("\n6. Resetting the number set...")
        response = self.session.post(f"{self.base_url}/reset")
        self.print_response("POST /reset", response)
        
        # 7. Verify reset
        print("\n7. Verifying reset...")
        response = self.session.get(f"{self.base_url}/status")
        self.print_response("GET /status", response)
    
    def demo_error_handling(self) -> None:
        """Demonstrate error handling."""
        print("\n🔥 Demonstrating Error Handling")
        
        # 1. Try to extract invalid number (too low)
        print("\n1. Trying to extract number 0 (invalid)...")
        response = self.session.post(f"{self.base_url}/extract/0")
        self.print_response("POST /extract/0", response)
        
        # 2. Try to extract invalid number (too high)
        print("\n2. Trying to extract number 101 (invalid)...")
        response = self.session.post(f"{self.base_url}/extract/101")
        self.print_response("POST /extract/101", response)
        
        # 3. Try to get missing number without extractions
        print("\n3. Trying to get missing number without extractions...")
        response = self.session.get(f"{self.base_url}/missing")
        self.print_response("GET /missing", response)
        
        # 4. Extract a number and try to extract it again
        print("\n4. Extracting number 25...")
        response = self.session.post(f"{self.base_url}/extract/25")
        self.print_response("POST /extract/25", response)
        
        print("\n5. Trying to extract number 25 again (should fail)...")
        response = self.session.post(f"{self.base_url}/extract/25")
        self.print_response("POST /extract/25", response)
        
        # 6. Extract another number and try to get missing (should fail)
        print("\n6. Extracting another number (30)...")
        response = self.session.post(f"{self.base_url}/extract/30")
        self.print_response("POST /extract/30", response)
        
        print("\n7. Trying to get missing number with multiple extractions...")
        response = self.session.get(f"{self.base_url}/missing")
        self.print_response("GET /missing", response)
        
        # Reset for next demo
        self.session.post(f"{self.base_url}/reset")
    
    def demo_performance(self) -> None:
        """Demonstrate performance characteristics."""
        print("\n⚡ Performance Demonstration")
        
        # Test extraction performance
        print("\n1. Testing extraction performance...")
        numbers_to_test = [1, 25, 50, 75, 100]
        
        for num in numbers_to_test:
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/extract/{num}")
            end_time = time.time()
            
            if response.status_code == 200:
                print(f"   Extracted {num} in {(end_time - start_time)*1000:.2f}ms")
            else:
                print(f"   Failed to extract {num}")
            
            # Reset after each test
            self.session.post(f"{self.base_url}/reset")
        
        # Test missing number calculation performance
        print("\n2. Testing missing number calculation performance...")
        test_numbers = [7, 33, 66, 99]
        
        for num in test_numbers:
            # Extract the number
            self.session.post(f"{self.base_url}/extract/{num}")
            
            # Time the missing number calculation
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/missing")
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                api_time = data.get("execution_time_ms", 0)
                total_time = (end_time - start_time) * 1000
                print(f"   Missing number {num}: API={api_time:.2f}ms, Total={total_time:.2f}ms")
            
            # Reset for next test
            self.session.post(f"{self.base_url}/reset")
    
    def run_full_demo(self) -> None:
        """Run the complete demo."""
        if not self.check_api_health():
            return
        
        try:
            self.demo_basic_functionality()
            self.demo_error_handling()
            self.demo_performance()
            
            print("\n🎉 Demo completed successfully!")
            print(f"API Documentation: {self.base_url}/docs")
            print(f"Alternative Docs: {self.base_url}/redoc")
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Demo interrupted by user")
        except Exception as e:
            print(f"\n❌ Demo failed with error: {e}")


def main():
    """Main function to run the demo."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Demo the Missing Number API")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--basic-only",
        action="store_true",
        help="Run only basic functionality demo"
    )
    
    args = parser.parse_args()
    
    demo = APIDemo(args.url)
    
    if args.basic_only:
        if demo.check_api_health():
            demo.demo_basic_functionality()
    else:
        demo.run_full_demo()


if __name__ == "__main__":
    main()