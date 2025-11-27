"""
Configuration module for Web Crawler Application.
Contains all application constants, timeouts, and settings.
"""

import os

# Application Information
APP_NAME = "Multitool - Websites & Search"
APP_VERSION = "2.0.0"

# File and Path Constants
MAX_EXCEL_CELL_LENGTH = 32767
RESOURCES_DIR = os.path.join(os.path.dirname(__file__), 'resources')
DARK_THEME_PATH = os.path.join(RESOURCES_DIR, 'dark_theme.qss')
LOGO_PATH = os.path.join(RESOURCES_DIR, 'nestle_logo.png')

# HTTP Request Configuration
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

# Timeout Settings (in seconds)
TIMEOUT_STANDARD = 30  # Standard requests (most pages)
TIMEOUT_HEAVY = 40     # Heavy pages or slow servers
TIMEOUT_SHORT = 15     # Quick checks (HEAD requests)

# Concurrency Settings
MAX_CONCURRENCY = 10      # Default concurrent requests
MAX_CONCURRENCY_META = 8  # Meta checker concurrency
MAX_CONCURRENCY_PRODUCT = 8  # Product sheet checker concurrency

# SSL Configuration
# Note: ssl=False is maintained for backward compatibility per user request
# To enable SSL verification, set SSL_VERIFY = True and remove ssl=False from worker files
SSL_VERIFY = False  # Set to True to enable SSL certificate verification

# Image Processing
SUPPORTED_IMAGE_FORMATS = ('.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp', '.avif')
DEFAULT_IMAGE_QUALITY = 85
DEFAULT_IMAGE_FORMAT = 'jpg'

# UI Configuration
DEFAULT_WINDOW_WIDTH = 1000
DEFAULT_WINDOW_HEIGHT = 800


def load_stylesheet() -> str:
    """
    Load the dark theme stylesheet from resources.
    
    Returns:
        str: The QSS stylesheet content, or empty string if file not found
    """
    try:
        with open(DARK_THEME_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Dark theme stylesheet not found at {DARK_THEME_PATH}")
        return ""
    except Exception as e:
        print(f"Error loading stylesheet: {e}")
        return ""


def get_logo_path() -> str:
    """
    Get the path to the logo file if it exists.
    
    Returns:
        str: Path to logo file, or empty string if not found
    """
    if os.path.exists(LOGO_PATH):
        return LOGO_PATH
    # Try alternate location (same directory as original 10.py)
    alt_logo = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'nestle_logo.png')
    if os.path.exists(alt_logo):
        return alt_logo
    return ""
