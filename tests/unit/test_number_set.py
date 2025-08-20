"""
Unit tests for NumberSet class.

This module contains comprehensive tests for the NumberSet class functionality
including initialization, extraction, missing number calculation, and validation.
"""

import pytest
from src.api.number_set import NumberSet


class TestNumberSetInitialization:
    """Test NumberSet initialization and basic properties."""
    
    def test_default_initialization(self):
        """Test NumberSet initialization with default parameters."""
        number_set = NumberSet()
        
        assert number_set.max_number == 100
        assert len(number_set.get_current_set()) == 100
        assert number_set.get_current_set() == list(range(1, 101))
        assert number_set.count_remaining() == 100
        assert number_set.count_extracted() == 0
        assert number_set.is_complete() is True
    
    def test_custom_max_number_initialization(self):
        """Test NumberSet initialization with custom max_number."""
        number_set = NumberSet(50)
        
        assert number_set.max_number == 50
        assert len(number_set.get_current_set()) == 50
        assert number_set.get_current_set() == list(range(1, 51))
        assert number_set.count_remaining() == 50
    
    def test_invalid_max_number_initialization(self):
        """Test NumberSet initialization with invalid max_number values."""
        with pytest.raises(ValueError, match="max_number must be a positive integer"):
            NumberSet(0)
        
        with pytest.raises(ValueError, match="max_number must be a positive integer"):
            NumberSet(-1)
        
        with pytest.raises(ValueError, match="max_number must be a positive integer"):
            NumberSet(-100)


class TestNumberSetExtraction:
    """Test NumberSet extraction functionality."""
    
    def test_successful_extraction(self):
        """Test successful extraction of a valid number."""
        number_set = NumberSet()
        
        result = number_set.extract(50)
        
        assert result is True
        assert 50 not in number_set.get_current_set()
        assert 50 in number_set.get_extracted_numbers()
        assert number_set.count_remaining() == 99
        assert number_set.count_extracted() == 1
        assert number_set.is_complete() is False
    
    def test_extraction_of_already_extracted_number(self):
        """Test extraction of a number that was already extracted."""
        number_set = NumberSet()
        
        # Extract number first time
        result1 = number_set.extract(25)
        assert result1 is True
        
        # Try to extract same number again
        result2 = number_set.extract(25)
        assert result2 is False
        assert number_set.count_extracted() == 1
        assert 25 in number_set.get_extracted_numbers()
    
    def test_extraction_boundary_values(self):
        """Test extraction of boundary values (1 and max_number)."""
        number_set = NumberSet()
        
        # Extract minimum value
        result1 = number_set.extract(1)
        assert result1 is True
        assert 1 not in number_set.get_current_set()
        
        # Extract maximum value
        result2 = number_set.extract(100)
        assert result2 is True
        assert 100 not in number_set.get_current_set()
        
        assert number_set.count_extracted() == 2
    
    def test_extraction_invalid_range(self):
        """Test extraction with numbers outside valid range."""
        number_set = NumberSet()
        
        with pytest.raises(ValueError, match="Number must be between 1 and 100"):
            number_set.extract(0)
        
        with pytest.raises(ValueError, match="Number must be between 1 and 100"):
            number_set.extract(101)
        
        with pytest.raises(ValueError, match="Number must be between 1 and 100"):
            number_set.extract(-5)
    
    def test_extraction_invalid_type(self):
        """Test extraction with invalid data types."""
        number_set = NumberSet()
        
        with pytest.raises(TypeError, match="Number must be an integer"):
            number_set.extract("50")
        
        with pytest.raises(TypeError, match="Number must be an integer"):
            number_set.extract(50.5)
        
        with pytest.raises(TypeError, match="Number must be an integer"):
            number_set.extract(None)


class TestNumberSetMissingNumberCalculation:
    """Test NumberSet missing number calculation functionality."""
    
    def test_find_missing_number_single_extraction(self):
        """Test finding missing number with single extraction."""
        number_set = NumberSet()
        
        # Extract a number
        number_set.extract(42)
        
        # Find missing number
        missing = number_set.find_missing_number()
        
        assert missing == 42
    
    def test_find_missing_number_different_values(self):
        """Test finding missing number with different extracted values."""
        test_cases = [1, 25, 50, 75, 100]
        
        for test_number in test_cases:
            number_set = NumberSet()
            number_set.extract(test_number)
            missing = number_set.find_missing_number()
            assert missing == test_number
    
    def test_find_missing_number_no_extraction(self):
        """Test finding missing number when no numbers are extracted."""
        number_set = NumberSet()
        
        missing = number_set.find_missing_number()
        
        assert missing == 0
    
    def test_find_missing_number_multiple_extractions(self):
        """Test finding missing number with multiple extractions (should raise error)."""
        number_set = NumberSet()
        
        # Extract multiple numbers
        number_set.extract(10)
        number_set.extract(20)
        
        with pytest.raises(ValueError, match="Cannot find single missing number when multiple numbers are extracted"):
            number_set.find_missing_number()
    
    def test_mathematical_sum_approach(self):
        """Test that the mathematical sum approach is working correctly."""
        number_set = NumberSet(10)  # Smaller set for easier verification
        
        # Expected sum for 1-10: 10 * 11 / 2 = 55
        # Extract 7, remaining sum should be 55 - 7 = 48
        number_set.extract(7)
        
        # Verify the calculation manually
        expected_sum = 10 * 11 // 2  # 55
        actual_sum = sum(number_set.get_current_set())  # Should be 48
        missing = expected_sum - actual_sum  # Should be 7
        
        assert number_set.find_missing_number() == missing
        assert missing == 7


