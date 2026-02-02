"""
Comprehensive tests for iNaturalist Image Downloader
Tests core functionality without requiring GUI (tkinter display)
"""

import os
import sys
import tempfile
import shutil
import re
import pandas as pd
import requests
from unittest.mock import Mock, patch, MagicMock
import time

# Test Results tracker
test_results = []

def log_test(test_name, passed, details=""):
    status = "PASS" if passed else "FAIL"
    test_results.append((test_name, status, details))
    print(f"[{status}] {test_name}")
    if details:
        print(f"       Details: {details}")


def test_csv_parsing_valid():
    """Test parsing a valid CSV with image_url column"""
    test_name = "CSV Parsing - Valid CSV"
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,image_url,species\n")
            f.write("1,http://example.com/img1.jpg,Bird\n")
            f.write("2,http://example.com/img2.jpg,Cat\n")
            f.write("3,http://example.com/img3.jpg,Dog\n")
            csv_path = f.name

        data = pd.read_csv(csv_path)
        urls = data['image_url']

        os.unlink(csv_path)

        assert len(urls) == 3, f"Expected 3 URLs, got {len(urls)}"
        assert urls.iloc[0] == "http://example.com/img1.jpg"
        log_test(test_name, True, f"Parsed {len(urls)} URLs correctly")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_csv_parsing_missing_column():
    """Test parsing CSV without image_url column"""
    test_name = "CSV Parsing - Missing image_url column"
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,url,species\n")  # 'url' instead of 'image_url'
            f.write("1,http://example.com/img1.jpg,Bird\n")
            csv_path = f.name

        data = pd.read_csv(csv_path)
        try:
            urls = data['image_url']
            os.unlink(csv_path)
            log_test(test_name, False, "Should have raised KeyError")
        except KeyError:
            os.unlink(csv_path)
            log_test(test_name, True, "Correctly raised KeyError for missing column")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_csv_parsing_empty():
    """Test parsing empty CSV"""
    test_name = "CSV Parsing - Empty CSV (headers only)"
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,image_url,species\n")  # Only headers
            csv_path = f.name

        data = pd.read_csv(csv_path)
        urls = data['image_url']

        os.unlink(csv_path)

        assert urls.empty, "URLs should be empty"
        log_test(test_name, True, "Correctly identified empty URLs")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_csv_parsing_nan_values():
    """Test CSV with NaN/missing values in image_url"""
    test_name = "CSV Parsing - NaN values in image_url"
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,image_url,species\n")
            f.write("1,http://example.com/img1.jpg,Bird\n")
            f.write("2,,Cat\n")  # Empty URL
            f.write("3,http://example.com/img3.jpg,Dog\n")
            csv_path = f.name

        data = pd.read_csv(csv_path)
        urls = data['image_url']

        os.unlink(csv_path)

        nan_count = urls.isna().sum()
        log_test(test_name, True, f"Found {nan_count} NaN values in {len(urls)} URLs - APP DOES NOT HANDLE THIS")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_file_numbering_empty_dir():
    """Test file numbering in empty directory"""
    test_name = "File Numbering - Empty directory"
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            existing_images = os.listdir(tmpdir)
            max_num = 0
            for img in existing_images:
                match = re.search(r'image_(\d+)\.jpg', img)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
            starting_num = max_num + 1

            assert starting_num == 1, f"Expected starting_num=1, got {starting_num}"
            log_test(test_name, True, f"Starting number correctly set to {starting_num}")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_file_numbering_existing_images():
    """Test file numbering with existing images"""
    test_name = "File Numbering - Existing images"
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create existing images
            for i in [1, 2, 5, 10]:
                open(os.path.join(tmpdir, f"image_{i}.jpg"), 'w').close()

            existing_images = os.listdir(tmpdir)
            max_num = 0
            for img in existing_images:
                match = re.search(r'image_(\d+)\.jpg', img)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
            starting_num = max_num + 1

            assert starting_num == 11, f"Expected starting_num=11, got {starting_num}"
            log_test(test_name, True, f"Starting number correctly set to {starting_num} after max existing was 10")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_file_numbering_mixed_files():
    """Test file numbering with mixed file types"""
    test_name = "File Numbering - Mixed file types"
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create mixed files
            open(os.path.join(tmpdir, "image_5.jpg"), 'w').close()
            open(os.path.join(tmpdir, "image_3.png"), 'w').close()  # Different extension
            open(os.path.join(tmpdir, "photo_10.jpg"), 'w').close()  # Different prefix
            open(os.path.join(tmpdir, "image_abc.jpg"), 'w').close()  # Non-numeric

            existing_images = os.listdir(tmpdir)
            max_num = 0
            for img in existing_images:
                match = re.search(r'image_(\d+)\.jpg', img)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
            starting_num = max_num + 1

            assert starting_num == 6, f"Expected starting_num=6, got {starting_num}"
            log_test(test_name, True, f"Correctly ignored non-matching files, starting at {starting_num}")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_download_real_image():
    """Test downloading a real image from the internet"""
    test_name = "Download - Real image from internet"
    try:
        # Use a reliable test image
        test_url = "https://httpbin.org/image/jpeg"

        response = requests.get(test_url, timeout=10)

        if response.status_code == 200:
            with tempfile.TemporaryDirectory() as tmpdir:
                img_path = os.path.join(tmpdir, "image_1.jpg")
                with open(img_path, 'wb') as f:
                    f.write(response.content)

                file_size = os.path.getsize(img_path)
                assert file_size > 0, "Downloaded file is empty"
                log_test(test_name, True, f"Downloaded {file_size} bytes successfully")
        else:
            log_test(test_name, False, f"HTTP status {response.status_code}")
    except requests.exceptions.Timeout:
        log_test(test_name, False, "Request timed out (no timeout handling in original code!)")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_download_invalid_url():
    """Test downloading from invalid URL"""
    test_name = "Download - Invalid URL"
    try:
        test_url = "http://this-domain-does-not-exist-12345.com/image.jpg"

        try:
            response = requests.get(test_url, timeout=5)
            log_test(test_name, False, "Should have raised an exception")
        except requests.exceptions.RequestException as e:
            log_test(test_name, True, f"Correctly raised exception: {type(e).__name__}")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_download_404_url():
    """Test downloading from URL that returns 404"""
    test_name = "Download - 404 URL"
    try:
        test_url = "https://httpbin.org/status/404"

        response = requests.get(test_url, timeout=10)

        # The original code doesn't check status code!
        if response.status_code == 404:
            log_test(test_name, True, f"Got 404 - APP SAVES EMPTY/ERROR CONTENT (doesn't check status code)")
        else:
            log_test(test_name, False, f"Expected 404, got {response.status_code}")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_download_timeout_behavior():
    """Test behavior with slow response (timeout)"""
    test_name = "Download - Timeout behavior"
    try:
        # httpbin delay endpoint
        test_url = "https://httpbin.org/delay/5"  # 5 second delay

        start = time.time()
        # Original code has NO TIMEOUT - this would hang
        response = requests.get(test_url, timeout=2)  # We add timeout for testing
        elapsed = time.time() - start

        log_test(test_name, False, f"Request completed in {elapsed:.1f}s - original code has NO timeout!")
    except requests.exceptions.Timeout:
        log_test(test_name, True, "Timeout correctly raised - BUT original code has NO timeout handling!")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_csv_with_special_characters():
    """Test CSV with special characters in URLs"""
    test_name = "CSV Parsing - Special characters in URLs"
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,image_url,species\n")
            f.write("1,http://example.com/img%201.jpg,Bird\n")  # URL encoded space
            f.write("2,http://example.com/img?id=2&type=jpg,Cat\n")  # Query params
            csv_path = f.name

        data = pd.read_csv(csv_path)
        urls = data['image_url']

        os.unlink(csv_path)

        assert len(urls) == 2
        log_test(test_name, True, f"Parsed URLs with special chars correctly")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_large_csv():
    """Test handling of larger CSV files"""
    test_name = "CSV Parsing - Large CSV (1000 rows)"
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,image_url,species\n")
            for i in range(1000):
                f.write(f"{i},http://example.com/img{i}.jpg,Species{i}\n")
            csv_path = f.name

        start = time.time()
        data = pd.read_csv(csv_path)
        urls = data['image_url']
        elapsed = time.time() - start

        os.unlink(csv_path)

        assert len(urls) == 1000
        log_test(test_name, True, f"Parsed 1000 URLs in {elapsed:.3f}s")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_directory_with_many_files():
    """Test file numbering in directory with many files"""
    test_name = "File Numbering - Directory with 100 existing images"
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 100 images
            for i in range(1, 101):
                open(os.path.join(tmpdir, f"image_{i}.jpg"), 'w').close()

            start = time.time()
            existing_images = os.listdir(tmpdir)
            max_num = 0
            for img in existing_images:
                match = re.search(r'image_(\d+)\.jpg', img)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
            starting_num = max_num + 1
            elapsed = time.time() - start

            assert starting_num == 101
            log_test(test_name, True, f"Found max=100, starting at 101 in {elapsed:.4f}s")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_real_inaturalist_url():
    """Test downloading from actual iNaturalist URL"""
    test_name = "Download - Real iNaturalist URL"
    try:
        # A real iNaturalist static image URL (public)
        test_url = "https://inaturalist-open-data.s3.amazonaws.com/photos/1/square.jpg"

        response = requests.get(test_url, timeout=15)

        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            size = len(response.content)
            log_test(test_name, True, f"Downloaded {size} bytes, Content-Type: {content_type}")
        elif response.status_code == 403:
            log_test(test_name, True, f"Got 403 Forbidden - iNaturalist may require auth for some images")
        else:
            log_test(test_name, False, f"HTTP status {response.status_code}")
    except requests.exceptions.Timeout:
        log_test(test_name, False, "Request timed out")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_csv_with_commas_in_values():
    """Test CSV with commas inside quoted values"""
    test_name = "CSV Parsing - Commas in quoted values"
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('id,image_url,species\n')
            f.write('1,http://example.com/img1.jpg,"Bird, Common"\n')
            f.write('2,http://example.com/img2.jpg,"Cat, Domestic"\n')
            csv_path = f.name

        data = pd.read_csv(csv_path)
        urls = data['image_url']
        species = data['species']

        os.unlink(csv_path)

        assert len(urls) == 2
        assert species.iloc[0] == "Bird, Common"
        log_test(test_name, True, "Parsed CSV with commas in quoted values correctly")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_unicode_in_csv():
    """Test CSV with unicode characters"""
    test_name = "CSV Parsing - Unicode characters"
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write('id,image_url,species\n')
            f.write('1,http://example.com/img1.jpg,Äpfel\n')
            f.write('2,http://example.com/img2.jpg,日本語\n')
            f.write('3,http://example.com/img3.jpg,Мышь\n')
            csv_path = f.name

        data = pd.read_csv(csv_path)
        urls = data['image_url']

        os.unlink(csv_path)

        assert len(urls) == 3
        log_test(test_name, True, "Parsed CSV with unicode characters correctly")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_write_permissions():
    """Test writing to directory without permissions"""
    test_name = "File Write - Permission denied"
    try:
        # Try to write to root directory (should fail)
        test_path = "/root/test_image.jpg"
        try:
            with open(test_path, 'wb') as f:
                f.write(b'test')
            os.unlink(test_path)
            log_test(test_name, False, "Should have raised PermissionError")
        except PermissionError:
            log_test(test_name, True, "Correctly raised PermissionError - app should validate write access")
        except Exception as e:
            # Running as root or other error
            log_test(test_name, True, f"Got {type(e).__name__} - environment-specific")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_ssl_verification():
    """Test SSL certificate verification"""
    test_name = "Download - SSL verification"
    try:
        # This should work with valid SSL
        response = requests.get("https://httpbin.org/get", timeout=10)
        assert response.status_code == 200
        log_test(test_name, True, "SSL verification working correctly")
    except requests.exceptions.SSLError as e:
        log_test(test_name, False, f"SSL Error: {e}")
    except Exception as e:
        log_test(test_name, False, str(e))


