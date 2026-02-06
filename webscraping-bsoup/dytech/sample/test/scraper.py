"""
SGX Scraper Module
Handles downloading files from SGX derivatives website.
"""

import os
import re
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, List, Dict

from utils import get_logger


class SGXScraper:
    """
    Scraper for SGX derivative data files.
    
    The SGX website uses an incremental ID system for file URLs:
    https://links.sgx.com/1.0.0/derivatives-historical/{id}/FILENAME
    
    This scraper discovers the correct IDs by scanning the website
    and caches the mappings for efficient retrieval.
    """
    
    BASE_URL = "https://links.sgx.com/1.0.0/derivatives-historical"
    DERIVATIVES_PAGE = "https://www.sgx.com/research-education/derivatives"
    
    # Known file patterns
    FILE_TYPES = {
        "WEBPXTICK_DT": {
            "pattern": r"WEBPXTICK_DT-\d{8}\.zip",
            "name_template": "WEBPXTICK_DT-{date}.zip",
            "description": "Tick data (Time and Sales)"
        },
        "TickData_structure": {
            "pattern": r"TickData_structure\.dat",
            "name_template": "TickData_structure.dat",
            "description": "Tick data structure specification"
        },
        "TC": {
            "pattern": r"TC\.txt",
            "url_filename": "TC.txt",
            "name_template": "TC_{date}.txt",
            "description": "Trade Cancellation data"
        },
        "TC_structure": {
            "pattern": r"TC_structure\.dat",
            "name_template": "TC_structure.dat",
            "description": "Trade Cancellation structure specification"
        }
    }
    
    def __init__(self, config: dict):
        """
        Initialize the scraper.
        
        Args:
            config: Configuration dictionary with settings
        """
        self.config = config
        self.logger = get_logger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36"
        })
        
        # Output directory
        self.output_dir = Path(config.get("output_dir", "data"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Retry settings
        self.retry_attempts = config.get("retry_attempts", 3)
        self.retry_delay = config.get("retry_delay", 5)
        
        # ID cache for URL mapping
        self._id_cache: Dict[str, int] = {}
        
        # Known base IDs (discovered from website analysis)
        # These IDs increment daily, so we use them as reference points
        self._reference_ids = {
            # Reference date and corresponding IDs (approximate)
            "2026-01-30": {
                "WEBPXTICK_DT": 4182,
                "TickData_structure": 4182,
                "TC": 4433,
                "TC_structure": 4433
            }
        }
        
        self.logger.debug("SGXScraper initialized")
        self.logger.debug(f"Output directory: {self.output_dir}")
    
    def _get_date_folder(self, date: datetime) -> Path:
        """Get or create the folder for a specific date."""
        date_str = date.strftime("%Y-%m-%d")
        folder = self.output_dir / date_str
        folder.mkdir(parents=True, exist_ok=True)
        return folder
    
    def _estimate_id_for_date(self, file_type: str, target_date: datetime) -> int:
        """
        Estimate the SGX ID for a given date based on reference points.
        
        SGX uses incrementing IDs for each new file. We estimate the ID
        by calculating the business day offset from a known reference date.
        """
        ref_date_str = "2026-01-30"
        ref_date = datetime.strptime(ref_date_str, "%Y-%m-%d")
        ref_ids = self._reference_ids[ref_date_str]
        
        base_id = ref_ids.get(file_type, 4182)
        
        # Calculate business day difference
        delta_days = (target_date - ref_date).days
        
        # Estimate: roughly 1 ID per business day
        # This is approximate; actual IDs may vary
        estimated_id = base_id + delta_days
        
        self.logger.debug(
            f"Estimated ID for {file_type} on {target_date.strftime('%Y-%m-%d')}: "
            f"{estimated_id} (base: {base_id}, delta: {delta_days})"
        )
        
        return estimated_id
    
    def _scan_for_file(self, file_type: str, date: datetime, 
                       search_range: int = 10) -> Optional[Tuple[int, str]]:
        """
        Scan a range of IDs to find the correct file for a given date.
        
        Args:
            file_type: Type of file to search for
            date: Target date
            search_range: Number of IDs to scan in each direction
            
        Returns:
            Tuple of (id, filename) if found, None otherwise
        """
        date_str = date.strftime("%Y%m%d")
        estimated_id = self._estimate_id_for_date(file_type, date)
        
        file_info = self.FILE_TYPES[file_type]
        
        # Determine the URL filename (what's on the server)
        if "url_filename" in file_info:
            expected_name = file_info["url_filename"]
        elif "{date}" in file_info["name_template"]:
            expected_name = file_info["name_template"].format(date=date_str)
        else:
            expected_name = file_info["name_template"]
        
        self.logger.debug(f"Scanning for {expected_name} around ID {estimated_id}")
        
        # Scan IDs around the estimate
        for offset in range(search_range + 1):
            for id_candidate in [estimated_id + offset, estimated_id - offset]:
                if id_candidate <= 0:
                    continue
                
                url = f"{self.BASE_URL}/{id_candidate}/{expected_name}"
                
                try:
                    response = self.session.head(url, timeout=10, allow_redirects=True)
                    if response.status_code == 200:
                        self.logger.debug(f"Found {expected_name} at ID {id_candidate}")
                        return (id_candidate, expected_name)
                except requests.RequestException:
                    continue
        
        self.logger.debug(f"Could not find {expected_name} in ID range")
        return None
    
    def _download_file(self, url: str, dest_path: Path) -> bool:
        """
        Download a file with retry logic.
        
        Args:
            url: URL to download from
            dest_path: Destination path for the file
            
        Returns:
            True if successful, False otherwise
        """
        for attempt in range(1, self.retry_attempts + 1):
            try:
                self.logger.debug(f"Download attempt {attempt}/{self.retry_attempts}: {url}")
                
                # Don't follow redirects automatically so we can detect error pages
                response = self.session.get(url, timeout=60, stream=True, allow_redirects=False)
                
                # Check if we got redirected to an error page
                if response.status_code in (301, 302, 303, 307, 308):
                    redirect_location = response.headers.get("Location", "")
                    if "error" in redirect_location.lower() or "CustomErrorPage" in redirect_location:
                        self.logger.info(f"File not available (redirected to error page): {url}")
                        return False
                    # Follow the redirect manually if it's not an error
                    response = self.session.get(
                        response.headers["Location"], timeout=60, stream=True
                    )
                
                response.raise_for_status()
                
                # Check content type to ensure we're not downloading an HTML error page
                content_type = response.headers.get("content-type", "")
                if "text/html" in content_type.lower() and not dest_path.suffix == ".html":
                    self.logger.info(f"File not available (got HTML instead): {url}")
                    return False
                
                # Get file size from headers
                total_size = int(response.headers.get("content-length", 0))
                
                # Write to file
                with open(dest_path, "wb") as f:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                
                # Verify file was written
                actual_size = dest_path.stat().st_size
                
                if actual_size == 0:
                    self.logger.warning(f"Downloaded file is empty: {dest_path}")
                    dest_path.unlink()
                    continue
                
                self.logger.info(
                    f"Downloaded: {dest_path.name} ({actual_size:,} bytes)"
                )
                return True
                
            except requests.Timeout:
                self.logger.warning(f"Timeout downloading {url}")
            except requests.HTTPError as e:
                if e.response.status_code == 404:
                    self.logger.warning(f"File not found (404): {url}")
                    return False  # Don't retry 404s
                self.logger.warning(f"HTTP error downloading {url}: {e}")
            except requests.RequestException as e:
                self.logger.warning(f"Network error downloading {url}: {e}")
            except IOError as e:
                self.logger.error(f"IO error saving file: {e}")
            
            if attempt < self.retry_attempts:
                self.logger.debug(f"Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        
        self.logger.error(f"Failed to download after {self.retry_attempts} attempts: {url}")
        return False
    
    def download_file_by_type(self, file_type: str, date: datetime, 
                               force: bool = False) -> bool:
        """
        Download a specific file type for a given date.
        
        Args:
            file_type: One of WEBPXTICK_DT, TickData_structure, TC, TC_structure
            date: Target date
            force: Force re-download even if file exists
            
        Returns:
            True if successful, False otherwise
        """
        date_str = date.strftime("%Y%m%d")
        date_folder = self._get_date_folder(date)
        
        file_info = self.FILE_TYPES[file_type]
        
        # Determine filename
        if "{date}" in file_info["name_template"]:
            filename = file_info["name_template"].format(date=date_str)
        else:
            filename = file_info["name_template"]
        
        dest_path = date_folder / filename
        
        # Check if already exists
        if dest_path.exists() and not force:
            self.logger.info(f"File already exists, skipping: {dest_path}")
            return True
        
        self.logger.info(f"Downloading {file_type}: {filename}")
        
        # Determine the URL filename (may differ from local filename)
        if "url_filename" in file_info:
            url_filename = file_info["url_filename"]
        else:
            url_filename = filename
        
        # Try to find the file
        result = self._scan_for_file(file_type, date)
        
        if result is None:
            # Try direct URL construction as fallback
            estimated_id = self._estimate_id_for_date(file_type, date)
            url = f"{self.BASE_URL}/{estimated_id}/{url_filename}"
            self.logger.debug(f"Trying direct URL: {url}")
        else:
            file_id, found_name = result
            url = f"{self.BASE_URL}/{file_id}/{found_name}"
        
        return self._download_file(url, dest_path)
    
    def download_all_files(self, date: datetime, force: bool = False) -> Tuple[int, int]:
        """
        Download all required files for a given date.
        
        Args:
            date: Target date
            force: Force re-download even if files exist
            
        Returns:
            Tuple of (success_count, failure_count)
        """
        date_str = date.strftime("%Y-%m-%d")
        self.logger.info(f"Downloading all files for {date_str}")
        
        success_count = 0
        failure_count = 0
        
        # Files that are date-specific
        date_specific_files = ["WEBPXTICK_DT", "TC"]
        
        # Structure files (same content, but we still save per-date for completeness)
        structure_files = ["TickData_structure", "TC_structure"]
        
        all_files = date_specific_files + structure_files
        
        for file_type in all_files:
            try:
                if self.download_file_by_type(file_type, date, force):
                    success_count += 1
                else:
                    failure_count += 1
            except Exception as e:
                self.logger.error(f"Error downloading {file_type}: {e}")
                failure_count += 1
        
        self.logger.info(
            f"Completed {date_str}: {success_count} succeeded, {failure_count} failed"
        )
        
        return success_count, failure_count
    
    def check_missing_files(self, days: int = 5) -> List[Tuple[datetime, str]]:
        """
        Check for missing files in the last N days.
        
        Args:
            days: Number of days to check
            
        Returns:
            List of (date, file_type) tuples for missing files
        """
        missing = []
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for i in range(days):
            date = today - timedelta(days=i)
            
            # Skip weekends
            if date.weekday() >= 5:
                continue
            
            date_str = date.strftime("%Y%m%d")
            date_folder = self._get_date_folder(date)
            
            for file_type, file_info in self.FILE_TYPES.items():
                if "{date}" in file_info["name_template"]:
                    filename = file_info["name_template"].format(date=date_str)
                else:
                    filename = file_info["name_template"]
                
                file_path = date_folder / filename
                
                if not file_path.exists():
                    missing.append((date, file_type))
                    self.logger.debug(f"Missing: {file_path}")
        
        return missing
    
    def backfill_missing(self, days: int = 5) -> Tuple[int, int]:
        """
        Automatically download missing files for the last N days.
        
        Args:
            days: Number of days to check and backfill
            
        Returns:
            Tuple of (success_count, failure_count)
        """
        self.logger.info(f"Starting backfill for last {days} days")
        
        missing = self.check_missing_files(days)
        
        if not missing:
            self.logger.info("No missing files found")
            return 0, 0
        
        self.logger.info(f"Found {len(missing)} missing files")
        
        success_count = 0
        failure_count = 0
        
        for date, file_type in missing:
            try:
                if self.download_file_by_type(file_type, date):
                    success_count += 1
                else:
                    failure_count += 1
            except Exception as e:
                self.logger.error(f"Error during backfill: {e}")
                failure_count += 1
        
        self.logger.info(
            f"Backfill complete: {success_count} recovered, {failure_count} failed"
        )
        
        return success_count, failure_count
