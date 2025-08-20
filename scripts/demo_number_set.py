#!/usr/bin/env python3
"""
Demonstration script for NumberSet class functionality.

This script demonstrates the NumberSet class capabilities including:
- Initialization with natural numbers 1-100
- Extraction of specific numbers
- Finding missing numbers using mathematical approach
- Input validation
"""

import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from api.number_set import NumberSet


def demonstrate_number_set():
    """Demonstrate NumberSet functionality with various scenarios."""
    
    print("=== NumberSet Class Demonstration ===\n")
    
    # Initialize NumberSet
    print("1. Initializing NumberSet with numbers 1-100")
    number_set = NumberSet()
    print(f"   Initial count: {number_set.count_remaining()} numbers")
    print(f"   Is complete: {number_set.is_complete()}")
    print()
    
    # Demonstrate extraction
    print("2. Extracting number 42")
    result = number_set.extract(42)
    print(f"   Extraction successful: {result}")
    print(f"   Remaining count: {number_set.count_remaining()}")
    print(f"   Extracted numbers: {number_set.get_extracted_numbers()}")
    print()
    
    # Demonstrate missing number calculation
    print("3. Finding missing number using mathematical approach")
    missing = number_set.find_missing_number()
    print(f"   Missing number: {missing}")
    print(f"   Verification: The extracted number was 42, and we found {missing}")
    print()
    
    # Demonstrate mathematical calculation manually
    print("4. Manual verification of mathematical approach")
    expected_sum = 100 * 101 // 2  # Sum of 1 to 100
    actual_sum = sum(number_set.get_current_set())
    calculated_missing = expected_sum - actual_sum
    print(f"   Expected sum (1 to 100): {expected_sum}")
    print(f"   Actual sum (remaining numbers): {actual_sum}")
    print(f"   Calculated missing: {calculated_missing}")
    print()
    
    # Demonstrate reset functionality
    print("5. Resetting the number set")
    number_set.reset()
    print(f"   After reset - count: {number_set.count_remaining()}")
    print(f"   Is complete: {number_set.is_complete()}")
    print(f"   Missing number (no extractions): {number_set.find_missing_number()}")
    print()
    
    # Demonstrate edge cases
    print("6. Testing edge cases")
    
    # Extract boundary values
    print("   Extracting boundary values (1 and 100)")
    number_set.extract(1)
    number_set.extract(100)
    print(f"   Extracted numbers: {number_set.get_extracted_numbers()}")
    
    # Try to find missing number with multiple extractions
    print("   Attempting to find missing number with multiple extractions...")
    try:
        missing = number_set.find_missing_number()
        print(f"   Missing number: {missing}")
    except ValueError as e:
        print(f"   Error (expected): {e}")
    print()
    
    # Demonstrate validation
    print("7. Testing input validation")
    number_set.reset()
    
    try:
        number_set.extract(0)
    except ValueError as e:
        print(f"   Validation error for 0: {e}")
    
    try:
        number_set.extract(101)
    except ValueError as e:
        print(f"   Validation error for 101: {e}")
    
    try:
        number_set.extract("50")
    except TypeError as e:
        print(f"   Type error for string: {e}")
    print()
    
    # Final demonstration with user-like scenario
    print("8. Complete workflow demonstration")
    number_set.reset()
    
    test_number = 73
    print(f"   Extracting number {test_number}")
    number_set.extract(test_number)
    
    missing = number_set.find_missing_number()
    print(f"   Found missing number: {missing}")
    print(f"   Success: {missing == test_number}")
    print()
    
    print("=== Demonstration Complete ===")


if __name__ == "__main__":
    demonstrate_number_set()