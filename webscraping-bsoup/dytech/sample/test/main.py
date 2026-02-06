#!/usr/bin/env python3
"""
SGX Derivatives Data Downloader
Author: Miguel Andre R. Pajarillo
Description: CLI tool to download derivative data files from SGX website.

Usage:
    python main.py --today                    # Download today's files
    python main.py --date 2026-01-30          # Download files for specific date
    python main.py --backfill 5               # Backfill missing files for last N days
    python main.py --config config.json       # Use custom config file
"""

import argparse
import sys
from datetime import datetime, timedelta

from utils import setup_logging, get_logger
from scraper import SGXScraper
from config import load_config, DEFAULT_CONFIG


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download SGX derivative data files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --today                    Download today's files
    %(prog)s --date 2026-01-30          Download files for a specific date
    %(prog)s --backfill 5               Auto-download missing files for last 5 days
    %(prog)s --range 2026-01-25 2026-01-30  Download files for date range
    %(prog)s --config config.json       Use custom configuration file
        """
    )
    
    # Mutually exclusive group for date selection
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument(
        "--today", "-t",
        action="store_true",
        help="Download today's files"
    )
    date_group.add_argument(
        "--date", "-d",
        type=str,
        metavar="YYYY-MM-DD",
        help="Download files for a specific date"
    )
    date_group.add_argument(
        "--backfill", "-b",
        type=int,
        metavar="DAYS",
        help="Automatically download missing files for the last N days"
    )
    date_group.add_argument(
        "--range", "-r",
        nargs=2,
        metavar=("START", "END"),
        help="Download files for a date range (YYYY-MM-DD YYYY-MM-DD)"
    )
    
    # Configuration options
    parser.add_argument(
        "--config", "-c",
        type=str,
        metavar="FILE",
        help="Path to configuration file (JSON format)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        metavar="DIR",
        help="Output directory for downloaded files"
    )
    
    # Operational options
    parser.add_argument(
        "--retry", 
        type=int,
        default=3,
        metavar="N",
        help="Number of retry attempts for failed downloads (default: 3)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force re-download even if files exist"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be downloaded without actually downloading"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output (DEBUG level)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress stdout output (log to file only)"
    )
    
    return parser.parse_args()


def validate_date(date_str: str) -> datetime:
    """Validate and parse a date string."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD.")


def get_dates_to_process(args) -> list:
    """Determine which dates to process based on arguments."""
    dates = []
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if args.today:
        dates = [today]
    elif args.date:
        dates = [validate_date(args.date)]
    elif args.backfill:
        # Generate list of last N days (excluding weekends)
        for i in range(args.backfill):
            d = today - timedelta(days=i)
            # Skip weekends (SGX doesn't publish on weekends)
            if d.weekday() < 5:  # Monday=0, Friday=4
                dates.append(d)
    elif args.range:
        start_date = validate_date(args.range[0])
        end_date = validate_date(args.range[1])
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # Skip weekends
                dates.append(current)
            current += timedelta(days=1)
    else:
        # Default to today if no date option specified
        dates = [today]
    
    return sorted(dates, reverse=True)  # Most recent first


def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Load configuration
    config = DEFAULT_CONFIG.copy()
    if args.config:
        try:
            user_config = load_config(args.config)
            config.update(user_config)
        except Exception as e:
            print(f"Error loading config file: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Override config with command line arguments
    if args.output:
        config["output_dir"] = args.output
    if args.retry:
        config["retry_attempts"] = args.retry
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    quiet = args.quiet
    setup_logging(
        log_file=config.get("log_file", "downloader.log"),
        console_level=log_level,
        quiet=quiet
    )
    
    logger = get_logger(__name__)
    logger.info("=" * 60)
    logger.info("SGX Derivatives Data Downloader Started")
    logger.info("=" * 60)
    
    # Determine dates to process
    try:
        dates = get_dates_to_process(args)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    
    if not dates:
        logger.warning("No dates to process.")
        sys.exit(0)
    
    logger.info(f"Processing {len(dates)} date(s)")
    
    # Initialize scraper
    scraper = SGXScraper(config)
    
    # Process each date
    total_success = 0
    total_failed = 0
    
    for date in dates:
        date_str = date.strftime("%Y-%m-%d")
        logger.info(f"Processing date: {date_str}")
        
        if args.dry_run:
            logger.info(f"[DRY RUN] Would download files for {date_str}")
            continue
        
        success, failed = scraper.download_all_files(
            date=date,
            force=args.force
        )
        total_success += success
        total_failed += failed
    
    # Summary
    logger.info("=" * 60)
    logger.info("Download Summary")
    logger.info(f"  Total successful: {total_success}")
    logger.info(f"  Total failed: {total_failed}")
    logger.info("=" * 60)
    
    if total_failed > 0:
        logger.warning("Some downloads failed. Check logs for details.")
        sys.exit(1)
    
    logger.info("All downloads completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
