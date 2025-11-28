"""
Content Extractor GUI Tab.

Allows users to extract structured content from a URL and save it as a Word document.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit,
    QLabel, QTextEdit, QFileDialog, QMessageBox
)

from workers.content_extractor_worker import ContentExtractorWorker


class ContentExtractorGUI(QWidget):
    """GUI for the Content Extractor tool."""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        # URL Input
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/article")
        url_layout.addWidget(self.url_input)
        layout.addLayout(url_layout)

        # Output Folder
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Folder:"))
        self.output_folder = QLineEdit()
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_output_folder)
        output_layout.addWidget(self.output_folder)
        output_layout.addWidget(self.browse_btn)
        layout.addLayout(output_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("Extract to Word")
        self.start_btn.clicked.connect(self.start_extraction)
        button_layout.addWidget(self.start_btn)
        layout.addLayout(button_layout)

        # Log Output
        layout.addWidget(QLabel("Log:"))
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        self.setLayout(layout)

    def browse_output_folder(self):
        """Open folder selection dialog."""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder.setText(folder)

    def start_extraction(self):
        """Start the extraction process."""
        url = self.url_input.text().strip()
        output_folder = self.output_folder.text().strip()

        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a URL.")
            return

        if not output_folder:
            QMessageBox.warning(self, "Input Error", "Please select an output folder.")
            return

        self.log_output.clear()
        self.log_output.append(f"Starting extraction for: {url}")
        self.start_btn.setEnabled(False)

        # Create and start worker
        self.worker = ContentExtractorWorker(url, output_folder)
        self.worker.log_update.connect(self.log_output.append)
        self.worker.finished.connect(self.extraction_finished)
        self.worker.error.connect(self.extraction_error)
        self.worker.start()

    def extraction_finished(self, filepath):
        """Handle successful extraction."""
        self.log_output.append(f"\n✓ Extraction complete")
        self.log_output.append(f"File: {filepath}")
        QMessageBox.information(
            self,
            "Extraction Complete",
            f"Document saved successfully:\n{filepath}"
        )
        self.start_btn.setEnabled(True)

    def extraction_error(self, error_msg):
        """Handle extraction error."""
        self.log_output.append(f"\n✗ Error: {error_msg}")
        QMessageBox.critical(
            self,
            "Extraction Failed",
            f"An error occurred:\n{error_msg}"
        )
        self.start_btn.setEnabled(True)
