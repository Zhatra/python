#!/usr/bin/env python3
"""
Integration test runner script.

This script provides a convenient way to run integration tests with
different configurations and options.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description=""):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    if description:
        print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, check=True, capture_output=False)
        print(f"\n✅ {description or 'Command'} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description or 'Command'} failed with exit code {e.returncode}")
        return False


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Run integration tests for the data pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_integration_tests.py                    # Run basic integration tests
  python run_integration_tests.py --all              # Run all tests including performance
  python run_integration_tests.py --performance      # Run only performance tests
  python run_integration_tests.py --api              # Run only API tests
  python run_integration_tests.py --pipeline         # Run only pipeline tests
  python run_integration_tests.py --postgres         # Use PostgreSQL instead of SQLite
  python run_integration_tests.py --verbose          # Verbose output
  python run_integration_tests.py --coverage         # Run with coverage report
        """
    )
    
    # Test selection options
    parser.add_argument(
        "--all", 
        action="store_true",
        help="Run all tests including performance and slow tests"
    )
    parser.add_argument(
        "--performance", 
        action="store_true",
        help="Run performance tests"
    )
    parser.add_argument(
        "--slow", 
        action="store_true",
        help="Run slow tests"
    )
    parser.add_argument(
        "--api", 
        action="store_true",
        help="Run only API integration tests"
    )
    parser.add_argument(
        "--pipeline", 
        action="store_true",
        help="Run only data pipeline integration tests"
    )
    
    # Database options
    parser.add_argument(
        "--postgres", 
        action="store_true",
        help="Use PostgreSQL for database tests"
    )
    parser.add_argument(
        "--memory-db", 
        action="store_true",
        help="Use in-memory SQLite database (default)"
    )
    
    # Output options
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet output"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run tests with coverage report"
    )
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML test report"
    )
    
    # Test filtering options
    parser.add_argument(
        "--filter", "-k",
        type=str,
        help="Filter tests by keyword"
    )
    parser.add_argument(
        "--markers", "-m",
        type=str,
        help="Run tests with specific markers"
    )
    
    # Parallel execution
    parser.add_argument(
        "--parallel", "-n",
        type=int,
        help="Run tests in parallel (number of workers)"
    )
    
    # Output directory
    parser.add_argument(
        "--output-dir",
        type=str,
        default="tests/integration/reports",
        help="Output directory for reports"
    )
    
    args = parser.parse_args()
    
    # Ensure we're in the project root
    project_root = Path(__file__).parent.parent.parent
    os.chdir(project_root)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    # Add test directory
    if args.api:
        pytest_cmd.append("tests/integration/test_api_workflow.py")
        pytest_cmd.append("tests/integration/test_api_integration.py")
    elif args.pipeline:
        pytest_cmd.append("tests/integration/test_complete_pipeline.py")
        pytest_cmd.append("tests/integration/test_data_loader_integration.py")
    else:
        pytest_cmd.append("tests/integration/")
    
    # Add verbosity options
    if args.verbose:
        pytest_cmd.extend(["-v", "-s"])
    elif args.quiet:
        pytest_cmd.append("-q")
    
    # Add test selection options
    if args.all:
        pytest_cmd.extend(["--run-performance", "--run-slow"])
    elif args.performance:
        pytest_cmd.extend(["-m", "performance", "--run-performance"])
    elif args.slow:
        pytest_cmd.extend(["-m", "slow", "--run-slow"])
    
    # Add database options
    if args.postgres:
        pytest_cmd.append("--use-postgres")
    
    # Add filtering options
    if args.filter:
        pytest_cmd.extend(["-k", args.filter])
    
    if args.markers:
        pytest_cmd.extend(["-m", args.markers])
    
    # Add parallel execution
    if args.parallel:
        pytest_cmd.extend(["-n", str(args.parallel)])
    
    # Add coverage options
    if args.coverage:
        pytest_cmd.extend([
            "--cov=src",
            "--cov-report=term-missing",
            f"--cov-report=html:{output_dir}/coverage_html",
            f"--cov-report=xml:{output_dir}/coverage.xml"
        ])
    
    # Add HTML report
    if args.html_report:
        pytest_cmd.extend([
            f"--html={output_dir}/report.html",
            "--self-contained-html"
        ])
    
    # Add JUnit XML report for CI
    pytest_cmd.extend([f"--junit-xml={output_dir}/junit.xml"])
    
    # Print configuration
    print("Integration Test Runner")
    print("=" * 60)
    print(f"Project root: {project_root}")
    print(f"Output directory: {output_dir}")
    print(f"Test selection: {'All tests' if args.all else 'Basic integration tests'}")
    if args.performance:
        print("Including: Performance tests")
    if args.slow:
        print("Including: Slow tests")
    if args.api:
        print("Focus: API tests only")
    if args.pipeline:
        print("Focus: Pipeline tests only")
    if args.postgres:
        print("Database: PostgreSQL")
    else:
        print("Database: SQLite (in-memory)")
    if args.coverage:
        print("Coverage: Enabled")
    if args.html_report:
        print("HTML Report: Enabled")
    
    # Check dependencies
    print("\nChecking dependencies...")
    
    required_packages = ["pytest", "pandas", "sqlalchemy", "fastapi"]
    optional_packages = ["pytest-cov", "pytest-html", "pytest-xdist", "psutil"]
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            missing_required.append(package)
            print(f"❌ {package} (required)")
    
    for package in optional_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            missing_optional.append(package)
            print(f"⚠️  {package} (optional)")
    
    if missing_required:
        print(f"\n❌ Missing required packages: {', '.join(missing_required)}")
        print("Please install them with: pip install " + " ".join(missing_required))
        return 1
    
    if missing_optional:
        print(f"\n⚠️  Missing optional packages: {', '.join(missing_optional)}")
        print("Some features may not be available. Install with: pip install " + " ".join(missing_optional))
    
    # Run pre-test checks
    print("\nRunning pre-test checks...")
    
    # Check if source code is importable
    try:
        sys.path.insert(0, str(project_root))
        from src import config
        print("✅ Source code imports successfully")
    except ImportError as e:
        print(f"❌ Cannot import source code: {e}")
        return 1
    
    # Check database connectivity if using PostgreSQL
    if args.postgres:
        print("Checking PostgreSQL connectivity...")
        try:
            from src.database.connection import DatabaseConnection
            
            test_db_config = {
                'host': os.getenv('TEST_DB_HOST', 'localhost'),
                'port': int(os.getenv('TEST_DB_PORT', '5432')),
                'database': os.getenv('TEST_DB_NAME', 'test_technical_test'),
                'username': os.getenv('TEST_DB_USER', 'testuser'),
                'password': os.getenv('TEST_DB_PASSWORD', 'testpass')
            }
            
            connection_string = (
                f"postgresql://{test_db_config['username']}:{test_db_config['password']}"
                f"@{test_db_config['host']}:{test_db_config['port']}/{test_db_config['database']}"
            )
            
            db_conn = DatabaseConnection(connection_string)
            if db_conn.test_connection():
                print("✅ PostgreSQL connection successful")
            else:
                print("❌ PostgreSQL connection failed")
                print("Falling back to SQLite in-memory database")
                pytest_cmd = [cmd for cmd in pytest_cmd if cmd != "--use-postgres"]
        except Exception as e:
            print(f"⚠️  PostgreSQL check failed: {e}")
            print("Falling back to SQLite in-memory database")
            pytest_cmd = [cmd for cmd in pytest_cmd if cmd != "--use-postgres"]
    
    # Run the tests
    print(f"\nRunning integration tests...")
    success = run_command(pytest_cmd, "Integration Tests")
    
    # Generate summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ All integration tests passed!")
        
        if args.coverage:
            print(f"📊 Coverage report: {output_dir}/coverage_html/index.html")
        
        if args.html_report:
            print(f"📋 Test report: {output_dir}/report.html")
        
        print(f"📄 JUnit XML: {output_dir}/junit.xml")
        
    else:
        print("❌ Some integration tests failed!")
        print("Check the output above for details.")
        return 1
    
    # Additional reports
    if args.coverage:
        print(f"\nCoverage Summary:")
        coverage_cmd = ["python", "-m", "coverage", "report", "--show-missing"]
        run_command(coverage_cmd, "Coverage Summary")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())