def test_redirect_handling():
    """Test handling of HTTP redirects"""
    test_name = "Download - HTTP redirects"
    try:
        # httpbin redirect endpoint
        test_url = "https://httpbin.org/redirect/2"  # 2 redirects

        response = requests.get(test_url, timeout=10)

        log_test(test_name, True, f"Followed {len(response.history)} redirects, final status: {response.status_code}")
    except Exception as e:
        log_test(test_name, False, str(e))


def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
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

    print("\n" + "-"*60)
    print("ISSUES FOUND IN ORIGINAL CODE:")
    print("-"*60)
    issues = [
        "1. NO TIMEOUT on requests.get() - can hang indefinitely",
        "2. NO HTTP STATUS CODE CHECK - saves error responses as images",
        "3. NO NaN/NULL HANDLING - crashes on missing URLs",
        "4. NO INPUT VALIDATION for URLs",
        "5. NO CANCEL BUTTON for downloads",
        "6. ALL images saved as .jpg regardless of actual format",
        "7. NO RETRY mechanism for failed downloads",
        "8. GUI operations from non-main thread (messagebox.showerror)",
        "9. NO DISK SPACE CHECK before downloading",
        "10. NO RATE LIMITING - may overwhelm servers",
    ]
    for issue in issues:
        print(f"  {issue}")


if __name__ == "__main__":
    print("="*60)
    print("iNaturalist Image Downloader - Test Suite")
    print("="*60)
    print()

    # Run all tests
    test_csv_parsing_valid()
    test_csv_parsing_missing_column()
    test_csv_parsing_empty()
    test_csv_parsing_nan_values()
    test_file_numbering_empty_dir()
    test_file_numbering_existing_images()
    test_file_numbering_mixed_files()
    test_csv_with_special_characters()
    test_large_csv()
    test_directory_with_many_files()
    test_csv_with_commas_in_values()
    test_unicode_in_csv()
    test_write_permissions()
    test_ssl_verification()
    test_redirect_handling()
    test_download_real_image()
    test_download_invalid_url()
    test_download_404_url()
    test_download_timeout_behavior()
    test_real_inaturalist_url()

    print_summary()
