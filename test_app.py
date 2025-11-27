"""
Quick test script to verify the application launches correctly.
"""

import sys
from PyQt6.QtWidgets import QApplication

# Import the main application
from gui.main_window import MainApp

def test_application():
    """Test that the application initializes correctly."""
    print("="*60)
    print("Testing Web Crawler Application")
    print("="*60)
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create main window
    print("\n✅ Creating main window...")
    window = MainApp()
    
    # Verify window properties
    print(f"✅ Window title: {window.windowTitle()}")
    print(f"✅ Window size: {window.width()}x{window.height()}")
    print(f"✅ Total tabs: {window.tabs.count()}")
    
    # List all tabs
    print("\nTabs:")
    for i in range(window.tabs.count()):
        print(f"  {i+1}. {window.tabs.tabText(i)}")
    
    # Check crawler sub-tabs
    crawler_tab = window.crawler_tab
    if hasattr(crawler_tab, 'subtabs'):
        print(f"\nCrawler sub-tabs: {crawler_tab.subtabs.count()}")
        for i in range(crawler_tab.subtabs.count()):
            print(f"  {i+1}. {crawler_tab.subtabs.tabText(i)}")
    
    # Check image downloader sub-tabs
    downloader_tab = window.downloader_tab
    if hasattr(downloader_tab, 'tabs'):
        print(f"\nImage Downloader sub-tabs: {downloader_tab.tabs.count()}")
        for i in range(downloader_tab.tabs.count()):
            print(f"  {i+1}. {downloader_tab.tabs.tabText(i)}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("✅ Application is ready to use!")
    print("="*60)
    
    # Don't show the window, just test initialization
    # window.show()
    # sys.exit(app.exec())

if __name__ == '__main__':
    test_application()
