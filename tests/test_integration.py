"""
Integration test - simulates full download workflow
"""

import os
import sys
import tempfile
import re
import pandas as pd
from unittest.mock import Mock, patch
import time

def test_full_workflow():
    """
    Simulates the complete download workflow as the app would do it,
    using mocked network requests.
    """
    print("="*60)
    print("INTEGRATION TEST: Full Download Workflow")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: Create a realistic iNaturalist export CSV
        print("\n[Step 1] Creating test CSV (iNaturalist format)...")
        csv_path = os.path.join(tmpdir, "observations-export.csv")
        download_path = os.path.join(tmpdir, "downloaded_images")
        os.makedirs(download_path)

        # Real iNaturalist export has these columns
        csv_content = """id,observed_on,time_observed_at,time_zone,user_id,user_login,created_at,updated_at,quality_grade,license,url,image_url,sound_url,tag_list,description,num_identification_agreements,num_identification_disagreements,captive_cultivated,oauth_application_id,place_guess,latitude,longitude,positional_accuracy,private_place_guess,private_latitude,private_longitude,public_positional_accuracy,geoprivacy,taxon_geoprivacy,coordinates_obscured,positioning_method,positioning_device,species_guess,scientific_name,common_name,iconic_taxon_name,taxon_id
123456,2024-01-15,2024-01-15 10:30:00,America/New_York,12345,naturalist1,2024-01-15 12:00:00,2024-01-15 12:00:00,research,CC-BY,https://www.inaturalist.org/observations/123456,https://inaturalist-open-data.s3.amazonaws.com/photos/1/medium.jpg,,bird watching,"A beautiful cardinal",5,0,false,,Central Park,40.785091,-73.968285,10,,,,,,false,,,"Northern Cardinal",Cardinalis cardinalis,Northern Cardinal,Aves,9083
123457,2024-01-16,2024-01-16 14:45:00,America/New_York,12345,naturalist1,2024-01-16 15:00:00,2024-01-16 15:00:00,research,CC-BY,https://www.inaturalist.org/observations/123457,https://inaturalist-open-data.s3.amazonaws.com/photos/2/medium.jpg,,nature walk,"Blue jay at feeder",3,0,false,,Backyard,40.123456,-74.654321,5,,,,,,false,,,"Blue Jay",Cyanocitta cristata,Blue Jay,Aves,8229
123458,2024-01-17,2024-01-17 09:00:00,America/Los_Angeles,67890,birdwatcher2,2024-01-17 10:00:00,2024-01-17 10:00:00,needs_id,CC-BY-NC,https://www.inaturalist.org/observations/123458,https://inaturalist-open-data.s3.amazonaws.com/photos/3/medium.jpg,,,Unknown sparrow,1,0,false,,Golden Gate Park,37.769421,-122.486214,20,,,,,,false,,,"Sparrow",,,Aves,
"""
        with open(csv_path, 'w') as f:
            f.write(csv_content)
        print(f"   Created CSV with 3 observations at: {csv_path}")

        # Step 2: Read CSV (exactly as app does)
        print("\n[Step 2] Reading CSV file...")
        try:
            data = pd.read_csv(csv_path)
            urls = data['image_url']
            print(f"   Read {len(urls)} URLs from CSV")
            print(f"   Sample URL: {urls.iloc[0][:60]}...")
        except Exception as e:
            print(f"   ERROR: {e}")
            return False

        # Step 3: Check for empty URLs
        print("\n[Step 3] Checking for empty URLs...")
        if urls.empty:
            print("   ERROR: No URLs found")
            return False
        nan_count = urls.isna().sum()
        print(f"   Found {nan_count} empty/NaN URLs")

        # Step 4: Calculate starting number
        print("\n[Step 4] Calculating starting image number...")
        existing_images = os.listdir(download_path)
        max_num = 0
        for img in existing_images:
            match = re.search(r'image_(\d+)\.jpg', img)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
        starting_num = max_num + 1
        print(f"   Starting number: {starting_num}")

        # Step 5: Simulate download
        print("\n[Step 5] Simulating download (mocked)...")

        # Create mock response
        mock_response = Mock()
        # Fake JPEG content (JFIF header)
        mock_response.content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00' + b'\x00' * 1000
        mock_response.status_code = 200

        total_size = 0
        total_time = 0
        start_time = time.time()
        downloaded = []

        for i, url in enumerate(urls, start=starting_num):
            download_start_time = time.time()

            # Simulate network delay
            time.sleep(0.01)

            elapsed_time = time.time() - download_start_time

            # Update metrics (exactly as app does)
            total_size += len(mock_response.content)
            total_time += elapsed_time

            mean_speed = (total_size * 8) / (total_time * 1_000_000) if total_time > 0 else 0

            img_name = f"image_{i}.jpg"
            img_path = os.path.join(download_path, img_name)
            with open(img_path, 'wb') as handler:
                handler.write(mock_response.content)

            downloaded.append(img_name)

            # Progress calculation (exactly as app does)
            progress = i - starting_num + 1
            current_time = time.time()
            elapsed_total_time = current_time - start_time
            avg_time_per_image = elapsed_total_time / progress
            remaining = len(urls) - progress
            remaining_time = avg_time_per_image * remaining

            print(f"   [{progress}/{len(urls)}] {img_name} - Speed: {mean_speed:.2f} Mbit/s, ETA: {remaining_time:.2f}s")

        # Step 6: Verify results
        print("\n[Step 6] Verifying results...")
        final_files = sorted(os.listdir(download_path))
        print(f"   Files created: {final_files}")

        expected = ['image_1.jpg', 'image_2.jpg', 'image_3.jpg']
        if final_files == expected:
            print("   [PASS] All images downloaded correctly!")

            # Check file sizes
            for f in final_files:
                size = os.path.getsize(os.path.join(download_path, f))
                print(f"   {f}: {size} bytes")
        else:
            print(f"   [FAIL] Expected {expected}, got {final_files}")
            return False

        # Step 7: Test continuation (existing images)
        print("\n[Step 7] Testing continuation from existing images...")
        existing_images = os.listdir(download_path)
        max_num = 0
        for img in existing_images:
            match = re.search(r'image_(\d+)\.jpg', img)
            if match:
                num = int(match.group(1))
                if num > max_num:
                    max_num = num
        next_starting_num = max_num + 1
        print(f"   Next run would start at: image_{next_starting_num}.jpg")

        if next_starting_num == 4:
            print("   [PASS] Continuation logic works correctly!")
        else:
            print(f"   [FAIL] Expected next=4, got {next_starting_num}")
            return False

    print("\n" + "="*60)
    print("INTEGRATION TEST: PASSED")
    print("="*60)
    return True


