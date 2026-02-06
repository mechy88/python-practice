# SGX Derivatives Data Downloader

**Author:** Miguel Andre R. Pajarillo  
**Date:** February 2026

A command-line tool to download derivative data files from the Singapore Exchange (SGX) website.

## Overview

This tool automates the daily download of the following files from [SGX Derivatives](https://www.sgx.com/research-education/derivatives):

| File | Description |
|------|-------------|
| `WEBPXTICK_DT-*.zip` | Tick data (Time and Sales) - Daily bid/ask quotes |
| `TickData_structure.dat` | Structure specification for tick data |
| `TC_*.txt` | Trade Cancellation data |
| `TC_structure.dat` | Structure specification for TC data |

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Create a virtual environment** (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

2. **Install dependencies**:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Commands

```bash
# Download today's files
python3 main.py --today

# Download files for a specific date
python3 main.py --date 2026-01-30

# Download files for a date range
python3 main.py --range 2026-01-25 2026-01-30

# Automatically backfill missing files for the last 5 days
python3 main.py --backfill 5
```

### Command Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--today` | `-t` | Download today's files |
| `--date YYYY-MM-DD` | `-d` | Download files for a specific date |
| `--range START END` | `-r` | Download files for a date range |
| `--backfill DAYS` | `-b` | Auto-download missing files for last N days |
| `--config FILE` | `-c` | Use custom configuration file |
| `--output DIR` | `-o` | Output directory for downloads |
| `--retry N` | | Number of retry attempts (default: 3) |
| `--force` | `-f` | Force re-download even if files exist |
| `--dry-run` | | Show what would be downloaded |
| `--verbose` | `-v` | Enable debug output |
| `--quiet` | `-q` | Suppress console output |

### Examples

```bash
# Verbose output for debugging
python3 main.py --today --verbose

# Download to a custom directory
python3 main.py --date 2026-01-30 --output /path/to/data

# Force re-download existing files
python3 main.py --today --force

# Preview what would be downloaded
python3 main.py --range 2026-01-20 2026-01-30 --dry-run

# Use a custom configuration file
python3 main.py --today --config my_config.json
```

## Configuration File

You can use a JSON configuration file for persistent settings:

```json
{
    "output_dir": "data",
    "log_file": "downloader.log",
    "retry_attempts": 3,
    "retry_delay": 5,
    "backfill_days": 5
}
```

Save as `config.json` and use with `--config config.json`.

## Output Structure

Downloaded files are organized by date:

```
data/
├── 2026-01-30/
│   ├── WEBPXTICK_DT-20260130.zip
│   ├── TickData_structure.dat
│   ├── TC_20260130.txt
│   └── TC_structure.dat
├── 2026-01-29/
│   └── ...
└── 2026-01-28/
    └── ...
```

## Logging

The tool implements comprehensive logging:

- **Console (stdout):** INFO level and above - operational messages
- **File (downloader.log):** DEBUG level - detailed troubleshooting info

Log messages include:
- Download progress and status
- File sizes and verification
- Error details with retry information
- Summary statistics

### Sample Log Output

```
10:30:15 [INFO] SGX Derivatives Data Downloader Started
10:30:15 [INFO] Processing date: 2026-01-30
10:30:16 [INFO] Downloaded: WEBPXTICK_DT-20260130.zip (2,456,789 bytes)
10:30:17 [INFO] Downloaded: TickData_structure.dat (1,234 bytes)
10:30:18 [WARNING] File not found (404): TC_20260130.txt
10:30:18 [INFO] Completed 2026-01-30: 3 succeeded, 1 failed
```

## Recovery & Backfill

### Automatic Recovery

The `--backfill` option automatically checks for missing files:

```bash
# Check and download missing files for last 5 business days
python3 main.py --backfill 5
```

### Manual Recovery

To re-download specific dates:

```bash
# Re-download a specific date (even if files exist)
python3 main.py --date 2026-01-25 --force

# Re-download a range of dates
python3 main.py --range 2026-01-20 2026-01-25 --force
```

### Historical Files

The tool can attempt to download historical files beyond what's listed on the SGX website by estimating the correct URL IDs. However, note that:

- SGX only guarantees the last 5 market days on their website
- Older files may or may not be available
- The ID estimation may need adjustment for dates far in the past

## Troubleshooting

### Common Issues

1. **404 Not Found errors**
   - The file may not exist for that date (weekends, holidays)
   - The ID estimation may be off - try adjusting the date

2. **Connection timeouts**
   - Check your internet connection
   - Try increasing `--retry` count

3. **Empty files downloaded**
   - The tool automatically detects and retries empty downloads
   - Check the log file for details

### Debug Mode

Use `--verbose` to see detailed debug information:

```bash
python3 main.py --today --verbose
```

## Design Decisions

1. **ID-based URL Discovery:** SGX uses incremental IDs in their URLs. The scraper estimates IDs based on known reference points and scans nearby IDs to find files.

2. **Organized Output:** Files are stored in date-based folders to prevent overwrites and make it easy to locate specific data.

3. **Comprehensive Logging:** Two-tier logging (console + file) ensures operational visibility while maintaining detailed debug trails.

4. **Graceful Failure Handling:** Network errors trigger retries; 404s are logged but don't halt the process; empty files are detected and re-attempted.

5. **Weekend/Holiday Awareness:** The tool skips weekends by default since SGX doesn't publish data on non-trading days.

## License

This project was created for the DTL Data Team Mini-project assessment.

## Contact

For questions about this implementation:
- Email: careers@dytechlab.com
- Subject: Miguel Andre R. Pajarillo_Data MiniProject_20260207
