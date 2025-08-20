"""
API workflow integration tests.

This module contains comprehensive integration tests for the NumberSet API
workflow, testing complete user scenarios and API interactions.
"""

import pytest
import asyncio
import time
import concurrent.futures
from typing import List, Dict, Any
from fastapi.testclient import TestClient

from src.api.main import app, number_set
from src.api.number_set import NumberSet


class TestAPIWorkflowIntegration:
    """Integration tests for complete API workflows."""
    
    @pytest.fixture
    def client(self):
        """Create a test client with fresh state."""
        with TestClient(app) as client:
            # Reset the number set before each test
            client.post("/reset")
            yield client
    
    def test_complete_single_number_workflow(self, client):
        """Test complete workflow for single number extraction and finding."""
        # Step 1: Verify initial state
        response = client.get("/status")
        assert response.status_code == 200
        initial_status = response.json()
        assert initial_status["extracted_count"] == 0
        assert len(initial_status["extracted_numbers"]) == 0
        assert initial_status["remaining_count"] == 100
        
        # Step 2: Extract a number
        extract_number = 42
        response = client.post(f"/extract/{extract_number}")
        assert response.status_code == 200
        
        extract_data = response.json()
        assert extract_data["success"] is True
        assert extract_data["extracted_number"] == extract_number
        assert extract_data["remaining_count"] == 99
        
        # Step 3: Verify state after extraction
        response = client.get("/status")
        assert response.status_code == 200
        status_after_extract = response.json()
        assert status_after_extract["extracted_count"] == 1
        assert extract_number in status_after_extract["extracted_numbers"]
        assert status_after_extract["remaining_count"] == 99
        
        # Step 4: Find missing number
        response = client.get("/missing")
        assert response.status_code == 200
        
        missing_data = response.json()
        assert missing_data["missing_number"] == extract_number
        assert missing_data["calculation_method"] == "mathematical_sum"
        assert "execution_time_ms" in missing_data
        assert missing_data["execution_time_ms"] >= 0
        
        # Step 5: Reset and verify
        response = client.post("/reset")
        assert response.status_code == 200
        
        reset_data = response.json()
        assert reset_data["success"] is True
        assert "Number set has been reset" in reset_data["message"]
        
        # Step 6: Verify state after reset
        response = client.get("/status")
        assert response.status_code == 200
        final_status = response.json()
        assert final_status["extracted_count"] == 0
        assert len(final_status["extracted_numbers"]) == 0
        assert final_status["remaining_count"] == 100
    
    def test_multiple_extractions_workflow(self, client):
        """Test workflow with multiple number extractions."""
        numbers_to_extract = [1, 25, 50, 75, 100]
        
        # Extract multiple numbers
        for i, number in enumerate(numbers_to_extract):
            response = client.post(f"/extract/{number}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["extracted_number"] == number
            assert data["remaining_count"] == 100 - (i + 1)
        
        # Verify final state
        response = client.get("/status")
        assert response.status_code == 200
        
        status = response.json()
        assert status["extracted_count"] == 5
        assert set(status["extracted_numbers"]) == set(numbers_to_extract)
        assert status["remaining_count"] == 95
        
        # Try to get missing number (should fail with multiple extractions)
        response = client.get("/missing")
        assert response.status_code == 422
        
        error_data = response.json()
        assert error_data["error"] == "MULTIPLE_NUMBERS_EXTRACTED"
        assert error_data["details"]["extracted_count"] == 5
    
    def test_error_recovery_workflow(self, client):
        """Test API error recovery and continued functionality."""
        # Step 1: Successful extraction
        response = client.post("/extract/30")
        assert response.status_code == 200
        
        # Step 2: Attempt invalid extraction (out of range)
        response = client.post("/extract/150")
        assert response.status_code == 400
        assert response.json()["error"] == "NUMBER_OUT_OF_RANGE"
        
        # Step 3: Attempt duplicate extraction
        response = client.post("/extract/30")
        assert response.status_code == 409
        assert response.json()["error"] == "NUMBER_ALREADY_EXTRACTED"
        
        # Step 4: Verify state is still consistent
        response = client.get("/status")
        assert response.status_code == 200
        status = response.json()
        assert status["extracted_count"] == 1
        assert 30 in status["extracted_numbers"]
        
        # Step 5: Continue with valid operations
        response = client.post("/extract/60")
        assert response.status_code == 200
        
        # Step 6: Try to get missing number (should fail with multiple)
        response = client.get("/missing")
        assert response.status_code == 422
        
        # Step 7: Reset and continue
        response = client.post("/reset")
        assert response.status_code == 200
        
        # Step 8: Extract single number and find missing
        response = client.post("/extract/77")
        assert response.status_code == 200
        
        response = client.get("/missing")
        assert response.status_code == 200
        assert response.json()["missing_number"] == 77
    
    def test_boundary_values_workflow(self, client):
        """Test workflow with boundary values."""
        # Test minimum value
        response = client.post("/extract/1")
        assert response.status_code == 200
        
        response = client.get("/missing")
        assert response.status_code == 200
        assert response.json()["missing_number"] == 1
        
        # Reset and test maximum value
        client.post("/reset")
        
        response = client.post("/extract/100")
        assert response.status_code == 200
        
        response = client.get("/missing")
        assert response.status_code == 200
        assert response.json()["missing_number"] == 100
        
        # Test invalid boundary values
        client.post("/reset")
        
        response = client.post("/extract/0")
        assert response.status_code == 400
        
        response = client.post("/extract/101")
        assert response.status_code == 400
    
    def test_performance_workflow(self, client):
        """Test API performance with various operations."""
        # Test extraction performance
        start_time = time.time()
        
        for i in range(1, 11):  # Extract 10 numbers
            response = client.post(f"/extract/{i}")
            assert response.status_code == 200
        
        extraction_time = time.time() - start_time
        assert extraction_time < 5.0  # Should complete within 5 seconds
        
        # Test status retrieval performance
        start_time = time.time()
        
        for _ in range(10):  # Get status 10 times
            response = client.get("/status")
            assert response.status_code == 200
        
        status_time = time.time() - start_time
        assert status_time < 2.0  # Should complete within 2 seconds
        
        # Test reset performance
        start_time = time.time()
        
        response = client.post("/reset")
        assert response.status_code == 200
        
        reset_time = time.time() - start_time
        assert reset_time < 1.0  # Should complete within 1 second
        
        # Test single number workflow performance
        start_time = time.time()
        
        client.post("/extract/50")
        response = client.get("/missing")
        assert response.status_code == 200
        
        workflow_time = time.time() - start_time
        assert workflow_time < 1.0  # Should complete within 1 second
        
        # Verify execution time is reported
        data = response.json()
        assert data["execution_time_ms"] < 100  # Should be very fast
    
    def test_concurrent_api_access(self, client):
        """Test API behavior under concurrent access."""
        import threading
        import queue
        
        results = queue.Queue()
        errors = queue.Queue()
        
        def extract_number(number: int):
            """Extract a number and store result."""
            try:
                response = client.post(f"/extract/{number}")
                results.put((number, response.status_code, response.json()))
            except Exception as e:
                errors.put((number, str(e)))
        
        # Reset first
        client.post("/reset")
        
        # Create threads for concurrent extractions
        threads = []
        numbers = [10, 20, 30, 40, 50]
        
        for number in numbers:
            thread = threading.Thread(target=extract_number, args=(number,))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert errors.empty(), f"Errors occurred: {list(errors.queue)}"
        
        successful_extractions = []
        while not results.empty():
            number, status_code, data = results.get()
            if status_code == 200:
                successful_extractions.append(number)
        
        # All extractions should succeed
        assert len(successful_extractions) == 5
        assert set(successful_extractions) == set(numbers)
        
        # Verify final state
        response = client.get("/status")
        assert response.status_code == 200
        status = response.json()
        assert status["extracted_count"] == 5
        assert set(status["extracted_numbers"]) == set(numbers)
    
    def test_api_state_persistence_across_requests(self, client):
        """Test that API state persists correctly across multiple requests."""
        # Simulate multiple client sessions
        session_1_extractions = [5, 15, 25]
        session_2_extractions = [35, 45, 55]
        
        # Session 1: Extract some numbers
        for number in session_1_extractions:
            response = client.post(f"/extract/{number}")
            assert response.status_code == 200
        
        # Verify state
        response = client.get("/status")
        assert response.status_code == 200
        status = response.json()
        assert status["extracted_count"] == 3
        assert set(status["extracted_numbers"]) == set(session_1_extractions)
        
        # Session 2: Extract more numbers (simulating different client)
        for number in session_2_extractions:
            response = client.post(f"/extract/{number}")
            assert response.status_code == 200
        
        # Verify combined state
        response = client.get("/status")
        assert response.status_code == 200
        status = response.json()
        assert status["extracted_count"] == 6
        expected_numbers = session_1_extractions + session_2_extractions
        assert set(status["extracted_numbers"]) == set(expected_numbers)
        
        # Try to extract already extracted number from session 1
        response = client.post(f"/extract/{session_1_extractions[0]}")
        assert response.status_code == 409
        assert response.json()["error"] == "NUMBER_ALREADY_EXTRACTED"
    
    def test_api_documentation_and_schema_validation(self, client):
        """Test API documentation and schema validation."""
        # Test OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "info" in schema
        assert "paths" in schema
        assert "components" in schema
        
        # Verify required endpoints are documented
        paths = schema["paths"]
        assert "/extract/{number}" in paths
        assert "/missing" in paths
        assert "/status" in paths
        assert "/reset" in paths
        
        # Test that endpoints match schema
        # Extract endpoint
        extract_path = paths["/extract/{number}"]
        assert "post" in extract_path
        
        # Missing endpoint
        missing_path = paths["/missing"]
        assert "get" in missing_path
        
        # Status endpoint
        status_path = paths["/status"]
        assert "get" in status_path
        
        # Reset endpoint
        reset_path = paths["/reset"]
        assert "post" in reset_path
    
    def test_complete_user_scenario_workflow(self, client):
        """Test complete user scenario from start to finish."""
        # Scenario: User wants to find a missing number after extracting one
        
        # Step 1: User checks initial status
        response = client.get("/status")
        assert response.status_code == 200
        initial_status = response.json()
        assert initial_status["extracted_count"] == 0
        
        # Step 2: User extracts their chosen number
        chosen_number = 73
        response = client.post(f"/extract/{chosen_number}")
        assert response.status_code == 200
        
        extract_result = response.json()
        assert extract_result["success"] is True
        assert extract_result["extracted_number"] == chosen_number
        
        # Step 3: User checks status to confirm
        response = client.get("/status")
        assert response.status_code == 200
        status = response.json()
        assert chosen_number in status["extracted_numbers"]
        
        # Step 4: User gets the missing number
        response = client.get("/missing")
        assert response.status_code == 200
        
        missing_result = response.json()
        assert missing_result["missing_number"] == chosen_number
        assert missing_result["calculation_method"] == "mathematical_sum"
        
        # Step 5: User tries to extract the same number again (should fail)
        response = client.post(f"/extract/{chosen_number}")
        assert response.status_code == 409
        
        # Step 6: User resets to start over
        response = client.post("/reset")
        assert response.status_code == 200
        
        # Step 7: User verifies reset worked
        response = client.get("/status")
        assert response.status_code == 200
        final_status = response.json()
        assert final_status["extracted_count"] == 0
        assert len(final_status["extracted_numbers"]) == 0
        
        # Step 8: User can now extract the same number again
        response = client.post(f"/extract/{chosen_number}")
        assert response.status_code == 200


class TestNumberSetIntegration:
    """Integration tests for NumberSet class functionality."""
    
    def test_number_set_mathematical_correctness(self):
        """Test mathematical correctness of NumberSet operations."""
        number_set = NumberSet(100)
        
        # Test sum formula correctness
        expected_sum = sum(range(1, 101))  # 1 + 2 + ... + 100 = 5050
        # Calculate expected sum using the formula: n(n+1)/2
        calculated_expected_sum = 100 * (100 + 1) // 2
        assert calculated_expected_sum == expected_sum
        
        # Test missing number calculation for various extractions
        test_cases = [1, 50, 100, 25, 75]
        
        for number in test_cases:
            number_set.reset()
            number_set.extract(number)
            
            missing = number_set.find_missing_number()
            assert missing == number
            
            # Verify the math: expected_sum - current_sum = missing_number
            current_sum = sum(number_set.get_current_set())
            assert expected_sum - current_sum == missing
    
    def test_number_set_edge_cases(self):
        """Test NumberSet edge cases and boundary conditions."""
        # Test with different max numbers
        for max_num in [10, 50, 100, 1000]:
            number_set = NumberSet(max_num)
            
            # Extract first number
            number_set.extract(1)
            assert number_set.find_missing_number() == 1
            
            # Reset and extract last number
            number_set.reset()
            number_set.extract(max_num)
            assert number_set.find_missing_number() == max_num
            
            # Reset and extract middle number
            number_set.reset()
            middle = max_num // 2
            number_set.extract(middle)
            assert number_set.find_missing_number() == middle
    
    def test_number_set_state_consistency(self):
        """Test NumberSet state consistency across operations."""
        number_set = NumberSet(100)
        
        # Track state changes
        initial_count = number_set.count_remaining()
        assert initial_count == 100
        assert number_set.count_extracted() == 0
        
        # Extract numbers and verify state
        numbers_to_extract = [10, 20, 30, 40, 50]
        
        for i, number in enumerate(numbers_to_extract):
            number_set.extract(number)
            
            # Verify counts
            assert number_set.count_remaining() == 100 - (i + 1)
            assert number_set.count_extracted() == i + 1
            
            # Verify extracted numbers list
            extracted = number_set.get_extracted_numbers()
            assert len(extracted) == i + 1
            assert number in extracted
        
        # Verify final state
        assert number_set.count_remaining() == 95
        assert number_set.count_extracted() == 5
        assert set(number_set.get_extracted_numbers()) == set(numbers_to_extract)
        
        # Reset and verify
        number_set.reset()
        assert number_set.count_remaining() == 100
        assert number_set.count_extracted() == 0
        assert len(number_set.get_extracted_numbers()) == 0
    
    def test_number_set_performance_characteristics(self):
        """Test NumberSet performance characteristics."""
        import time
        
        # Test with large number set
        large_number_set = NumberSet(10000)
        
        # Test extraction performance
        start_time = time.time()
        
        for i in range(1, 101):  # Extract 100 numbers
            large_number_set.extract(i)
        
        extraction_time = time.time() - start_time
        assert extraction_time < 1.0  # Should be very fast
        
        # Test missing number calculation performance
        large_number_set.reset()
        large_number_set.extract(5000)  # Extract middle number
        
        start_time = time.time()
        missing = large_number_set.find_missing_number()
        calculation_time = time.time() - start_time
        
        assert missing == 5000
        assert calculation_time < 0.1  # Should be nearly instantaneous
        
        # Test state query performance
        start_time = time.time()
        
        for _ in range(1000):  # Query state 1000 times
            count = large_number_set.count_remaining()
            assert count == 9999
        
        query_time = time.time() - start_time
        assert query_time < 1.0  # Should be very fast
    
    def test_number_set_memory_efficiency(self):
        """Test NumberSet memory efficiency."""
        import sys
        
        # Test memory usage with different sizes
        small_set = NumberSet(100)
        small_size = sys.getsizeof(small_set)
        
        large_set = NumberSet(10000)
        large_size = sys.getsizeof(large_set)
        
        # Memory usage should scale reasonably
        size_ratio = large_size / small_size
        number_ratio = 10000 / 100
        
        # Memory usage should not scale linearly with number count
        # (due to efficient set-based implementation)
        assert size_ratio < number_ratio * 0.5
        
        # Test memory usage after extractions
        initial_size = sys.getsizeof(large_set)
        
        # Extract many numbers
        for i in range(1, 1001):
            large_set.extract(i)
        
        after_extraction_size = sys.getsizeof(large_set)
        
        # Memory usage should not increase dramatically
        size_increase_ratio = after_extraction_size / initial_size
        assert size_increase_ratio < 2.0  # Should not double in size


class TestAPIIntegrationWithRealScenarios:
    """Integration tests simulating real-world API usage scenarios."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        with TestClient(app) as client:
            client.post("/reset")
            yield client
    
    def test_demo_scenario_workflow(self, client):
        """Test the demo scenario workflow as described in requirements."""
        # This simulates the exact workflow described in the technical test
        
        # Step 1: Initialize (implicit - API starts with full set)
        response = client.get("/status")
        assert response.status_code == 200
        status = response.json()
        assert status["remaining_count"] == 100
        
        # Step 2: User provides a number to extract
        demo_number = 42  # Classic choice for demos
        
        response = client.post(f"/extract/{demo_number}")
        assert response.status_code == 200
        
        extract_data = response.json()
        assert extract_data["success"] is True
        assert extract_data["extracted_number"] == demo_number
        
        # Step 3: System calculates and returns the missing number
        response = client.get("/missing")
        assert response.status_code == 200
        
        missing_data = response.json()
        assert missing_data["missing_number"] == demo_number
        assert "execution_time_ms" in missing_data
        
        # Step 4: Demonstrate that the system correctly identified the extracted number
        # This is proven by the fact that missing_number == extracted_number
        assert missing_data["missing_number"] == extract_data["extracted_number"]
        
        print(f"Demo completed successfully:")
        print(f"  Extracted number: {extract_data['extracted_number']}")
        print(f"  Missing number found: {missing_data['missing_number']}")
        print(f"  Calculation time: {missing_data['execution_time_ms']} ms")
        print(f"  Method: {missing_data['calculation_method']}")
    
    def test_multiple_demo_runs(self, client):
        """Test multiple demo runs with different numbers."""
        demo_numbers = [7, 23, 56, 89, 91]
        
        for demo_number in demo_numbers:
            # Reset for each demo
            client.post("/reset")
            
            # Extract number
            response = client.post(f"/extract/{demo_number}")
            assert response.status_code == 200
            
            # Find missing number
            response = client.get("/missing")
            assert response.status_code == 200
            
            missing_data = response.json()
            assert missing_data["missing_number"] == demo_number
            
            print(f"Demo {demo_number}: Successfully found missing number {missing_data['missing_number']}")
    
    def test_error_handling_in_demo_scenario(self, client):
        """Test error handling during demo scenarios."""
        # Test invalid input handling
        invalid_numbers = [0, 101, -5, 150]
        
        for invalid_number in invalid_numbers:
            response = client.post(f"/extract/{invalid_number}")
            assert response.status_code == 400
            
            error_data = response.json()
            assert error_data["error"] == "NUMBER_OUT_OF_RANGE"
            assert "outside valid range" in error_data["message"]
        
        # Test duplicate extraction
        client.post("/reset")
        client.post("/extract/25")
        
        response = client.post("/extract/25")
        assert response.status_code == 409
        
        error_data = response.json()
        assert error_data["error"] == "NUMBER_ALREADY_EXTRACTED"
        
        # Test missing number without extraction
        client.post("/reset")
        
        response = client.get("/missing")
        assert response.status_code == 422
        
        error_data = response.json()
        assert error_data["error"] == "NO_NUMBERS_EXTRACTED"
    
    def test_api_robustness_under_stress(self, client):
        """Test API robustness under stress conditions."""
        # Rapid sequential requests
        start_time = time.time()
        
        for i in range(1, 51):  # Extract 50 numbers rapidly
            response = client.post(f"/extract/{i}")
            assert response.status_code == 200
        
        rapid_extraction_time = time.time() - start_time
        assert rapid_extraction_time < 10.0  # Should handle rapid requests
        
        # Verify final state is correct
        response = client.get("/status")
        assert response.status_code == 200
        
        status = response.json()
        assert status["extracted_count"] == 50
        assert status["remaining_count"] == 50
        
        # Test rapid status queries
        start_time = time.time()
        
        for _ in range(100):  # 100 rapid status queries
            response = client.get("/status")
            assert response.status_code == 200
        
        rapid_query_time = time.time() - start_time
        assert rapid_query_time < 5.0  # Should handle rapid queries
        
        print(f"Stress test results:")
        print(f"  50 extractions time: {rapid_extraction_time:.2f} seconds")
        print(f"  100 status queries time: {rapid_query_time:.2f} seconds")