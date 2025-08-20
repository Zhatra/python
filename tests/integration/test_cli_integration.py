"""
Integration tests for CLI demo functionality.

This module tests the integration between the CLI interface and the core
NumberSet functionality to ensure end-to-end functionality works correctly.
"""

import unittest
import subprocess
import sys
import os
import tempfile
import json

# Add project root to Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)


class TestCLIIntegration(unittest.TestCase):
    """Integration tests for CLI demo with core functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cli_script = os.path.join(project_root, 'scripts', 'cli_demo.py')
    
    def test_cli_with_api_number_set_integration(self):
        """Test that CLI uses the same NumberSet class as the API."""
        # Test that the CLI produces the same results as direct NumberSet usage
        from src.api.number_set import NumberSet
        
        # Direct NumberSet usage
        number_set = NumberSet(100)
        number_set.extract(42)
        expected_missing = number_set.find_missing_number()
        
        # CLI usage
        result = subprocess.run(
            [sys.executable, self.cli_script, '--extract', '42', '--quiet'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        cli_missing = int(result.stdout.strip())
        
        # Should produce the same result
        self.assertEqual(expected_missing, cli_missing)
    
    def test_cli_error_handling_matches_api(self):
        """Test that CLI error handling matches API error handling."""
        # Test invalid number extraction
        result = subprocess.run(
            [sys.executable, self.cli_script, '--extract', '150'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Error extracting 150', result.stdout)
        self.assertIn('outside valid range', result.stdout)
    
    def test_cli_performance_consistency(self):
        """Test that CLI performance is consistent with direct API usage."""
        import time
        from src.api.number_set import NumberSet
        
        # Measure direct API performance
        start_time = time.time()
        number_set = NumberSet(1000)
        number_set.extract(500)
        missing = number_set.find_missing_number()
        api_time = time.time() - start_time
        
        # Measure CLI performance
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, self.cli_script, '--extract', '500', '--max-number', '1000', '--quiet'],
            capture_output=True,
            text=True
        )
        cli_time = time.time() - start_time
        
        self.assertEqual(result.returncode, 0)
        cli_missing = int(result.stdout.strip())
        
        # Results should match
        self.assertEqual(missing, cli_missing)
        
        # CLI should not be significantly slower (allowing for subprocess overhead)
        self.assertLess(cli_time, api_time * 10)  # Allow 10x overhead for subprocess
    
    def test_cli_with_different_number_ranges(self):
        """Test CLI functionality with different number ranges."""
        test_cases = [
            {'max_number': 10, 'extract': 5},
            {'max_number': 50, 'extract': 25},
            {'max_number': 200, 'extract': 150},
            {'max_number': 1000, 'extract': 777},
        ]
        
        for case in test_cases:
            with self.subTest(case=case):
                result = subprocess.run(
                    [sys.executable, self.cli_script, 
                     '--extract', str(case['extract']), 
                     '--max-number', str(case['max_number']), 
                     '--quiet'],
                    capture_output=True,
                    text=True
                )
                
                self.assertEqual(result.returncode, 0)
                missing = int(result.stdout.strip())
                self.assertEqual(missing, case['extract'])
    
    def test_cli_demo_mode_comprehensive(self):
        """Test that demo mode exercises all core functionality."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--demo', '--verbose'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        
        # Should test edge cases
        self.assertIn('Edge case: minimum number', result.stdout)
        self.assertIn('Edge case: maximum number', result.stdout)
        self.assertIn('Middle number', result.stdout)
        
        # Should show timing information
        self.assertIn('Extraction time', result.stdout)
        self.assertIn('Calculation time', result.stdout)
        
        # Should show all tests passed
        self.assertIn('CORRECT!', result.stdout)
        self.assertNotIn('INCORRECT!', result.stdout)
    
    def test_cli_benchmark_accuracy(self):
        """Test that benchmark mode produces accurate performance metrics."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--benchmark', '--max-number', '100'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        self.assertEqual(result.returncode, 0)
        
        # Should contain performance metrics
        self.assertIn('Performance Benchmark', result.stdout)
        self.assertIn('Average extraction time', result.stdout)
        self.assertIn('Average calculation time', result.stdout)
        self.assertIn('Algorithm complexity: O(1)', result.stdout)
        
        # Should test multiple numbers
        self.assertIn('Testing extraction of number: 1', result.stdout)
        self.assertIn('Testing extraction of number: 100', result.stdout)
    
    def test_cli_multiple_extractions_handling(self):
        """Test CLI handling of multiple number extractions."""
        result = subprocess.run(
            [sys.executable, self.cli_script, 
             '--extract', '10', '--extract', '20', '--extract', '30'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Multiple numbers extracted', result.stdout)
        self.assertIn('algorithm works only when exactly one number is missing', result.stdout)
    
    def test_cli_validation_integration(self):
        """Test that CLI validation integrates properly with core validation."""
        # Test various invalid inputs
        invalid_cases = [
            {'args': ['--extract', '0'], 'expected': 'Error extracting 0'},
            {'args': ['--extract', '-5'], 'expected': 'Error extracting -5'},
            {'args': ['--extract', '101'], 'expected': 'Error extracting 101'},
        ]
        
        for case in invalid_cases:
            with self.subTest(case=case):
                result = subprocess.run(
                    [sys.executable, self.cli_script] + case['args'],
                    capture_output=True,
                    text=True
                )
                
                self.assertEqual(result.returncode, 0)
                self.assertIn(case['expected'], result.stdout)


class TestCLIWorkflow(unittest.TestCase):
    """Test complete CLI workflows."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cli_script = os.path.join(project_root, 'scripts', 'cli_demo.py')
    
    def test_complete_demonstration_workflow(self):
        """Test a complete demonstration workflow."""
        # Run demo mode to show all functionality
        result = subprocess.run(
            [sys.executable, self.cli_script, '--demo'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        
        # Verify all test cases ran successfully
        test_case_count = result.stdout.count('Test Case')
        self.assertGreaterEqual(test_case_count, 5)
        
        # Verify all were correct
        correct_count = result.stdout.count('CORRECT!')
        self.assertEqual(correct_count, test_case_count)
    
    def test_user_argument_acceptance_workflow(self):
        """Test that CLI accepts user arguments as per requirement 6.6."""
        # Test various user argument combinations
        test_cases = [
            ['--extract', '42'],
            ['--extract', '1', '--verbose'],
            ['--extract', '100', '--max-number', '100'],
            ['--demo', '--quiet'],
            ['--benchmark', '--max-number', '50'],
        ]
        
        for args in test_cases:
            with self.subTest(args=args):
                result = subprocess.run(
                    [sys.executable, self.cli_script] + args,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                self.assertEqual(result.returncode, 0)
                # Should not contain error messages
                self.assertNotIn('Error:', result.stdout)
    
    def test_extracted_number_identification_workflow(self):
        """Test that CLI correctly identifies extracted numbers as per requirement 6.7."""
        # Test with various numbers to ensure correct identification
        test_numbers = [1, 7, 42, 50, 99, 100]
        
        for number in test_numbers:
            with self.subTest(number=number):
                result = subprocess.run(
                    [sys.executable, self.cli_script, '--extract', str(number), '--quiet'],
                    capture_output=True,
                    text=True
                )
                
                self.assertEqual(result.returncode, 0)
                identified_number = int(result.stdout.strip())
                
                # Should correctly identify the extracted number
                self.assertEqual(identified_number, number)
    
    def test_demonstration_shows_correctness(self):
        """Test that demonstration clearly shows algorithm correctness."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--demo'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        
        # Should explicitly show that algorithm correctly identified numbers
        self.assertIn('correctly identifies extracted numbers', result.stdout)
        
        # Should show successful completion
        self.assertIn('demonstration complete', result.stdout)
        
        # Should show all tests were correct
        self.assertIn('CORRECT!', result.stdout)


if __name__ == '__main__':
    unittest.main()