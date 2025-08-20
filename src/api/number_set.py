"""
NumberSet class for missing number algorithm implementation.

This module provides the NumberSet class that manages a set of natural numbers
from 1 to 100 and can find missing numbers using mathematical approach.
"""

import logging
from typing import List, Set

from src.exceptions import (
    NumberOutOfRangeError, NumberAlreadyExtractedError, 
    NoNumbersExtractedError, MultipleNumbersExtractedError
)
from src.validation import InputValidator

logger = logging.getLogger(__name__)


class NumberSet:
    """
    A class representing a set of the first 100 natural numbers with extraction capabilities.
    
    This class maintains a set of numbers from 1 to 100 and provides methods to:
    - Extract (remove) specific numbers from the set
    - Find missing numbers using mathematical sum approach
    - Validate input parameters
    """
    
    def __init__(self, max_number: int = 100):
        """
        Initialize the NumberSet with natural numbers from 1 to max_number.
        
        Args:
            max_number (int): Maximum number in the set (default: 100)
            
        Raises:
            ValueError: If max_number is not a positive integer
        """
        if not isinstance(max_number, int) or max_number <= 0:
            logger.error(f"Invalid max_number: {max_number}")
            raise ValueError("max_number must be a positive integer")
            
        self.max_number = max_number
        self.numbers: Set[int] = set(range(1, max_number + 1))
        self.extracted_numbers: Set[int] = set()
        
        logger.info(f"NumberSet initialized with max_number={max_number}")
    
    def extract(self, number: int) -> bool:
        """
        Extract (remove) a specific number from the set.
        
        Args:
            number (int): The number to extract from the set
            
        Returns:
            bool: True if the number was successfully extracted
            
        Raises:
            NumberOutOfRangeError: If number is not within valid range (1 to max_number)
            NumberAlreadyExtractedError: If number has already been extracted
            TypeError: If number is not an integer
        """
        if not isinstance(number, int):
            logger.error(f"Invalid number type: {type(number)}")
            raise TypeError("Number must be an integer")
        
        # Validate number range
        try:
            InputValidator.validate_number_range(number, 1, self.max_number)
        except NumberOutOfRangeError:
            logger.error(f"Number {number} is out of range (1-{self.max_number})")
            raise
        
        # Check if number is already extracted
        if number not in self.numbers:
            logger.warning(f"Attempted to extract already extracted number: {number}")
            raise NumberAlreadyExtractedError(number)
        
        # Extract the number
        self.numbers.remove(number)
        self.extracted_numbers.add(number)
        logger.info(f"Successfully extracted number: {number}")
        return True
    
    def find_missing_number(self) -> int:
        """
        Find the missing number using mathematical sum approach.
        
        Uses the formula: sum of 1 to n = n(n+1)/2
        Missing number = expected_sum - actual_sum
        
        Returns:
            int: The missing number
            
        Raises:
            NoNumbersExtractedError: If no numbers have been extracted
            MultipleNumbersExtractedError: If more than one number is missing
        """
        if len(self.extracted_numbers) == 0:
            logger.warning("Attempted to find missing number but no numbers extracted")
            raise NoNumbersExtractedError()
        
        if len(self.extracted_numbers) > 1:
            logger.error(f"Cannot find single missing number when {len(self.extracted_numbers)} numbers are extracted")
            raise MultipleNumbersExtractedError(len(self.extracted_numbers))
        
        # Calculate expected sum using mathematical formula
        expected_sum = self.max_number * (self.max_number + 1) // 2
        
        # Calculate actual sum of remaining numbers
        actual_sum = sum(self.numbers)
        
        # Missing number is the difference
        missing_number = expected_sum - actual_sum
        
        logger.info(f"Calculated missing number: {missing_number}")
        return missing_number
    
    def get_current_set(self) -> List[int]:
        """
        Get the current set of numbers as a sorted list.
        
        Returns:
            List[int]: Sorted list of remaining numbers in the set
        """
        return sorted(list(self.numbers))
    
    def get_extracted_numbers(self) -> List[int]:
        """
        Get the list of extracted numbers.
        
        Returns:
            List[int]: Sorted list of extracted numbers
        """
        return sorted(list(self.extracted_numbers))
    
    def reset(self) -> None:
        """
        Reset the set to contain all numbers from 1 to max_number.
        """
        self.numbers = set(range(1, self.max_number + 1))
        self.extracted_numbers = set()
        logger.info("NumberSet has been reset")
    
    def is_complete(self) -> bool:
        """
        Check if the set contains all numbers (no extractions made).
        
        Returns:
            bool: True if no numbers have been extracted, False otherwise
        """
        return len(self.extracted_numbers) == 0
    
    def count_remaining(self) -> int:
        """
        Get the count of remaining numbers in the set.
        
        Returns:
            int: Number of remaining numbers in the set
        """
        return len(self.numbers)
    
    def count_extracted(self) -> int:
        """
        Get the count of extracted numbers.
        
        Returns:
            int: Number of extracted numbers
        """
        return len(self.extracted_numbers)