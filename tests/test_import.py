"""
Test if the module can be imported and GUI initialized
"""
import os
import sys

print("Testing module import capabilities...")

# Test 1: Check if tkinter is available
try:
    import tkinter as tk
    print("[PASS] tkinter is available")
    tkinter_available = True
except ImportError as e:
    print(f"[INFO] tkinter not available: {e}")
    tkinter_available = False

# Test 2: Check if required modules are available
modules = ['pandas', 'requests', 'threading', 'time', 're', 'os']
for mod in modules:
    try:
        __import__(mod)
        print(f"[PASS] {mod} is available")
    except ImportError as e:
        print(f"[FAIL] {mod} not available: {e}")

# Test 3: Try to check if display is available (X11)
if tkinter_available:
    try:
        display = os.environ.get('DISPLAY', '')
        if display:
            print(f"[INFO] DISPLAY is set to: {display}")
            # Try to create a root window
            root = tk.Tk()
            root.withdraw()  # Hide it
            print("[PASS] Can create Tk root window")
            root.destroy()
        else:
            print("[INFO] No DISPLAY environment variable - headless mode")
            print("[INFO] Cannot test GUI in headless environment")
    except Exception as e:
        print(f"[INFO] Cannot create Tk window: {e}")

# Test 4: Check if the main script has syntax errors (without running mainloop)
print("\n--- Checking main script syntax ---")
try:
    import ast
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'inaturalist_downloader.py')
    with open(script_path, 'r') as f:
        source = f.read()

    # Parse the AST to check syntax
    tree = ast.parse(source)
    print("[PASS] No syntax errors in inaturalist_downloader.py")

    # Analyze the AST
    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]

    print(f"[INFO] Functions defined: {functions}")
    print(f"[INFO] Classes defined: {classes}")
    print(f"[INFO] Imports: {imports}")

except SyntaxError as e:
    print(f"[FAIL] Syntax error in script: {e}")
except Exception as e:
    print(f"[FAIL] Error analyzing script: {e}")

# Test 5: Check for potential issues in the code
print("\n--- Static Analysis ---")

script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'inaturalist_downloader.py')
with open(script_path, 'r') as f:
    lines = f.readlines()

issues = []

# Check for timeout parameter in requests.get
has_timeout = any('timeout' in line for line in lines)
if not has_timeout:
    issues.append("CRITICAL: No timeout parameter in requests.get() - requests can hang indefinitely")

# Check for status_code check
has_status_check = any('status_code' in line for line in lines)
if not has_status_check:
    issues.append("CRITICAL: No HTTP status code check - error pages saved as images")

# Check for isna/isnull check
has_nan_check = any('isna' in line or 'isnull' in line or 'notna' in line for line in lines)
if not has_nan_check:
    issues.append("BUG: No NaN/null check for URLs - will crash on missing values")

# Check for cancel mechanism
has_cancel = any('cancel' in line.lower() for line in lines)
if not has_cancel:
    issues.append("UX: No cancel button - cannot stop download once started")

# Check for thread safety
has_lock = any('Lock' in line or 'mutex' in line for line in lines)
if not has_lock:
    issues.append("POTENTIAL: No thread lock - race condition if download button clicked multiple times")

# Check for disk space check
has_disk_check = any('disk' in line.lower() or 'shutil.disk_usage' in line for line in lines)
if not has_disk_check:
    issues.append("POTENTIAL: No disk space check before downloading")

# Check for retry logic
has_retry = any('retry' in line.lower() for line in lines)
if not has_retry:
    issues.append("RELIABILITY: No retry logic for failed downloads")

print(f"Found {len(issues)} potential issues:")
for issue in issues:
    print(f"  - {issue}")

print("\n--- Import Test Complete ---")
