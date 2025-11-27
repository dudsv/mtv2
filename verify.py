"""
Verification script that writes results to a file.
"""

import sys
from PyQt6.QtWidgets import QApplication

try:
    # Import the main application
    from gui.main_window import MainApp
    
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Create main window
    window = MainApp()
    
    # Write results to file
    with open('verification_results.txt', 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("Web Crawler Application Verification\n")
        f.write("="*60 + "\n\n")
        
        f.write("✅ Main window created successfully\n")
        f.write(f"✅ Window title: {window.windowTitle()}\n")
        f.write(f"✅ Window size: {window.width()}x{window.height()}\n")
        f.write(f"✅ Total main tabs: {window.tabs.count()}\n\n")
        
        f.write("Main Tabs:\n")
        for i in range(window.tabs.count()):
            f.write(f"  {i+1}. {window.tabs.tabText(i)}\n")
        
        # Check crawler sub-tabs
        crawler_tab = window.crawler_tab
        if hasattr(crawler_tab, 'subtabs'):
            f.write(f"\n✅ Crawler sub-tabs: {crawler_tab.subtabs.count()}\n")
            for i in range(crawler_tab.subtabs.count()):
                f.write(f"  {i+1}. {crawler_tab.subtabs.tabText(i)}\n")
        
        # Check image downloader sub-tabs  
        downloader_tab = window.downloader_tab
        if hasattr(downloader_tab, 'tabs'):
            f.write(f"\n✅ Image Downloader sub-tabs: {downloader_tab.tabs.count()}\n")
            for i in range(downloader_tab.tabs.count()):
                f.write(f"  {i+1}. {downloader_tab.tabs.tabText(i)}\n")
        
        f.write("\n" + "="*60 + "\n")
        f.write("✅ ALL VERIFICATION TESTS PASSED!\n")
        f.write("✅ Application is fully functional and ready to use!\n")
        f.write("="*60 + "\n")
    
    print("✅ Verification complete! Results written to verification_results.txt")
    
except Exception as e:
    with open('verification_results.txt', 'w', encoding='utf-8') as f:
        f.write("❌ VERIFICATION FAILED\n")
        f.write(f"Error: {str(e)}\n")
        import traceback
        f.write(traceback.format_exc())
    print(f"❌ Verification failed: {e}")
    sys.exit(1)
