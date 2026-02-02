import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import requests
import os
import re
import threading
import time
import shutil

# Configuration
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Global state for download control
download_cancelled = False
download_in_progress = False


def get_file_extension(content_type, url):
    """Determine file extension from content-type header or URL."""
    # Map common content types to extensions
    content_type_map = {
        'image/jpeg': '.jpg',
        'image/jpg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/webp': '.webp',
        'image/bmp': '.bmp',
        'image/tiff': '.tiff',
        'image/svg+xml': '.svg',
    }

    if content_type:
        # Extract main type (ignore parameters like charset)
        main_type = content_type.split(';')[0].strip().lower()
        if main_type in content_type_map:
            return content_type_map[main_type]

    # Fallback: try to extract from URL
    url_lower = url.lower()
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.svg']:
        if ext in url_lower:
            return '.jpg' if ext == '.jpeg' else ext

    # Default to .jpg
    return '.jpg'


def check_disk_space(path, required_bytes=100_000_000):
    """Check if there's enough disk space (default: 100MB minimum)."""
    try:
        usage = shutil.disk_usage(path)
        return usage.free >= required_bytes
    except Exception:
        return True  # If we can't check, proceed anyway


def download_with_retry(url, timeout=REQUEST_TIMEOUT, max_retries=MAX_RETRIES):
    """Download URL with retry logic and proper error handling."""
    last_exception = None

    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()  # Raises exception for 4xx/5xx status codes
            return response
        except requests.exceptions.Timeout:
            last_exception = f"Timeout after {timeout}s"
        except requests.exceptions.HTTPError as e:
            # Don't retry on client errors (4xx)
            if response.status_code < 500:
                raise
            last_exception = f"HTTP {response.status_code}"
        except requests.exceptions.RequestException as e:
            last_exception = str(e)

        if attempt < max_retries - 1:
            time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff

    raise requests.exceptions.RequestException(f"Failed after {max_retries} attempts: {last_exception}")


# Function to browse for CSV file
def browse_csv():
    filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if filename:
        csv_file_path.set(filename)


# Function to browse for download directory
def browse_directory():
    directory = filedialog.askdirectory()
    if directory:
        download_dir.set(directory)


def update_gui_safe(widget, property_name, value):
    """Thread-safe GUI update using root.after()."""
    def update():
        if property_name == 'text':
            widget['text'] = value
        elif property_name == 'value':
            widget['value'] = value
        elif property_name == 'state':
            widget['state'] = value
    root.after(0, update)


def show_message_safe(msg_type, title, message):
    """Thread-safe message box display."""
    def show():
        if msg_type == 'error':
            messagebox.showerror(title, message)
        elif msg_type == 'info':
            messagebox.showinfo(title, message)
        elif msg_type == 'warning':
            messagebox.showwarning(title, message)
    root.after(0, show)


def cancel_download():
    """Cancel the current download."""
    global download_cancelled
    download_cancelled = True
    update_gui_safe(cancel_button, 'state', 'disabled')
    update_gui_safe(status_label, 'text', "Cancelling...")


def reset_ui():
    """Reset UI to initial state."""
    def reset():
        global download_in_progress
        download_in_progress = False
        progress_bar['value'] = 0
        progress_label['text'] = ""
        remaining_time_label['text'] = ""
        mean_speed_label['text'] = ""
        status_label['text'] = ""
        download_button['state'] = 'normal'
        cancel_button['state'] = 'disabled'
    root.after(0, reset)


