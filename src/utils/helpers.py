"""
Utility helper functions
"""

import re
from typing import List, Dict
from pathlib import Path


def clean_text(text: str) -> str:
    """
    Clean and normalize text

    Args:
        text: Input text

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove special characters (keep alphanumeric, spaces, and basic punctuation)
    text = re.sub(r'[^\w\s.,!?;:()\-\'\"]+', '', text)

    return text.strip()


def extract_year_from_filename(filename: str) -> int:
    """
    Extract year from filename

    Args:
        filename: Filename string

    Returns:
        Year as integer, or 0 if not found
    """
    # Look for 4-digit year pattern
    match = re.search(r'(20\d{2})', filename)
    if match:
        return int(match.group(1))
    return 0


def extract_set_from_filename(filename: str) -> str:
    """
    Extract paper set from filename

    Args:
        filename: Filename string

    Returns:
        Set identifier (e.g., "Set-1")
    """
    # Look for "set" followed by number or letter
    match = re.search(r'set[_\-\s]*([0-9A-Za-z]+)', filename, re.IGNORECASE)
    if match:
        return f"Set-{match.group(1)}"
    return "Unknown"


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable string

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2h 30m")
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def ensure_directory(path: str):
    """
    Ensure directory exists, create if not

    Args:
        path: Directory path
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def get_file_size_mb(filepath: str) -> float:
    """
    Get file size in MB

    Args:
        filepath: Path to file

    Returns:
        File size in MB
    """
    try:
        size_bytes = Path(filepath).stat().st_size
        return size_bytes / (1024 * 1024)
    except:
        return 0.0
