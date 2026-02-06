"""
Configuration handling for SGX Downloader.
Supports JSON configuration files for flexible customization.
"""

import json
from pathlib import Path
from typing import Any, Dict


# Default configuration values
DEFAULT_CONFIG: Dict[str, Any] = {
    # Output settings
    "output_dir": "data",
    "log_file": "downloader.log",
    
    # Download settings
    "retry_attempts": 3,
    "retry_delay": 5,  # seconds
    "timeout": 60,  # seconds
    
    # Backfill settings
    "backfill_days": 5,
    "auto_backfill": False,
    
    # SGX URL settings (for advanced users)
    "sgx_base_url": "https://links.sgx.com/1.0.0/derivatives-historical",
    "sgx_page_url": "https://www.sgx.com/research-education/derivatives",
    
    # File patterns
    "file_types": {
        "WEBPXTICK_DT": {
            "enabled": True,
            "description": "Tick data (Time and Sales)"
        },
        "TickData_structure": {
            "enabled": True,
            "description": "Tick data structure specification"
        },
        "TC": {
            "enabled": True,
            "description": "Trade Cancellation data"
        },
        "TC_structure": {
            "enabled": True,
            "description": "Trade Cancellation structure specification"
        }
    }
}


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    return config


def save_config(config: Dict[str, Any], config_path: str) -> None:
    """
    Save configuration to a JSON file.
    
    Args:
        config: Configuration dictionary
        config_path: Path to save the configuration
    """
    path = Path(config_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)


def merge_config(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries.
    
    The override values take precedence over base values.
    Nested dictionaries are merged recursively.
    
    Args:
        base: Base configuration
        override: Override configuration
        
    Returns:
        Merged configuration
    """
    result = base.copy()
    
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    
    return result


def generate_sample_config(output_path: str = "config.sample.json") -> None:
    """
    Generate a sample configuration file with all options documented.
    
    Args:
        output_path: Path to save the sample configuration
    """
    sample_config = {
        "_comment": "SGX Downloader Configuration File",
        "_note": "Copy this file to config.json and customize as needed",
        **DEFAULT_CONFIG
    }
    
    save_config(sample_config, output_path)
    print(f"Sample configuration saved to: {output_path}")