def test_error_scenarios():
    """Test various error scenarios"""
    print("\n" + "="*60)
    print("ERROR SCENARIO TESTS")
    print("="*60)

    tests_passed = 0
    tests_total = 0

    # Test 1: Missing image_url column
    print("\n[Test 1] CSV missing 'image_url' column")
    tests_total += 1
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("id,url,species\n1,http://example.com/img1.jpg,Bird\n")
        csv_path = f.name
    try:
        data = pd.read_csv(csv_path)
        urls = data['image_url']
        print("   [FAIL] Should have raised KeyError")
    except KeyError:
        print("   [PASS] Correctly detected missing column")
        tests_passed += 1
    os.unlink(csv_path)

    # Test 2: Empty CSV
    print("\n[Test 2] Empty CSV (headers only)")
    tests_total += 1
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("id,image_url\n")
        csv_path = f.name
    data = pd.read_csv(csv_path)
    urls = data['image_url']
    if urls.empty:
        print("   [PASS] Correctly identified empty CSV")
        tests_passed += 1
    else:
        print("   [FAIL] Should be empty")
    os.unlink(csv_path)

    # Test 3: NaN URLs
    print("\n[Test 3] CSV with NaN/empty URLs")
    tests_total += 1
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("id,image_url\n1,http://example.com/img1.jpg\n2,\n3,http://example.com/img3.jpg\n")
        csv_path = f.name
    data = pd.read_csv(csv_path)
    urls = data['image_url']
    nan_count = urls.isna().sum()
    if nan_count == 1:
        print(f"   [PASS] Detected {nan_count} NaN URL (app would crash trying to download)")
        tests_passed += 1
    else:
        print(f"   [FAIL] Expected 1 NaN, got {nan_count}")
    os.unlink(csv_path)

    # Test 4: Malformed CSV
    print("\n[Test 4] Malformed CSV")
    tests_total += 1
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write("this is not a csv\njust random text\n")
        csv_path = f.name
    try:
        data = pd.read_csv(csv_path)
        if 'image_url' not in data.columns:
            print("   [PASS] Malformed CSV doesn't have image_url column")
            tests_passed += 1
        else:
            print("   [FAIL] Unexpected column found")
    except Exception as e:
        print(f"   [PASS] Error parsing malformed CSV: {type(e).__name__}")
        tests_passed += 1
    os.unlink(csv_path)

    print(f"\n--- Error Tests: {tests_passed}/{tests_total} passed ---")
    return tests_passed == tests_total


if __name__ == "__main__":
    success1 = test_full_workflow()
    success2 = test_error_scenarios()

    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    if success1 and success2:
        print("All integration tests PASSED")
    else:
        print("Some tests FAILED")
