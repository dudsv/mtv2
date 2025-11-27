"""
Main application window and container GUIs.

Contains:
- CrawlerMainGUI: Container for all crawler sub-tabs
- MainApp: Main application window with all tool tabs
"""

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTabWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from gui.crawler_gui import CrawlerGUI
from gui.sitemap_extractor_gui import SitemapExtractorGUI
from gui.broken_link_inspector_gui import BrokenLinkInspectorGUI
from gui.meta_product_checker_guis import MetaCheckerGUI
from gui.image_tool_guis import ImageDownloaderGUI, ImageCompressorGUI, ImageResizerGUI
from gui.chatbot_tab import ChatbotTab
from gui.misc_tabs import AboutTab
import config


class CrawlerMainGUI(QWidget):
    """Container for all Crawler sub-tabs."""
    
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        title = QLabel("Crawler")
        title.setObjectName("Title")
        layout.addWidget(title)

        self.subtabs = QTabWidget()
        layout.addWidget(self.subtabs)

        # Original tab
        self.webcrawler_tab = CrawlerGUI()
        self.subtabs.addTab(self.webcrawler_tab, "Web Crawler")

        # New tabs
        self.sitemap_tab = SitemapExtractorGUI()
        self.subtabs.addTab(self.sitemap_tab, "Sitemap")

        # Broken Links tab
        self.broken_tab = BrokenLinkInspectorGUI()
        self.subtabs.addTab(self.broken_tab, "Broken Links")

        # Meta Checker tab
        self.meta_tab = MetaCheckerGUI()
        self.subtabs.addTab(self.meta_tab, "Meta Checker")

        # Note: ProductSheetCheckerGUI would be added here if extracted
        # self.product_tab = ProductSheetCheckerGUI()
        # self.subtabs.addTab(self.product_tab, "Product Sheet")


class MainApp(QWidget):
    """Main application window that integrates all tools into a tabbed interface."""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("MainApp")  # Important for styling
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        # Logo (if available)
        logo_label = QLabel()
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Try to find logo in resources folder
            logo_path = os.pathjoin(config.RESOURCES_DIR, 'nestle_logo.png')
            if not os.path.exists(logo_path):
                # Fallback to script directory
                logo_path = os.path.join(script_dir, 'nestle_logo.png')
            
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    logo_label.setPixmap(pixmap.scaled(200, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    layout.addWidget(logo_label)
        except Exception:
            pass  # Logo is optional

        # Main tabs
        self.tabs = QTabWidget()
        self.crawler_tab = CrawlerMainGUI()
        self.downloader_tab = ImageDownloaderGUI()
        self.compressor_tab = ImageCompressorGUI()
        self.resizer_tab = ImageResizerGUI()
        self.chatbot_tab = ChatbotTab()
        self.about_tab = AboutTab()

        self.tabs.addTab(self.crawler_tab, "Crawler")
        self.tabs.addTab(self.downloader_tab, "Image Downloader")
        self.tabs.addTab(self.compressor_tab, "Image Compressor")
        self.tabs.addTab(self.resizer_tab, "Image Resizer")
        self.tabs.addTab(self.chatbot_tab, "Assistant")
        self.tabs.addTab(self.about_tab, "About")

        layout.addWidget(self.tabs)
        self.setLayout(layout)
        self.setWindowTitle("Multitool - Websites & Search")
        self.resize(1000, 800)
        
        # Load stylesheet
        stylesheet = config.load_stylesheet()
        if stylesheet:
            self.setStyleSheet(stylesheet)

    def closeEvent(self, event):
        """Ensure all threads are stopped when closing the application."""
        # Get the crawler thread
        crawler_thread = None
        if isinstance(self.crawler_tab, CrawlerMainGUI):
            crawler_thread = self.crawler_tab.webcrawler_tab.crawler_thread
        else:
            crawler_thread = getattr(self.crawler_tab, "crawler_thread", None)

        threads_to_stop = [
            crawler_thread,
            getattr(self.downloader_tab.all_images_tab, "downloader_thread", None),
            getattr(self.downloader_tab.excel_tab, "image_thread", None),
            getattr(self.downloader_tab.url_tab, "image_thread", None),
            getattr(self.compressor_tab, "image_thread", None),
            getattr(self.chatbot_tab, "downloader_thread", None),
        ]

        for thread in threads_to_stop:
            if thread and thread.isRunning():
                thread.stop()
                thread.wait()

        event.accept()
