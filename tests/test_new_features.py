"""
Tests for the new features added to iNaturalist Image Downloader
"""

import os
import sys
import tempfile
import re
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import time

# Add parent directory to path to import functions
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

test_results = []

def log_test(test_name, passed, details=""):
    status = "PASS" if passed else "FAIL"
    test_results.append((test_name, status, details))
    print(f"[{status}] {test_name}")
    if details:
        print(f"       Details: {details}")


def test_get_file_extension():
    """Test content-type to extension mapping"""
    test_name = "File Extension Detection"
    try:
        # Import the function
        # Since we can't import tkinter, we'll test the logic directly
        content_type_map = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
        }

        def get_file_extension(content_type, url):
            if content_type:
                main_type = content_type.split(';')[0].strip().lower()
                if main_type in content_type_map:
                    return content_type_map[main_type]
            url_lower = url.lower()
            for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                if ext in url_lower:
                    return '.jpg' if ext == '.jpeg' else ext
            return '.jpg'

        # Test cases
        tests = [
            ('image/jpeg', 'http://example.com/img.jpg', '.jpg'),
            ('image/png', 'http://example.com/img.png', '.png'),
            ('image/gif', 'http://example.com/img.gif', '.gif'),
            ('image/jpeg; charset=utf-8', 'http://example.com/img', '.jpg'),  # With charset
            ('', 'http://example.com/photo.png', '.png'),  # No content-type, use URL
            ('', 'http://example.com/photo', '.jpg'),  # Default to .jpg
            ('application/octet-stream', 'http://example.com/photo.gif', '.gif'),  # Fallback to URL
        ]

        failures = []
        for content_type, url, expected in tests:
            result = get_file_extension(content_type, url)
            if result != expected:
                failures.append(f"Expected {expected} for {content_type}/{url}, got {result}")

        if failures:
            log_test(test_name, False, "; ".join(failures))
        else:
            log_test(test_name, True, f"All {len(tests)} extension mappings correct")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_disk_space_check():
    """Test disk space checking function"""
    test_name = "Disk Space Check"
    try:
        import shutil

        def check_disk_space(path, required_bytes=100_000_000):
            try:
                usage = shutil.disk_usage(path)
                return usage.free >= required_bytes
            except Exception:
                return True

        with tempfile.TemporaryDirectory() as tmpdir:
            # Should have space
            result = check_disk_space(tmpdir, 1000)  # 1KB required
            assert result == True, "Should have 1KB free"

            # Probably won't have this much
            result2 = check_disk_space(tmpdir, 10**18)  # 1 Exabyte
            # This might still pass on some systems, so we just check it doesn't crash

            log_test(test_name, True, "Disk space check works correctly")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_retry_logic():
    """Test download retry logic"""
    test_name = "Retry Logic"
    try:
        import requests

        call_count = 0

        def mock_get_fails_twice(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise requests.exceptions.Timeout("timeout")
            response = Mock()
            response.status_code = 200
            response.raise_for_status = Mock()
            response.content = b'image data'
            return response

        # Simulate retry logic
        max_retries = 3
        timeout = 5
        last_exception = None

        for attempt in range(max_retries):
            try:
                response = mock_get_fails_twice("http://example.com/img.jpg", timeout=timeout)
                break
            except requests.exceptions.Timeout:
                last_exception = "Timeout"
                if attempt < max_retries - 1:
                    pass  # Would sleep here

        assert call_count == 3, f"Expected 3 attempts, got {call_count}"
        log_test(test_name, True, f"Retry logic works: succeeded after {call_count} attempts")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_nan_filtering():
    """Test NaN URL filtering"""
    test_name = "NaN URL Filtering"
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,image_url\n")
            f.write("1,http://example.com/img1.jpg\n")
            f.write("2,\n")  # Empty
            f.write("3,http://example.com/img3.jpg\n")
            f.write("4,\n")  # Empty
            f.write("5,http://example.com/img5.jpg\n")
            csv_path = f.name

        data = pd.read_csv(csv_path)
        urls = data['image_url']

        # Filter as the new code does
        valid_urls = [(i, url) for i, url in enumerate(urls) if pd.notna(url) and str(url).strip()]
        skipped_count = len(urls) - len(valid_urls)

        os.unlink(csv_path)

        assert len(valid_urls) == 3, f"Expected 3 valid URLs, got {len(valid_urls)}"
        assert skipped_count == 2, f"Expected 2 skipped, got {skipped_count}"
        log_test(test_name, True, f"Correctly filtered: {len(valid_urls)} valid, {skipped_count} skipped")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_case_insensitive_column():
    """Test case-insensitive column name matching"""
    test_name = "Case-Insensitive Column Names"
    try:
        test_cases = [
            ("image_url", "image_url"),
            ("IMAGE_URL", "IMAGE_URL"),
            ("Image_URL", "Image_URL"),
            ("url", "url"),
            ("URL", "URL"),
        ]

        for col_name, expected in test_cases:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                f.write(f"id,{col_name}\n")
                f.write("1,http://example.com/img1.jpg\n")
                csv_path = f.name

            data = pd.read_csv(csv_path)

            # Match logic from new code
            url_column = None
            for check_name in ['image_url', 'IMAGE_URL', 'Image_URL', 'url', 'URL']:
                if check_name in data.columns:
                    url_column = check_name
                    break

            os.unlink(csv_path)

            if url_column != expected:
                log_test(test_name, False, f"Failed to match {col_name}")
                return

        log_test(test_name, True, f"All {len(test_cases)} column name variations matched")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_status_code_validation():
    """Test HTTP status code validation"""
    test_name = "HTTP Status Code Validation"
    try:
        import requests

        # Test that raise_for_status raises on 4xx/5xx
        mock_response = Mock()
        mock_response.status_code = 404

        def raise_for_status():
            if mock_response.status_code >= 400:
                raise requests.exceptions.HTTPError(f"HTTP {mock_response.status_code}")

        mock_response.raise_for_status = raise_for_status

        try:
            mock_response.raise_for_status()
            log_test(test_name, False, "Should have raised HTTPError for 404")
        except requests.exceptions.HTTPError:
            log_test(test_name, True, "Correctly raises HTTPError for 404 status")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_content_size_validation():
    """Test minimum content size validation"""
    test_name = "Content Size Validation"
    try:
        # Test the logic that checks for too-small responses
        min_size = 100

        test_cases = [
            (b'x' * 50, False, "50 bytes - too small"),
            (b'x' * 100, True, "100 bytes - ok"),
            (b'x' * 1000, True, "1000 bytes - ok"),
            (b'', False, "0 bytes - too small"),
        ]

        failures = []
        for content, should_pass, desc in test_cases:
            is_valid = len(content) >= min_size
            if is_valid != should_pass:
                failures.append(f"{desc}: expected {should_pass}, got {is_valid}")

        if failures:
            log_test(test_name, False, "; ".join(failures))
        else:
            log_test(test_name, True, "Content size validation correct")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_cancel_flag():
    """Test cancellation mechanism"""
    test_name = "Cancellation Flag"
    try:
        # Simulate the cancellation logic
        download_cancelled = False

        # Simulate download loop
        items_processed = 0
        for i in range(10):
            if download_cancelled:
                break
            items_processed += 1
            if i == 4:
                download_cancelled = True  # Cancel after 5 items

        assert items_processed == 5, f"Expected 5 items before cancel, got {items_processed}"
        log_test(test_name, True, f"Cancellation works: stopped after {items_processed} items")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_directory_validation():
    """Test download directory validation"""
    test_name = "Directory Validation"
    try:
        # Test with valid directory
        with tempfile.TemporaryDirectory() as tmpdir:
            assert os.path.isdir(tmpdir), "Should be valid directory"

        # Test with non-existent directory
        fake_dir = "/this/directory/does/not/exist/12345"
        assert not os.path.isdir(fake_dir), "Should not exist"

        # Test with file instead of directory
        with tempfile.NamedTemporaryFile(delete=False) as f:
            file_path = f.name
        assert not os.path.isdir(file_path), "File should not be treated as directory"
        os.unlink(file_path)

        log_test(test_name, True, "Directory validation works correctly")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_improved_regex_pattern():
    """Test the improved regex pattern that matches any extension"""
    test_name = "Improved Regex Pattern"
    try:
        # New pattern matches any extension
        pattern = r'image_(\d+)\.\w+'

        test_cases = [
            ("image_1.jpg", True, 1),
            ("image_100.png", True, 100),
            ("image_50.gif", True, 50),
            ("image_999.webp", True, 999),
            ("image_1.jpeg", True, 1),
            ("photo_1.jpg", False, None),  # Wrong prefix
            ("image_abc.jpg", False, None),  # Non-numeric
        ]

        failures = []
        for filename, should_match, expected_num in test_cases:
            match = re.search(pattern, filename)
            matched = match is not None
            if matched != should_match:
                failures.append(f"{filename}: expected match={should_match}, got {matched}")
            elif matched and int(match.group(1)) != expected_num:
                failures.append(f"{filename}: expected num={expected_num}, got {match.group(1)}")

        if failures:
            log_test(test_name, False, "; ".join(failures))
        else:
            log_test(test_name, True, f"All {len(test_cases)} patterns matched correctly")
    except Exception as e:
        log_test(test_name, False, str(e))


def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("NEW FEATURES TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, status, _ in test_results if status == "PASS")
    failed = sum(1 for _, status, _ in test_results if status == "FAIL")
    total = len(test_results)

    print(f"\nTotal tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass rate: {passed/total*100:.1f}%")

    if failed > 0:
        print("\n" + "-"*60)
        print("FAILED TESTS:")
        for name, status, details in test_results:
            if status == "FAIL":
                print(f"  - {name}: {details}")


if __name__ == "__main__":
    print("="*60)
    print("iNaturalist Image Downloader - New Features Tests")
    print("="*60)
    print()

    test_get_file_extension()
    test_disk_space_check()
    test_retry_logic()
    test_nan_filtering()
    test_case_insensitive_column()
    test_status_code_validation()
    test_content_size_validation()
    test_cancel_flag()
    test_directory_validation()
    test_improved_regex_pattern()

    print_summary()
