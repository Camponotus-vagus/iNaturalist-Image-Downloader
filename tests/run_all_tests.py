#!/usr/bin/env python3
"""
Run all tests for iNaturalist Image Downloader
"""

import subprocess
import sys
import os

def main():
    print("="*70)
    print("    iNaturalist Image Downloader - Complete Test Suite")
    print("="*70)
    print()

    test_dir = os.path.dirname(os.path.abspath(__file__))

    tests = [
        ("test_downloader.py", "Core Functionality Tests"),
        ("test_mocked.py", "Mock-based Logic Tests"),
        ("test_import.py", "Import & Static Analysis"),
        ("test_integration.py", "Integration Tests"),
        ("test_new_features.py", "New Features Tests"),
    ]

    results = []
    for test_file, description in tests:
        print(f"\n{'='*70}")
        print(f"Running: {description}")
        print(f"File: {test_file}")
        print("="*70 + "\n")

        test_path = os.path.join(test_dir, test_file)
        result = subprocess.run([sys.executable, test_path], capture_output=False)
        results.append((test_file, result.returncode))

    print("\n" + "="*70)
    print("OVERALL TEST SUMMARY")
    print("="*70)
    for test_file, returncode in results:
        status = "PASSED" if returncode == 0 else "FAILED"
        print(f"  {test_file}: {status}")

    all_passed = all(rc == 0 for _, rc in results)
    print()
    if all_passed:
        print("All test suites completed successfully!")
    else:
        print("Some test suites had failures.")
        sys.exit(1)


if __name__ == "__main__":
    main()
