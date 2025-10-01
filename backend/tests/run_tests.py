"""
Test runner script for admin functionality tests
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_config import setup_test_environment, teardown_test_environment


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> int:
    """Run a command and return the exit code."""
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def run_unit_tests(test_path: str, verbose: bool = False, coverage: bool = False) -> int:
    """Run unit tests."""
    cmd = ["python", "-m", "pytest", test_path]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80"
        ])
    
    return run_command(cmd, cwd=project_root)


def run_integration_tests(test_path: str, verbose: bool = False) -> int:
    """Run integration tests."""
    cmd = ["python", "-m", "pytest", test_path, "-m", "integration"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, cwd=project_root)


def run_security_tests(test_path: str, verbose: bool = False) -> int:
    """Run security tests."""
    cmd = ["python", "-m", "pytest", test_path, "-m", "security"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, cwd=project_root)


def run_performance_tests(test_path: str, verbose: bool = False) -> int:
    """Run performance tests."""
    cmd = ["python", "-m", "pytest", test_path, "-m", "performance"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, cwd=project_root)


def run_e2e_tests(test_path: str, verbose: bool = False) -> int:
    """Run end-to-end tests."""
    cmd = ["python", "-m", "pytest", test_path, "-m", "e2e"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, cwd=project_root)


def run_all_tests(verbose: bool = False, coverage: bool = False) -> int:
    """Run all tests."""
    print("Running all tests...")
    
    # Setup test environment
    setup_test_environment()
    
    try:
        # Run unit tests
        print("\n=== Running Unit Tests ===")
        exit_code = run_unit_tests("tests/", verbose, coverage)
        if exit_code != 0:
            return exit_code
        
        # Run integration tests
        print("\n=== Running Integration Tests ===")
        exit_code = run_integration_tests("tests/", verbose)
        if exit_code != 0:
            return exit_code
        
        # Run security tests
        print("\n=== Running Security Tests ===")
        exit_code = run_security_tests("tests/", verbose)
        if exit_code != 0:
            return exit_code
        
        # Run performance tests
        print("\n=== Running Performance Tests ===")
        exit_code = run_performance_tests("tests/", verbose)
        if exit_code != 0:
            return exit_code
        
        # Run end-to-end tests
        print("\n=== Running End-to-End Tests ===")
        exit_code = run_e2e_tests("tests/", verbose)
        if exit_code != 0:
            return exit_code
        
        print("\n=== All Tests Passed ===")
        return 0
    
    finally:
        # Teardown test environment
        teardown_test_environment()


def run_specific_tests(test_pattern: str, verbose: bool = False, coverage: bool = False) -> int:
    """Run specific tests based on pattern."""
    print(f"Running tests matching pattern: {test_pattern}")
    
    # Setup test environment
    setup_test_environment()
    
    try:
        cmd = ["python", "-m", "pytest", test_pattern]
        
        if verbose:
            cmd.append("-v")
        
        if coverage:
            cmd.extend([
                "--cov=app",
                "--cov-report=html",
                "--cov-report=term-missing",
                "--cov-fail-under=80"
            ])
        
        exit_code = run_command(cmd, cwd=project_root)
        
        if exit_code == 0:
            print(f"Tests matching '{test_pattern}' passed!")
        else:
            print(f"Tests matching '{test_pattern}' failed!")
        
        return exit_code
    
    finally:
        # Teardown test environment
        teardown_test_environment()


def clean_test_artifacts() -> int:
    """Clean up test artifacts."""
    print("Cleaning up test artifacts...")
    
    artifacts = [
        "test.db",
        "test_sync.db",
        "htmlcov",
        ".coverage",
        "coverage.xml",
        ".pytest_cache",
        "__pycache__",
        "*.pyc",
        "*.pyo"
    ]
    
    for artifact in artifacts:
        if artifact.startswith("*"):
            # Handle wildcard patterns
            for path in project_root.rglob(artifact):
                if path.is_file():
                    path.unlink()
                    print(f"Removed file: {path}")
                elif path.is_dir():
                    import shutil
                    shutil.rmtree(path)
                    print(f"Removed directory: {path}")
        else:
            path = project_root / artifact
            if path.exists():
                if path.is_file():
                    path.unlink()
                    print(f"Removed file: {path}")
                elif path.is_dir():
                    import shutil
                    shutil.rmtree(path)
                    print(f"Removed directory: {path}")
    
    return 0


def generate_test_report() -> int:
    """Generate a test report."""
    print("Generating test report...")
    
    cmd = [
        "python", "-m", "pytest",
        "tests/",
        "--html=test_report.html",
        "--self-contained-html",
        "--cov=app",
        "--cov-report=html",
        "--cov-report=xml"
    ]
    
    exit_code = run_command(cmd, cwd=project_root)
    
    if exit_code == 0:
        print("Test report generated successfully!")
        print("HTML report: test_report.html")
        print("Coverage report: htmlcov/index.html")
    else:
        print("Failed to generate test report!")
    
    return exit_code


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test runner for admin functionality")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Unit tests command
    unit_parser = subparsers.add_parser("unit", help="Run unit tests")
    unit_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    unit_parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    unit_parser.add_argument("--path", default="tests/", help="Test path")
    
    # Integration tests command
    integration_parser = subparsers.add_parser("integration", help="Run integration tests")
    integration_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    integration_parser.add_argument("--path", default="tests/", help="Test path")
    
    # Security tests command
    security_parser = subparsers.add_parser("security", help="Run security tests")
    security_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    security_parser.add_argument("--path", default="tests/", help="Test path")
    
    # Performance tests command
    performance_parser = subparsers.add_parser("performance", help="Run performance tests")
    performance_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    performance_parser.add_argument("--path", default="tests/", help="Test path")
    
    # End-to-end tests command
    e2e_parser = subparsers.add_parser("e2e", help="Run end-to-end tests")
    e2e_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    e2e_parser.add_argument("--path", default="tests/", help="Test path")
    
    # All tests command
    all_parser = subparsers.add_parser("all", help="Run all tests")
    all_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    all_parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    
    # Specific tests command
    specific_parser = subparsers.add_parser("specific", help="Run specific tests")
    specific_parser.add_argument("pattern", help="Test pattern")
    specific_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    specific_parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    
    # Clean command
    clean_parser = subparsers.add_parser("clean", help="Clean test artifacts")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate test report")
    
    args = parser.parse_args()
    
    if args.command == "unit":
        return run_unit_tests(args.path, args.verbose, args.coverage)
    elif args.command == "integration":
        return run_integration_tests(args.path, args.verbose)
    elif args.command == "security":
        return run_security_tests(args.path, args.verbose)
    elif args.command == "performance":
        return run_performance_tests(args.path, args.verbose)
    elif args.command == "e2e":
        return run_e2e_tests(args.path, args.verbose)
    elif args.command == "all":
        return run_all_tests(args.verbose, args.coverage)
    elif args.command == "specific":
        return run_specific_tests(args.pattern, args.verbose, args.coverage)
    elif args.command == "clean":
        return clean_test_artifacts()
    elif args.command == "report":
        return generate_test_report()
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())