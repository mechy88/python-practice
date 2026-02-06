"""
Utility functions for SGX Downloader.
Includes logging configuration and recovery helpers.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# Global logger registry
_loggers = {}


def setup_logging(
    log_file: str = "downloader.log",
    console_level: str = "INFO",
    file_level: str = "DEBUG",
    quiet: bool = False
) -> None:
    """
    Configure logging with both console and file handlers.
    
    The logging configuration follows these rules:
    - Console (stdout): Shows INFO and above by default, configurable
    - File: Always logs DEBUG and above for troubleshooting
    - Quiet mode: Disables console output, logs to file only
    
    Args:
        log_file: Path to the log file
        console_level: Minimum level for console output
        file_level: Minimum level for file output
        quiet: If True, suppress console output
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Clear any existing handlers
    root_logger.handlers = []
    
    # Create formatters
    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S"
    )
    
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler (stdout)
    if not quiet:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, console_level.upper()))
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # File handler
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    file_handler.setLevel(getattr(logging, file_level.upper()))
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Log startup message
    root_logger.debug("-" * 60)
    root_logger.debug(f"Logging initialized at {datetime.now().isoformat()}")
    root_logger.debug(f"Log file: {log_path.absolute()}")


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
    return _loggers[name]


def is_business_day(date: datetime) -> bool:
    """
    Check if a date is a business day (Monday-Friday).
    
    Note: This does not account for SGX holidays.
    For a production system, you would want to maintain
    a holiday calendar.
    
    Args:
        date: Date to check
        
    Returns:
        True if business day, False otherwise
    """
    return date.weekday() < 5


def get_previous_business_day(date: datetime) -> datetime:
    """
    Get the previous business day.
    
    Args:
        date: Starting date
        
    Returns:
        Previous business day
    """
    from datetime import timedelta
    
    current = date - timedelta(days=1)
    while not is_business_day(current):
        current -= timedelta(days=1)
    return current


def format_file_size(size_bytes: int) -> str:
    """
    Format a file size in bytes to a human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def verify_file_integrity(file_path: Path, min_size: int = 1) -> bool:
    """
    Verify that a downloaded file is valid.
    
    Args:
        file_path: Path to the file
        min_size: Minimum acceptable file size in bytes
        
    Returns:
        True if file is valid, False otherwise
    """
    logger = get_logger(__name__)
    
    if not file_path.exists():
        logger.warning(f"File does not exist: {file_path}")
        return False
    
    size = file_path.stat().st_size
    
    if size < min_size:
        logger.warning(
            f"File too small ({format_file_size(size)}): {file_path}"
        )
        return False
    
    logger.debug(f"File verified ({format_file_size(size)}): {file_path}")
    return True


class DownloadStats:
    """Track download statistics for reporting."""
    
    def __init__(self):
        self.started_at = datetime.now()
        self.files_attempted = 0
        self.files_succeeded = 0
        self.files_failed = 0
        self.files_skipped = 0
        self.bytes_downloaded = 0
    
    def record_success(self, size_bytes: int = 0):
        """Record a successful download."""
        self.files_attempted += 1
        self.files_succeeded += 1
        self.bytes_downloaded += size_bytes
    
    def record_failure(self):
        """Record a failed download."""
        self.files_attempted += 1
        self.files_failed += 1
    
    def record_skip(self):
        """Record a skipped file (already exists)."""
        self.files_skipped += 1
    
    def get_summary(self) -> dict:
        """Get a summary of download statistics."""
        elapsed = datetime.now() - self.started_at
        return {
            "duration_seconds": elapsed.total_seconds(),
            "files_attempted": self.files_attempted,
            "files_succeeded": self.files_succeeded,
            "files_failed": self.files_failed,
            "files_skipped": self.files_skipped,
            "bytes_downloaded": self.bytes_downloaded,
            "bytes_formatted": format_file_size(self.bytes_downloaded)
        }
    
    def log_summary(self, logger: Optional[logging.Logger] = None):
        """Log a summary of download statistics."""
        if logger is None:
            logger = get_logger(__name__)
        
        summary = self.get_summary()
        
        logger.info("Download Statistics:")
        logger.info(f"  Duration: {summary['duration_seconds']:.1f} seconds")
        logger.info(f"  Attempted: {summary['files_attempted']}")
        logger.info(f"  Succeeded: {summary['files_succeeded']}")
        logger.info(f"  Failed: {summary['files_failed']}")
        logger.info(f"  Skipped: {summary['files_skipped']}")
        logger.info(f"  Downloaded: {summary['bytes_formatted']}")
