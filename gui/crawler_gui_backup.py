"""
Crawler-related GUI tabs and components.

Contains all GUI tabs related to web crawling functionality including:
- CrawlerGUI: Main web crawler interface
- CrawlerMainGUI: Container for all crawler sub-tabs (to be imported from other modules)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QRadioButton,
    QLineEdit, QLabel, QProgressBar, QFileDialog, QCheckBox, QMessageBox,
    QGroupBox
)

# Import workers
from workers.crawler_worker import CrawlerThread


class CrawlerGUI(QWidget):
    """GUI for the Web Crawler tool."""
    
    def __init__(self):
        super().__init__()
        self.crawler_thread = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # --- UI Widgets ---
        self.output_folder = QLineEdit()
        browse_output_btn = QPushButton("Browse")
        self.mode1 = QRadioButton("Search for modules (by CSS class)")
        self.mode2 = QRadioButton("Search for specific words")
        self.search_input = QLineEdit()
        self.url_input = QTextEdit()
        self.extract_options = {
            "title": QCheckBox("Extract Title"),
            "meta_title": QCheckBox("Extract Meta Title"),
            "meta_description": QCheckBox("Extract Meta Description"),
            "content": QCheckBox("Extract Content (Under Dev as .docx)"),
            "meta_tags": QCheckBox("Extract Meta Tags"),
        }
        self.check_errors = QCheckBox("Log 403 and 404 Errors")
        self.progress = QProgressBar()
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.start_button = QPushButton("Start Crawling")
        self.stop_button = QPushButton("Stop Crawling")
        self.stop_button.setEnabled(False)

        # --- Layout ---
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Folder:"))
        output_layout.addWidget(self.output_folder)
        output_layout.addWidget(browse_output_btn)
        
        mode_group = QGroupBox("Search Mode")
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(self.mode1)
        mode_layout.addWidget(self.mode2)
        mode_group.setLayout(mode_layout)

        extract_group = QGroupBox("Extract Options")
        extract_layout = QVBoxLayout()
        for option in self.extract_options.values():
            extract_layout.addWidget(option)
        extract_group.setLayout(extract_layout)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)

        layout.addLayout(output_layout)
        layout.addWidget(mode_group)
        self.search_input.setPlaceholderText("Enter search terms separated by commas")
        layout.addWidget(self.search_input)
        self.url_input.setPlaceholderText("Enter one URL or sitemap.xml per line")
        layout.addWidget(self.url_input)
        layout.addWidget(extract_group)
        layout.addWidget(self.check_errors)
        layout.addWidget(self.progress)
        layout.addWidget(self.log_output)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

        # --- Connections ---
        browse_output_btn.clicked.connect(self.browse_output_folder)
        self.start_button.clicked.connect(self.start_crawling)
        self.stop_button.clicked.connect(self.stop_crawling)

    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder.setText(folder)

    def start_crawling(self):
        urls = [url.strip() for url in self.url_input.toPlainText().strip().splitlines() if url.strip()]
        if not urls:
            QMessageBox.warning(self, "Input Error", "Please enter at least one URL.")
            return

        output_folder = self.output_folder.text()
        if not output_folder:
            QMessageBox.warning(self, "Input Error", "Please select an output folder.")
            return

        mode = 1 if self.mode1.isChecked() else 2 if self.mode2.isChecked() else 0
        search_input = self.search_input.text().strip()
        if mode in [1, 2] and not search_input:
            QMessageBox.warning(self, "Input Error", "Search mode is selected, but no search terms were provided.")
            return

        self.log_output.clear()
        self.progress.setValue(0)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        extract_opts = {key: option.isChecked() for key, option in self.extract_options.items()}

        self.crawler_thread = CrawlerThread(
            mode=mode,
            search_input=search_input,
            urls=urls,
            extract_options=extract_opts,
            check_errors=self.check_errors.isChecked(),
            output_folder=output_folder
        )
        self.crawler_thread.progress_update.connect(self.progress.setValue)
        self.crawler_thread.log_update.connect(self.log_output.append)
        self.crawler_thread.finished.connect(self.crawl_finished)
        self.crawler_thread.start()

    def stop_crawling(self):
        if self.crawler_thread and self.crawler_thread.isRunning():
            self.crawler_thread.stop()
            self.stop_button.setEnabled(False)

    def crawl_finished(self, output_folder):
        self.log_output.append(f"Process finished. Results are in: {output_folder}")
        QMessageBox.information(self, "Crawling Completed", f"Crawling finished.\\nResults saved in: {output_folder}")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
