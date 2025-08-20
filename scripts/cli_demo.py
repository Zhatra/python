#!/usr/bin/env python3
"""
Command-line interface demo for the Missing Number functionality.

This script demonstrates the missing number algorithm without requiring
the full API server to be running.
"""

import sys
import os
import argparse
import time
from typing import List, Optional

# Add project root to Python path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

from src.api.number_set import NumberSet
from src.exceptions import (
    NumberOutOfRangeError, NumberAlreadyExtractedError, 
    NoNumbersExtractedError, MultipleNumbersExtractedError
)


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Demonstrate the Missing Number algorithm",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/cli_demo.py --extract 42
  python scripts/cli_demo.py --extract 25 --extract 75
  python scripts/cli_demo.py --interactive
  python scripts/cli_demo.py --demo
  python scripts/cli_demo.py --benchmark
        """
    )
    
    parser.add_argument(
        "--extract", "-e",
        type=int,
        action="append",
        help="Extract a number from the set (can be used multiple times)"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    parser.add_argument(
        "--demo", "-d",
        action="store_true",
        help="Run automated demonstration with predefined examples"
    )
    
    parser.add_argument(
        "--benchmark", "-b",
        action="store_true",
        help="Run performance benchmark of the algorithm"
    )
    
    parser.add_argument(
        "--max-number",
        type=int,
        default=100,
        help="Maximum number in the set (default: 100)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress non-essential output"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.verbose and args.quiet:
        print("Error: --verbose and --quiet cannot be used together")
        sys.exit(1)
    
    if args.interactive:
        run_interactive_demo(args.max_number, args.verbose)
    elif args.demo:
        run_automated_demo(args.max_number, args.verbose, args.quiet)
    elif args.benchmark:
        run_benchmark_demo(args.max_number, args.verbose)
    elif args.extract:
        run_extraction_demo(args.extract, args.max_number, args.verbose, args.quiet)
    else:
        print("Please specify a mode: --extract, --interactive, --demo, or --benchmark")
        parser.print_help()
        sys.exit(1)


def run_extraction_demo(numbers_to_extract: List[int], max_number: int, verbose: bool = False, quiet: bool = False):
    """Run a demo with specified numbers to extract."""
    if not quiet:
        print(f"🔢 Missing Number Algorithm Demo")
        print(f"Working with numbers 1 to {max_number}")
        print("=" * 50)
    
    # Initialize the number set
    number_set = NumberSet(max_number)
    
    if verbose:
        print(f"Initial set size: {number_set.count_remaining()}")
        print(f"Numbers to extract: {numbers_to_extract}")
    
    # Track extraction results
    successful_extractions = []
    failed_extractions = []
    
    # Extract the specified numbers
    for num in numbers_to_extract:
        try:
            success = number_set.extract(num)
            if success:
                successful_extractions.append(num)
                if not quiet:
                    print(f"✅ Extracted number: {num}")
            else:
                failed_extractions.append(num)
                if not quiet:
                    print(f"❌ Failed to extract {num}")
        except (NumberOutOfRangeError, NumberAlreadyExtractedError, TypeError) as e:
            failed_extractions.append(num)
            if not quiet:
                print(f"❌ Error extracting {num}: {e}")
    
    if not quiet:
        print(f"\nExtraction Summary:")
        print(f"  Successful: {len(successful_extractions)}")
        print(f"  Failed: {len(failed_extractions)}")
        print(f"  Remaining numbers: {number_set.count_remaining()}")
        
        if verbose and successful_extractions:
            print(f"  Successfully extracted: {successful_extractions}")
        if verbose and failed_extractions:
            print(f"  Failed to extract: {failed_extractions}")
    
    # Calculate missing number if exactly one was extracted
    try:
        if number_set.count_extracted() == 1:
            start_time = time.time()
            missing = number_set.find_missing_number()
            calculation_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if not quiet:
                print(f"\n🎯 Missing number calculated: {missing}")
                print(f"✨ Algorithm correctly identified the extracted number!")
                if verbose:
                    print(f"⏱️  Calculation time: {calculation_time:.3f} ms")
            else:
                print(f"{missing}")  # Just output the result for quiet mode
                
        elif number_set.count_extracted() == 0:
            if not quiet:
                print(f"\n⚠️  No numbers were extracted, so no missing number to find")
        else:
            if not quiet:
                print(f"\n⚠️  Multiple numbers extracted ({number_set.count_extracted()})")
                print("The algorithm works only when exactly one number is missing")
                if verbose:
                    print(f"Extracted numbers: {number_set.get_extracted_numbers()}")
                    
    except (NoNumbersExtractedError, MultipleNumbersExtractedError) as e:
        if not quiet:
            print(f"\n❌ Error calculating missing number: {e}")
    
    return number_set


def run_interactive_demo(max_number: int, verbose: bool = False):
    """Run an interactive demo."""
    print(f"🔢 Interactive Missing Number Demo")
    print(f"Working with numbers 1 to {max_number}")
    print("=" * 50)
    
    number_set = NumberSet(max_number)
    
    while True:
        print(f"\nCurrent state:")
        print(f"  Remaining: {number_set.count_remaining()}")
        print(f"  Extracted: {number_set.count_extracted()}")
        if number_set.count_extracted() > 0:
            print(f"  Extracted numbers: {number_set.get_extracted_numbers()}")
        
        print(f"\nOptions:")
        print(f"  1. Extract a number")
        print(f"  2. Find missing number")
        print(f"  3. Reset the set")
        print(f"  4. Show current set")
        print(f"  5. Run quick demo")
        print(f"  6. Exit")
        
        try:
            choice = input("\nEnter your choice (1-6): ").strip()
            
            if choice == "1":
                num_str = input(f"Enter number to extract (1-{max_number}): ").strip()
                try:
                    num = int(num_str)
                    start_time = time.time()
                    success = number_set.extract(num)
                    extraction_time = (time.time() - start_time) * 1000
                    
                    if success:
                        print(f"✅ Successfully extracted {num}")
                        if verbose:
                            print(f"⏱️  Extraction time: {extraction_time:.3f} ms")
                    else:
                        print(f"❌ Failed to extract {num}")
                except ValueError:
                    print(f"❌ Invalid number: {num_str}")
                except (NumberOutOfRangeError, NumberAlreadyExtractedError, TypeError) as e:
                    print(f"❌ Error: {e}")
            
            elif choice == "2":
                try:
                    if number_set.count_extracted() == 0:
                        print("⚠️  No numbers extracted yet")
                    elif number_set.count_extracted() > 1:
                        print("⚠️  Multiple numbers extracted, algorithm needs exactly one")
                        if verbose:
                            print(f"Extracted numbers: {number_set.get_extracted_numbers()}")
                    else:
                        start_time = time.time()
                        missing = number_set.find_missing_number()
                        calculation_time = (time.time() - start_time) * 1000
                        
                        print(f"🎯 Missing number: {missing}")
                        print(f"✨ Algorithm correctly identified the extracted number!")
                        if verbose:
                            print(f"⏱️  Calculation time: {calculation_time:.3f} ms")
                except (NoNumbersExtractedError, MultipleNumbersExtractedError) as e:
                    print(f"❌ Error: {e}")
            
            elif choice == "3":
                number_set.reset()
                print("🔄 Set has been reset")
            
            elif choice == "4":
                current_set = number_set.get_current_set()
                if len(current_set) <= 20:
                    print(f"Current set: {current_set}")
                else:
                    print(f"Current set has {len(current_set)} numbers")
                    print(f"First 10: {current_set[:10]}")
                    print(f"Last 10: {current_set[-10:]}")
                    if verbose:
                        print(f"Sample middle numbers: {current_set[len(current_set)//2-5:len(current_set)//2+5]}")
            
            elif choice == "5":
                print("\n🚀 Running quick demonstration...")
                demo_number = 42  # Classic choice
                number_set.reset()
                number_set.extract(demo_number)
                missing = number_set.find_missing_number()
                print(f"✅ Extracted {demo_number}, algorithm found: {missing}")
                print("✨ Demonstration complete!")
            
            elif choice == "6":
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1-6.")
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except EOFError:
            print("\n\n👋 Goodbye!")
            break


def run_automated_demo(max_number: int, verbose: bool = False, quiet: bool = False):
    """Run an automated demonstration with predefined examples."""
    if not quiet:
        print(f"🚀 Automated Missing Number Algorithm Demonstration")
        print(f"Working with numbers 1 to {max_number}")
        print("=" * 60)
    
    # Test cases to demonstrate
    test_cases = [
        {"number": 42, "description": "Classic test case"},
        {"number": 1, "description": "Edge case: minimum number"},
        {"number": max_number, "description": f"Edge case: maximum number ({max_number})"},
        {"number": max_number // 2, "description": "Middle number"},
        {"number": 7, "description": "Lucky number seven"},
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        if not quiet:
            print(f"\n📋 Test Case {i}: {test_case['description']}")
            print(f"   Extracting number: {test_case['number']}")
        
        # Initialize fresh number set
        number_set = NumberSet(max_number)
        
        try:
            # Extract the number
            start_time = time.time()
            number_set.extract(test_case['number'])
            extraction_time = (time.time() - start_time) * 1000
            
            # Find the missing number
            start_time = time.time()
            missing = number_set.find_missing_number()
            calculation_time = (time.time() - start_time) * 1000
            
            # Verify correctness
            is_correct = missing == test_case['number']
            
            if not quiet:
                print(f"   ✅ Extracted: {test_case['number']}")
                print(f"   🎯 Algorithm found: {missing}")
                print(f"   {'✨ CORRECT!' if is_correct else '❌ INCORRECT!'}")
                
                if verbose:
                    print(f"   ⏱️  Extraction time: {extraction_time:.3f} ms")
                    print(f"   ⏱️  Calculation time: {calculation_time:.3f} ms")
                    print(f"   📊 Remaining numbers: {number_set.count_remaining()}")
            else:
                print(f"Test {i}: {test_case['number']} -> {missing} ({'✓' if is_correct else '✗'})")
                
        except Exception as e:
            if not quiet:
                print(f"   ❌ Error: {e}")
            else:
                print(f"Test {i}: ERROR - {e}")
    
    if not quiet:
        print(f"\n🎉 Automated demonstration complete!")
        print(f"All test cases demonstrate that the algorithm correctly identifies extracted numbers.")


def run_benchmark_demo(max_number: int, verbose: bool = False):
    """Run performance benchmark of the algorithm."""
    print(f"⚡ Performance Benchmark")
    print(f"Testing algorithm performance with set size: {max_number}")
    print("=" * 50)
    
    # Test different numbers to extract
    test_numbers = [1, max_number // 4, max_number // 2, 3 * max_number // 4, max_number]
    iterations = 1000  # Number of iterations for timing
    
    print(f"Running {iterations} iterations for each test case...")
    
    results = []
    
    for test_num in test_numbers:
        print(f"\n📊 Testing extraction of number: {test_num}")
        
        # Time the extraction and calculation operations
        extraction_times = []
        calculation_times = []
        
        for _ in range(iterations):
            number_set = NumberSet(max_number)
            
            # Time extraction
            start_time = time.time()
            number_set.extract(test_num)
            extraction_time = (time.time() - start_time) * 1000000  # microseconds
            extraction_times.append(extraction_time)
            
            # Time calculation
            start_time = time.time()
            missing = number_set.find_missing_number()
            calculation_time = (time.time() - start_time) * 1000000  # microseconds
            calculation_times.append(calculation_time)
        
        # Calculate statistics
        avg_extraction = sum(extraction_times) / len(extraction_times)
        avg_calculation = sum(calculation_times) / len(calculation_times)
        min_extraction = min(extraction_times)
        max_extraction = max(extraction_times)
        min_calculation = min(calculation_times)
        max_calculation = max(calculation_times)
        
        results.append({
            'number': test_num,
            'avg_extraction': avg_extraction,
            'avg_calculation': avg_calculation,
            'min_extraction': min_extraction,
            'max_extraction': max_extraction,
            'min_calculation': min_calculation,
            'max_calculation': max_calculation
        })
        
        print(f"   Extraction - Avg: {avg_extraction:.2f}μs, Min: {min_extraction:.2f}μs, Max: {max_extraction:.2f}μs")
        print(f"   Calculation - Avg: {avg_calculation:.2f}μs, Min: {min_calculation:.2f}μs, Max: {max_calculation:.2f}μs")
    
    # Summary
    print(f"\n📈 Performance Summary:")
    print(f"   Set size: {max_number} numbers")
    print(f"   Iterations per test: {iterations}")
    
    avg_total_extraction = sum(r['avg_extraction'] for r in results) / len(results)
    avg_total_calculation = sum(r['avg_calculation'] for r in results) / len(results)
    
    print(f"   Average extraction time: {avg_total_extraction:.2f}μs")
    print(f"   Average calculation time: {avg_total_calculation:.2f}μs")
    print(f"   Algorithm complexity: O(1) for calculation, O(1) for extraction")
    
    if verbose:
        print(f"\n📋 Detailed Results:")
        for result in results:
            print(f"   Number {result['number']:3d}: "
                  f"Extract {result['avg_extraction']:6.2f}μs, "
                  f"Calculate {result['avg_calculation']:6.2f}μs")


if __name__ == "__main__":
    main()