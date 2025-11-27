"""
Simple extraction assistant script to help identify the remaining GUI classes 
that need to be extracted from 10.py.

This script will help us understand what GUI components remain and their approximate sizes.
"""

import re

# List of GUI classes we're looking for based on the implementation plan
gui_classes_to_find = [
    "SitemapExtractorGUI",
    "BrokenLinkInspectorGUI", 
    "MetaCheckerGUI",
    "ProductSheetCheckerGUI",
    "CrawlerMainGUI",
    "AllImagesDownloaderGUI",
    "ExcelDownloaderGUI",
    "URLDownloaderGUI",
    "ImageDownloaderGUI",
    "ImageCompressorGUI",
    "ImageResizerGUI",
    "ChatbotTab",
    "AboutTab",
    "MainApp"
]

print("GUI Classes to Extract:")
print("=" * 50)
for cls in gui_classes_to_find:
    print(f"- {cls}")

print("\nNext Steps:")
print("=" * 50)
print("1. Extract each GUI class from 10.py")
print("2. Group related classes into logical modules")
print("3. Update imports to use the modular structure")
print("4. Create main window and entry point")
print("5. Test the application")
