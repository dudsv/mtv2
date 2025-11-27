"""
Utility helper functions for the Web Crawler Application.
Includes filename sanitization, text normalization, and data validation.
"""

import re
import string
import math
from pathlib import Path
from typing import Union


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """
    Sanitize filename by removing invalid characters and path traversal attempts.
    
    Args:
        filename: The filename to sanitize
        max_length: Maximum allowed filename length (default: 255)
        
    Returns:
        A safe filename string, or "unnamed_file" if result is empty
    """
    if not filename:
        return "unnamed_file"
    
    # Remove path separators, null bytes, and other unsafe characters
    # Windows: < > : " / \ | ? *
    # Also remove control characters
    clean = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', filename)
    
    # Remove leading/trailing dots and spaces (Windows restrictions)
    clean = clean.strip('. ')
    
    # Limit length while preserving extension if possible
    if len(clean) > max_length:
        name, ext = Path(clean).stem, Path(clean).suffix
        clean = name[:max_length - len(ext)] + ext
    
    return clean if clean else "unnamed_file"


def norm_num(value: Union[int, float, str, None]) -> str:
    """
    Convert any numeric value (int/float/str) to string without decimal places.
    
    Args:
        value: The value to normalize (can be int, float, str, or None)
        
    Returns:
        String representation of the number, or empty string if invalid/None
    """
    if value is None:
        return ""
    
    # Handle int directly
    if isinstance(value, int):
        return str(value)
    
    # Handle float (including values from Excel)
    if isinstance(value, float):
        # Check for NaN using math.isnan
        if math.isnan(value):
            return ""
        return str(int(round(value)))
    
    # Handle string
    s = str(value).strip()
    
    # Remove .0 suffix if present (e.g., "123.0" -> "123")
    if s.endswith(".0"):
        try:
            # Validate it's actually a number before removing .0
            float(s)
            s = s[:-2]
        except ValueError:
            pass
    
    return s


def norm_text(text: str) -> str:
    """
    Normalize text by collapsing whitespace and stripping.
    
    Args:
        text: The text to normalize
        
    Returns:
        Normalized text with single spaces, or empty string if None/empty
    """
    if not text:
        return ""
    # Replace all whitespace sequences with single space
    normalized = re.sub(r'\s+', ' ', text).strip()
    return normalized


def norm_title(text: str) -> str:
    """
    Normalize title text by collapsing whitespace and removing common suffixes.
    Specifically removes patterns like " | Purina" or " | Purina ES" from the end.
    
    Args:
        text: The title text to normalize
        
    Returns:
        Normalized title text
    """
    if not text:
        return ""
    
    # Collapse whitespace
    normalized = re.sub(r'\s+', ' ', text).strip()
    
    # Remove suffixes like " | Purina" or " | Purina ES" (case-insensitive)
    normalized = re.sub(r'\s*\|\s*purina(?:\s+[A-Z]{2})?$', '', normalized, flags=re.IGNORECASE)
    
    return normalized.strip()


def validate_url(url: str) -> bool:
    """
    Validate if a string is a properly formatted URL.
    
    Args:
        url: The URL string to validate
        
    Returns:
        True if URL appears valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    url = url.strip()
    
    # Basic check for http/https protocol
    if not url.lower().startswith(('http://', 'https://')):
        return False
    
    # Check for at least a domain
    if len(url) < 10:  # Minimum: "http://a.b"
        return False
    
    # Check for common invalid patterns
    if ' ' in url or '\n' in url or '\t' in url:
        return False
    
    return True


def validate_file_path(file_path: str) -> bool:
    """
    Validate if a file path exists and is accessible.
    
    Args:
        file_path: The file path to validate
        
    Returns:
        True if file exists and is accessible, False otherwise
    """
    try:
        path = Path(file_path)
        return path.exists() and path.is_file()
    except (ValueError, OSError):
        return False


def validate_excel_file(file_path: str) -> bool:
    """
    Validate if a file is an Excel file (.xlsx or .xls).
    
    Args:
        file_path: The file path to validate
        
    Returns:
        True if file is a valid Excel file, False otherwise
    """
    if not validate_file_path(file_path):
        return False
    
    path = Path(file_path)
    return path.suffix.lower() in ['.xlsx', '.xls']