class TestNumberSetUtilityMethods:
    """Test NumberSet utility methods."""
    
    def test_get_current_set(self):
        """Test getting current set of numbers."""
        number_set = NumberSet(5)
        
        current_set = number_set.get_current_set()
        
        assert current_set == [1, 2, 3, 4, 5]
        assert isinstance(current_set, list)
        
        # Extract a number and verify
        number_set.extract(3)
        current_set = number_set.get_current_set()
        assert current_set == [1, 2, 4, 5]
    
    def test_get_extracted_numbers(self):
        """Test getting extracted numbers."""
        number_set = NumberSet()
        
        # Initially empty
        extracted = number_set.get_extracted_numbers()
        assert extracted == []
        
        # Extract some numbers
        number_set.extract(10)
        number_set.extract(5)
        number_set.extract(15)
        
        extracted = number_set.get_extracted_numbers()
        assert extracted == [5, 10, 15]  # Should be sorted
        assert isinstance(extracted, list)
    
    def test_reset_functionality(self):
        """Test reset functionality."""
        number_set = NumberSet()
        
        # Extract some numbers
        number_set.extract(10)
        number_set.extract(20)
        number_set.extract(30)
        
        assert number_set.count_extracted() == 3
        assert number_set.count_remaining() == 97
        assert not number_set.is_complete()
        
        # Reset
        number_set.reset()
        
        assert number_set.count_extracted() == 0
        assert number_set.count_remaining() == 100
        assert number_set.is_complete()
        assert number_set.get_current_set() == list(range(1, 101))
        assert number_set.get_extracted_numbers() == []
    
    def test_is_complete(self):
        """Test is_complete method."""
        number_set = NumberSet()
        
        # Initially complete
        assert number_set.is_complete() is True
        
        # After extraction, not complete
        number_set.extract(50)
        assert number_set.is_complete() is False
        
        # After reset, complete again
        number_set.reset()
        assert number_set.is_complete() is True
    
    def test_count_methods(self):
        """Test count_remaining and count_extracted methods."""
        number_set = NumberSet(10)
        
        # Initial state
        assert number_set.count_remaining() == 10
        assert number_set.count_extracted() == 0
        
        # After extractions
        number_set.extract(3)
        number_set.extract(7)
        
        assert number_set.count_remaining() == 8
        assert number_set.count_extracted() == 2
        
        # Verify total is consistent
        assert number_set.count_remaining() + number_set.count_extracted() == 10


class TestNumberSetEdgeCases:
    """Test NumberSet edge cases and error conditions."""
    
    def test_extract_all_numbers(self):
        """Test extracting all numbers from a small set."""
        number_set = NumberSet(3)
        
        # Extract all numbers
        for i in range(1, 4):
            result = number_set.extract(i)
            assert result is True
        
        assert number_set.count_remaining() == 0
        assert number_set.count_extracted() == 3
        assert number_set.get_current_set() == []
        assert number_set.get_extracted_numbers() == [1, 2, 3]
    
    def test_single_number_set(self):
        """Test NumberSet with only one number."""
        number_set = NumberSet(1)
        
        assert number_set.get_current_set() == [1]
        assert number_set.count_remaining() == 1
        
        # Extract the only number
        result = number_set.extract(1)
        assert result is True
        
        assert number_set.get_current_set() == []
        assert number_set.count_remaining() == 0
        assert number_set.find_missing_number() == 1
    
    def test_large_number_set(self):
        """Test NumberSet with large max_number."""
        number_set = NumberSet(1000)
        
        assert number_set.count_remaining() == 1000
        assert number_set.max_number == 1000
        
        # Extract a number and verify calculation still works
        number_set.extract(500)
        assert number_set.find_missing_number() == 500
    
    def test_custom_max_number_validation(self):
        """Test extraction validation with custom max_number."""
        number_set = NumberSet(50)
        
        # Valid extractions
        assert number_set.extract(1) is True
        assert number_set.extract(50) is True
        
        # Invalid extractions
        with pytest.raises(ValueError, match="Number must be between 1 and 50"):
            number_set.extract(51)
        
        with pytest.raises(ValueError, match="Number must be between 1 and 50"):
            number_set.extract(0)


class TestNumberSetIntegration:
    """Integration tests for NumberSet functionality."""
    
    def test_complete_workflow(self):
        """Test complete workflow of NumberSet operations."""
        number_set = NumberSet()
        
        # Initial state verification
        assert number_set.is_complete()
        assert number_set.count_remaining() == 100
        
        # Extract a number
        extracted_number = 73
        result = number_set.extract(extracted_number)
        assert result is True
        
        # Verify state after extraction
        assert not number_set.is_complete()
        assert number_set.count_remaining() == 99
        assert number_set.count_extracted() == 1
        assert extracted_number in number_set.get_extracted_numbers()
        assert extracted_number not in number_set.get_current_set()
        
        # Find missing number
        missing = number_set.find_missing_number()
        assert missing == extracted_number
        
        # Reset and verify
        number_set.reset()
        assert number_set.is_complete()
        assert number_set.count_remaining() == 100
        assert number_set.count_extracted() == 0
        assert number_set.find_missing_number() == 0
    
    def test_multiple_operations_sequence(self):
        """Test sequence of multiple operations."""
        number_set = NumberSet(20)
        
        # Extract several numbers
        numbers_to_extract = [5, 10, 15]
        for num in numbers_to_extract:
            assert number_set.extract(num) is True
        
        # Verify state
        assert number_set.count_extracted() == 3
        assert number_set.count_remaining() == 17
        assert set(number_set.get_extracted_numbers()) == set(numbers_to_extract)
        
        # Try to find missing number (should fail with multiple extractions)
        with pytest.raises(ValueError):
            number_set.find_missing_number()
        
        # Reset and extract single number
        number_set.reset()
        number_set.extract(12)
        
        # Now finding missing number should work
        assert number_set.find_missing_number() == 12