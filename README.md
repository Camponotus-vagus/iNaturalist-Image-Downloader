# iNaturalist Image Downloader

[![Build Status](https://github.com/Camponotus-vagus/iNaturalist-Image-Downloader/actions/workflows/build-release.yml/badge.svg)](https://github.com/Camponotus-vagus/iNaturalist-Image-Downloader/actions)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.x](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)

A user-friendly, open-source GUI application for batch downloading images from iNaturalist. Simply export observation URLs to a CSV file from iNaturalist and let this tool handle the rest.

## Features

**Core Functionality:**
- Browse and select a CSV file containing image URLs
- Choose a directory to save downloaded images
- Progressive filename numbering (`image_1.jpg`, `image_2.jpg`, etc.)
- Smart continuation from last existing image in the directory
- Automatic file extension detection based on content type

**User Experience:**
- Real-time progress bar with visual feedback
- Live download speed display (Mbit/s)
- Estimated time remaining (ETA) calculation
- Cancel button to gracefully stop downloads at any time
- Completion summary with success/failure statistics

**Robustness:**
- Automatic retry with exponential backoff (up to 3 attempts)
- 30-second timeout protection to prevent hanging
- HTTP status validation for reliable downloads
- Content validation to detect corrupted responses
- Disk space check before downloading (warns if < 100MB available)
- Graceful handling of empty or invalid URLs

## Quick Start

### Option 1: Download Pre-built Executable (Recommended)

Download the latest release for your platform from the [Releases page](https://github.com/Camponotus-vagus/iNaturalist-Image-Downloader/releases):

| Platform | File |
|----------|------|
| Windows | `inaturalist_downloader.exe` |
| macOS (Apple Silicon) | `inaturalist_downloader-macos-arm64` |
| macOS (Intel) | `inaturalist_downloader-macos-x64` |
| Linux | `inaturalist_downloader-linux` |

Simply download and run - no installation required!

### Option 2: Run from Source

**Requirements:**
- Python 3.x
- tkinter (usually included with Python)
- pandas
- requests

**Installation:**

1. Clone the repository:
   ```bash
   git clone https://github.com/Camponotus-vagus/iNaturalist-Image-Downloader.git
   cd iNaturalist-Image-Downloader
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:

   On Windows:
   ```bash
   venv\Scripts\activate
   ```

   On macOS and Linux:
   ```bash
   source venv/bin/activate
   ```

4. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application:

```bash
python inaturalist_downloader.py
```

**Steps:**

1. Click "Browse" to select a CSV file containing image URLs
2. Click "Browse" to choose a destination folder for the images
3. Click "Download Images" to start the download process
4. Monitor progress via the progress bar and statistics display
5. (Optional) Click "Cancel" at any time to stop - partial downloads are saved

## CSV File Format

The CSV file should contain a column with image URLs. The application supports multiple column name variations:
- `image_url` (recommended)
- `IMAGE_URL`
- `Image_URL`
- `url`
- `URL`

**Example CSV:**
```csv
image_url
https://inaturalist-open-data.s3.amazonaws.com/photos/12345/original.jpg
https://inaturalist-open-data.s3.amazonaws.com/photos/67890/original.jpg
```

### Exporting from iNaturalist

To export image URLs from [iNaturalist](https://www.inaturalist.org/observations/export):

1. Go to the [iNaturalist Observations Export](https://www.inaturalist.org/observations/export) page
2. In Step 1, select the type of observations you want to export (e.g., "Formicidae")
3. In Step 3, de-select all columns except for `image_url`
4. Scroll to the bottom and click "Create Export"
5. Wait for the export to complete and download the CSV file

The downloaded CSV file is ready to use with this application!

## Screenshots

### Initial Screen
<img width="846" alt="Screenshot 2024-05-31 alle 11 12 58" src="https://github.com/Camponotus-vagus/iNaturalist-Image-Downloader/assets/114755488/b69c2fb8-5b69-4173-8de4-e3c55745c9ed">

### Download in Progress
<img width="846" alt="Screenshot 2024-05-31 alle 11 22 20" src="https://github.com/Camponotus-vagus/iNaturalist-Image-Downloader/assets/114755488/cb00a566-c13c-4ecb-b487-746243b20657">

### Download Complete
<img width="730" alt="Screenshot 2024-05-31 alle 11 35 35" src="https://github.com/Camponotus-vagus/iNaturalist-Image-Downloader/assets/114755488/1b7844a0-c81a-4637-9f51-399f6b8b29e8">

### Sample CSV File
<img width="1195" alt="Screenshot 2024-05-30 alle 18 55 36" src="https://github.com/Camponotus-vagus/iNaturalist-Image-Downloader/assets/114755488/6416cecc-b4d2-4348-a4e0-aa46e50da055">

## Configuration

The application uses the following default settings (defined in `inaturalist_downloader.py`):

| Setting | Default | Description |
|---------|---------|-------------|
| `REQUEST_TIMEOUT` | 30 seconds | Maximum time to wait for a server response |
| `MAX_RETRIES` | 3 | Number of retry attempts for failed downloads |
| `RETRY_DELAY` | 2 seconds | Initial delay between retries (doubles each attempt) |

## Development

### Running Tests

The project includes a comprehensive test suite:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run all tests
python tests/run_all_tests.py
```

### Building Executables

To build a standalone executable for your platform:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed inaturalist_downloader.py
```

The executable will be created in the `dist/` directory.

### Project Structure

```
iNaturalist-Image-Downloader/
├── inaturalist_downloader.py  # Main application
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── LICENSE                    # GNU GPLv3 License
├── README.md                  # This file
├── tests/                     # Test suite
│   ├── run_all_tests.py
│   ├── test_downloader.py
│   ├── test_mocked.py
│   ├── test_integration.py
│   └── ...
└── .github/workflows/         # CI/CD pipelines
    └── build-release.yml
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any features, bug fixes, or enhancements.

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run the test suite to ensure everything works
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the GNU GPLv3 License. See the [LICENSE](LICENSE) file for details.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Camponotus-vagus/iNaturalist-Image-Downloader&type=Date)](https://star-history.com/#Camponotus-vagus/iNaturalist-Image-Downloader&Date)