# Function to download images from CSV
def download_images():
    global download_cancelled, download_in_progress

    # Prevent multiple simultaneous downloads
    if download_in_progress:
        messagebox.showwarning("Warning", "A download is already in progress.")
        return

    csv_path = csv_file_path.get()
    download_path = download_dir.get()

    if not csv_path or not download_path:
        messagebox.showerror("Error", "Please load a CSV file and select a download directory.")
        return

    # Check if download directory exists
    if not os.path.isdir(download_path):
        messagebox.showerror("Error", f"Download directory does not exist: {download_path}")
        return

    # Check disk space
    if not check_disk_space(download_path):
        messagebox.showerror("Error", "Not enough disk space. Please free up at least 100MB.")
        return

    # Read the CSV file
    try:
        data = pd.read_csv(csv_path)
        # Support multiple common column names
        url_column = None
        for col_name in ['image_url', 'IMAGE_URL', 'Image_URL', 'url', 'URL']:
            if col_name in data.columns:
                url_column = col_name
                break

        if url_column is None:
            messagebox.showerror("Error", "CSV must have an 'image_url' column.")
            return

        urls = data[url_column]
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read the CSV file: {e}")
        return

    # Filter out NaN/empty URLs
    valid_urls = [(i, url) for i, url in enumerate(urls) if pd.notna(url) and str(url).strip()]
    skipped_count = len(urls) - len(valid_urls)

    if not valid_urls:
        messagebox.showerror("Error", "No valid URLs found in the CSV file.")
        return

    if skipped_count > 0:
        result = messagebox.askyesno(
            "Warning",
            f"Found {skipped_count} empty/invalid URLs that will be skipped.\n"
            f"Continue with {len(valid_urls)} valid URLs?"
        )
        if not result:
            return

    # Get the starting number for images
    existing_images = os.listdir(download_path)
    max_num = 0
    for img in existing_images:
        match = re.search(r'image_(\d+)\.\w+', img)  # Match any extension
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
    starting_num = max_num + 1

    # Reset cancel flag and set download state
    download_cancelled = False
    download_in_progress = True

    # Update UI
    download_button['state'] = 'disabled'
    cancel_button['state'] = 'normal'
    progress_bar['maximum'] = len(valid_urls)
    progress_label['text'] = f"Downloading 0/{len(valid_urls)} images..."
    remaining_time_label['text'] = "Remaining time: estimating..."
    mean_speed_label['text'] = "Mean speed: 0 Mbit/s"
    status_label['text'] = ""

    def download():
        global download_cancelled, download_in_progress

        total_size = 0
        total_time = 0
        start_time = time.time()
        successful = 0
        failed = 0
        failed_urls = []

        for idx, (original_idx, url) in enumerate(valid_urls):
            # Check for cancellation
            if download_cancelled:
                update_gui_safe(status_label, 'text', f"Cancelled. Downloaded {successful} images.")
                break

            img_num = starting_num + idx

            try:
                download_start_time = time.time()

                # Download with retry and timeout
                response = download_with_retry(url)
                img_data = response.content

                elapsed_time = time.time() - download_start_time

                # Validate content (basic check)
                if len(img_data) < 100:
                    raise ValueError("Downloaded content too small, likely an error page")

                # Update total size and time for mean speed calculation
                total_size += len(img_data)
                total_time += elapsed_time

                # Calculate mean speed in Mbit/s
                mean_speed = (total_size * 8) / (total_time * 1_000_000) if total_time > 0 else 0
                update_gui_safe(mean_speed_label, 'text', f"Mean speed: {mean_speed:.2f} Mbit/s")

                # Determine file extension from content-type
                content_type = response.headers.get('Content-Type', '')
                extension = get_file_extension(content_type, url)

                img_name = f"image_{img_num}{extension}"
                with open(os.path.join(download_path, img_name), 'wb') as handler:
                    handler.write(img_data)

                successful += 1

            except Exception as e:
                failed += 1
                failed_urls.append((url, str(e)))
                # Log error but continue with other downloads
                update_gui_safe(status_label, 'text', f"Failed: {os.path.basename(url)[:30]}...")

            # Update progress (thread-safe)
            progress = idx + 1
            update_gui_safe(progress_bar, 'value', progress)
            update_gui_safe(progress_label, 'text', f"Downloading {progress}/{len(valid_urls)} images...")

            # Estimate remaining time
            current_time = time.time()
            elapsed_total_time = current_time - start_time
            if progress > 0:
                avg_time_per_image = elapsed_total_time / progress
                remaining = len(valid_urls) - progress
                remaining_time = avg_time_per_image * remaining
                if remaining_time >= 60:
                    remaining_str = f"{remaining_time/60:.1f}m"
                else:
                    remaining_str = f"{remaining_time:.0f}s"
                update_gui_safe(remaining_time_label, 'text', f"Remaining time: {remaining_str}")

        # Download complete - show summary
        if download_cancelled:
            summary = f"Download cancelled.\n\nDownloaded: {successful}\nFailed: {failed}\nRemaining: {len(valid_urls) - successful - failed}"
        else:
            summary = f"Download complete!\n\nSuccessful: {successful}\nFailed: {failed}"
            if failed > 0:
                summary += f"\n\nFailed URLs logged. First failure:\n{failed_urls[0][0][:50]}...\nReason: {failed_urls[0][1]}"

        show_message_safe('info', "Download Summary", summary)
        reset_ui()

    # Run the download function in a separate thread
    threading.Thread(target=download, daemon=True).start()


# Create the main window
root = tk.Tk()
root.title("iNaturalist Image Downloader")
root.resizable(False, False)

csv_file_path = tk.StringVar()
download_dir = tk.StringVar()

# CSV File selection
tk.Label(root, text="CSV File:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
tk.Entry(root, textvariable=csv_file_path, width=50).grid(row=0, column=1, padx=10, pady=10)
tk.Button(root, text="Browse", command=browse_csv).grid(row=0, column=2, padx=10, pady=10)

# Download Directory selection
tk.Label(root, text="Download Directory:").grid(row=1, column=0, padx=10, pady=10, sticky='e')
tk.Entry(root, textvariable=download_dir, width=50).grid(row=1, column=1, padx=10, pady=10)
tk.Button(root, text="Browse", command=browse_directory).grid(row=1, column=2, padx=10, pady=10)

# Buttons frame
button_frame = tk.Frame(root)
button_frame.grid(row=2, column=0, columnspan=3, pady=20)

download_button = tk.Button(button_frame, text="Download Images", command=download_images, width=15)
download_button.pack(side=tk.LEFT, padx=10)

cancel_button = tk.Button(button_frame, text="Cancel", command=cancel_download, width=15, state='disabled')
cancel_button.pack(side=tk.LEFT, padx=10)

# Progress Bar and Labels
progress_label = tk.Label(root, text="")
progress_label.grid(row=3, column=0, columnspan=3, pady=5)

progress_bar = ttk.Progressbar(root, orient='horizontal', length=400, mode='determinate')
progress_bar.grid(row=4, column=0, columnspan=3, pady=5)

remaining_time_label = tk.Label(root, text="")
remaining_time_label.grid(row=5, column=0, columnspan=3, pady=5)

mean_speed_label = tk.Label(root, text="")
mean_speed_label.grid(row=6, column=0, columnspan=3, pady=5)

status_label = tk.Label(root, text="", fg="gray")
status_label.grid(row=7, column=0, columnspan=3, pady=5)

root.mainloop()
