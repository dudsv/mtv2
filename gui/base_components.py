"""
Base GUI components shared across multiple tabs.

This module contains base classes and common widgets used by multiple GUI tabs
to avoid code duplication.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel,
    QProgressBar, QFileDialog, QMessageBox, QComboBox, QSpinBox, QGroupBox
)


class BaseDownloaderGUI(QWidget):
    """Base class for downloader GUIs to avoid code duplication."""
    
    def __init__(self):
        super().__init__()
        self.image_thread = None

    def create_common_widgets(self):
        """
        Create and return common widgets used by image downloader/compressor tabs.
        
        Returns:
            list: List of widgets and layouts to be added to the tab's main layout
        """
        # --- Output and Settings ---
        self.output_folder = QLineEdit()
        output_btn = QPushButton("Browse")
        output_btn.clicked.connect(lambda: self.browse_folder(self.output_folder))
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["jpg", "png", "webp", "gif", "avif"])
        self.quality_spin = QSpinBox(minimum=1, maximum=100, value=85)
        
        format_quality_group = QGroupBox("Format and Compression")
        format_quality_layout = QHBoxLayout(format_quality_group)
        format_quality_layout.addWidget(QLabel("Format:"))
        format_quality_layout.addWidget(self.format_combo)
        format_quality_layout.addSpacing(20)
        format_quality_layout.addWidget(QLabel("Quality:"))
        format_quality_layout.addWidget(self.quality_spin)
        
        self.status_label = QLabel("Status: Ready")
        self.progress_bar_download = QProgressBar()
        self.progress_bar_compress = QProgressBar()
        self.process_button = QPushButton("Start Process")
        self.stop_button = QPushButton("Stop", enabled=False)

        # Layouts
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Folder:"))
        output_layout.addWidget(self.output_folder)
        output_layout.addWidget(output_btn)

        download_layout = QHBoxLayout()
        download_layout.addWidget(QLabel("Downloading:"))
        download_layout.addWidget(self.progress_bar_download)
        
        compress_layout = QHBoxLayout()
        compress_layout.addWidget(QLabel("Compressing:"))
        compress_layout.addWidget(self.progress_bar_compress)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.process_button)
        button_layout.addWidget(self.stop_button)

        return [output_layout, format_quality_group, self.status_label, 
                download_layout, compress_layout, button_layout]
    
    def processing_finished(self, status):
        """
        Handle the completion of image processing.
        
        Args:
            status (str): Status string from the worker thread
        """
        messages = {
            "Completed": ("Success", "Process completed successfully."),
            "Stopped": ("Stopped", "Process was stopped by the user."),
            "Error": ("Error", "An error occurred during processing.")
        }
        title, msg = messages.get(status, ("Info", status))
        QMessageBox.information(self, title, msg)
        self.status_label.setText("Status: Ready")
        self.process_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def browse_file(self, line_edit, file_filter):
        """
        Open a file dialog and set the selected file path to a line edit.
        
        Args:
            line_edit (QLineEdit): Target line edit widget
            file_filter (str): File filter string for the dialog
        """
        file, _ = QFileDialog.getOpenFileName(self, "Select File", "", file_filter)
        if file:
            line_edit.setText(file)

    def browse_folder(self, line_edit):
        """
        Open a folder dialog and set the selected folder path to a line edit.
        
        Args:
            line_edit (QLineEdit): Target line edit widget
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            line_edit.setText(folder)
        
    def stop_processing(self):
        """Stop the currently running image processing thread."""
        if self.image_thread and self.image_thread.isRunning():
            self.image_thread.stop()
            self.stop_button.setEnabled(False)
