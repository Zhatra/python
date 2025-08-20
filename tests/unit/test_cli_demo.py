"""
Unit tests for the CLI demo script.

This module tests the command-line interface functionality for the missing number
algorithm demonstration.
"""

import unittest
import sys
import os
import io
from unittest.mock import patch, MagicMock
import subprocess
import tempfile

# Add project root to Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, project_root)

# Import the CLI module
cli_module_path = os.path.join(project_root, 'scripts', 'cli_demo.py')


class TestCLIDemo(unittest.TestCase):
    """Test cases for CLI demo functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cli_script = os.path.join(project_root, 'scripts', 'cli_demo.py')
    
    def test_cli_help_output(self):
        """Test that CLI help output is displayed correctly."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--help'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Demonstrate the Missing Number algorithm', result.stdout)
        self.assertIn('--extract', result.stdout)
        self.assertIn('--interactive', result.stdout)
        self.assertIn('--demo', result.stdout)
        self.assertIn('--benchmark', result.stdout)
    
    def test_extract_single_number(self):
        """Test extracting a single number via CLI."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--extract', '42', '--quiet'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('42', result.stdout.strip())
    
    def test_extract_multiple_numbers_error(self):
        """Test that extracting multiple numbers shows appropriate error."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--extract', '25', '--extract', '75'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Multiple numbers extracted', result.stdout)
    
    def test_extract_invalid_number(self):
        """Test extracting an invalid number (out of range)."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--extract', '150'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Error extracting 150', result.stdout)
    
    def test_extract_with_verbose_flag(self):
        """Test extraction with verbose output."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--extract', '42', '--verbose'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Initial set size', result.stdout)
        self.assertIn('Calculation time', result.stdout)
    
    def test_demo_mode(self):
        """Test automated demo mode."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--demo'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Automated Missing Number Algorithm Demonstration', result.stdout)
        self.assertIn('Test Case 1', result.stdout)
        self.assertIn('CORRECT!', result.stdout)
    
    def test_demo_mode_quiet(self):
        """Test automated demo mode with quiet output."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--demo', '--quiet'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        # Should have minimal output in quiet mode
        lines = result.stdout.strip().split('\n')
        self.assertGreater(len(lines), 0)
        # Each line should be a test result
        for line in lines:
            if line.strip():
                self.assertIn('Test', line)
    
    def test_benchmark_mode(self):
        """Test benchmark mode."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--benchmark', '--max-number', '50'],
            capture_output=True,
            text=True,
            timeout=30  # Benchmark might take some time
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Performance Benchmark', result.stdout)
        self.assertIn('Average extraction time', result.stdout)
        self.assertIn('Average calculation time', result.stdout)
    
    def test_custom_max_number(self):
        """Test using custom maximum number."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--extract', '25', '--max-number', '50', '--quiet'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('25', result.stdout.strip())
    
    def test_invalid_max_number_with_extract(self):
        """Test extracting number larger than custom max number."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--extract', '75', '--max-number', '50'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Error extracting 75', result.stdout)
    
    def test_conflicting_verbose_quiet_flags(self):
        """Test that conflicting verbose and quiet flags are handled."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--verbose', '--quiet', '--demo'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 1)
        self.assertIn('--verbose and --quiet cannot be used together', result.stdout)
    
    def test_no_arguments_shows_help(self):
        """Test that running without arguments shows help message."""
        result = subprocess.run(
            [sys.executable, self.cli_script],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 1)
        self.assertIn('Please specify a mode', result.stdout)
    
    def test_edge_case_extract_number_1(self):
        """Test extracting number 1 (minimum edge case)."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--extract', '1', '--quiet'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertEqual('1', result.stdout.strip())
    
    def test_edge_case_extract_number_100(self):
        """Test extracting number 100 (maximum edge case)."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--extract', '100', '--quiet'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertEqual('100', result.stdout.strip())
    
    def test_extract_zero_invalid(self):
        """Test that extracting 0 is invalid."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--extract', '0'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Error extracting 0', result.stdout)
    
    def test_extract_negative_number_invalid(self):
        """Test that extracting negative numbers is invalid."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--extract', '-5'],
            capture_output=True,
            text=True
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertIn('Error extracting -5', result.stdout)


class TestCLIInteractiveMode(unittest.TestCase):
    """Test cases for interactive mode functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cli_script = os.path.join(project_root, 'scripts', 'cli_demo.py')
    
    @patch('builtins.input')
    def test_interactive_mode_basic_flow(self, mock_input):
        """Test basic interactive mode flow."""
        # Simulate user input: extract 42, find missing, exit
        mock_input.side_effect = ['1', '42', '2', '6']
        
        result = subprocess.run(
            [sys.executable, self.cli_script, '--interactive'],
            input='1\n42\n2\n6\n',
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Should exit cleanly
        self.assertEqual(result.returncode, 0)
        self.assertIn('Interactive Missing Number Demo', result.stdout)
    
    def test_interactive_mode_keyboard_interrupt(self):
        """Test that interactive mode handles keyboard interrupt gracefully."""
        # This test is complex to implement reliably across different systems
        # Instead, we'll test that the interactive mode starts correctly
        process = subprocess.Popen(
            [sys.executable, self.cli_script, '--interactive'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            # Send exit command instead of interrupt
            stdout, stderr = process.communicate(input='6\n', timeout=5)
            
            # Should exit cleanly with goodbye message
            self.assertIn('Interactive Missing Number Demo', stdout)
            self.assertIn('Goodbye', stdout)
        except subprocess.TimeoutExpired:
            process.kill()
            self.fail("Interactive mode did not respond to exit command properly")


class TestCLIPerformance(unittest.TestCase):
    """Test cases for CLI performance characteristics."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.cli_script = os.path.join(project_root, 'scripts', 'cli_demo.py')
    
    def test_large_number_set_performance(self):
        """Test performance with larger number sets."""
        result = subprocess.run(
            [sys.executable, self.cli_script, '--extract', '500', '--max-number', '1000', '--quiet'],
            capture_output=True,
            text=True,
            timeout=10  # Should complete quickly
        )
        
        self.assertEqual(result.returncode, 0)
        self.assertEqual('500', result.stdout.strip())
    
    def test_benchmark_completes_quickly(self):
        """Test that benchmark mode completes in reasonable time."""
        import time
        start_time = time.time()
        
        result = subprocess.run(
            [sys.executable, self.cli_script, '--benchmark', '--max-number', '100'],
            capture_output=True,
            text=True,
            timeout=60  # Should complete within 60 seconds
        )
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        self.assertEqual(result.returncode, 0)
        self.assertLess(execution_time, 30)  # Should complete in under 30 seconds
        self.assertIn('Performance Benchmark', result.stdout)


if __name__ == '__main__':
    unittest.main()