"""
Image downloader, compressor, and resizer GUI components.

Contains all GUI tabs related to image tools:
- AllImagesDownloaderGUI
- ExcelDownloaderGUI
- URLDownloaderGUI
- ImageDownloaderGUI (container)
- ImageCompressorGUI
- ImageResizerGUI
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLineEdit,
    QLabel, QProgressBar, QFileDialog, QMessageBox, QTabWidget, QRadioButton,
    QCheckBox, QComboBox, QSpinBox, QGroupBox, QLayout
)
from PyQt6.QtCore import Qt
from aiohttp import BasicAuth
from PIL import Image

from workers.image_downloader_worker import AllImagesDownloaderThread, ImageProcessorThread
from gui.base_components import BaseDownloaderGUI


class AllImagesDownloaderGUI(QWidget):
    """GUI for the 'Download All Images' feature."""
    
    def __init__(self):
        super().__init__()
        self.downloader_thread = None
        self.output_folder = ""
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)

        # URL input
        layout.addWidget(QLabel("Enter URLs (one per line):"))
        self.url_input = QTextEdit()
        self.url_input.setPlaceholderText("https://example.com/page1\nhttps://example.com/page2")
        layout.addWidget(self.url_input)

        # Output folder
        folder_layout = QHBoxLayout()
        self.folder_line = QLineEdit()
        browse_folder_btn = QPushButton("Browse")
        browse_folder_btn.clicked.connect(self.select_output_folder)
        folder_layout.addWidget(QLabel("Output Folder:"))
        folder_layout.addWidget(self.folder_line)
        folder_layout.addWidget(browse_folder_btn)
        layout.addLayout(folder_layout)

        # Compression options
        compress_group = QGroupBox("Compression Settings (optional)")
        compress_layout = QVBoxLayout()
        
        self.compress_checkbox = QCheckBox("Compress downloaded images")
        compress_layout.addWidget(self.compress_checkbox)
        
        format_layout = QHBoxLayout()
        self.format_combo = QComboBox()
        self.format_combo.addItems(["jpg", "png", "webp", "gif", "avif"])
        self.quality_spin = QSpinBox(minimum=1, maximum=100, value=85)
        format_layout.addWidget(QLabel("Format:"))
        format_layout.addWidget(self.format_combo)
        format_layout.addWidget(QLabel("Quality:"))
        format_layout.addWidget(self.quality_spin)
        compress_layout.addLayout(format_layout)
        compress_group.setLayout(compress_layout)
        layout.addWidget(compress_group)

        # Progress
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # Log
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        layout.addWidget(self.log_output)

        # Buttons
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("Start Download")
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.open_folder_btn = QPushButton("Open Output Folder")
        self.open_folder_btn.setEnabled(False)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.open_folder_btn)
        layout.addLayout(button_layout)

        # Connections
        self.start_btn.clicked.connect(self.start_download)
        self.stop_btn.clicked.connect(self.stop_download)
        self.open_folder_btn.clicked.connect(self.open_output_folder)

    def select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder = folder
            self.folder_line.setText(folder)

    def open_output_folder(self):
        if self.output_folder and os.path.exists(self.output_folder):
            os.startfile(self.output_folder)

    def start_download(self):
        urls = [u.strip() for u in self.url_input.toPlainText().strip().splitlines() if u.strip()]
        if not urls:
            QMessageBox.warning(self, "Input Error", "Please enter at least one URL.")
            return

        if not self.output_folder:
            QMessageBox.warning(self, "Output Error", "Please select an output folder.")
            return

        self.log_output.clear()
        self.progress.setValue(0)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.open_folder_btn.setEnabled(False)

        compress_options = {
            'enabled': self.compress_checkbox.isChecked(),
            'format': self.format_combo.currentText(),
            'quality': self.quality_spin.value()
        }

        self.downloader_thread = AllImagesDownloaderThread(
            urls=urls,
            save_folder=self.output_folder,
            auth=None,
            compress_options=compress_options
        )
        self.downloader_thread.progress.connect(self.update_progress)
        self.downloader_thread.log.connect(self.log_output.append)
        self.downloader_thread.finished.connect(self.on_finished)
        self.downloader_thread.start()

    def stop_download(self):
        if self.downloader_thread and self.downloader_thread.isRunning():
            self.downloader_thread.stop()
            self.stop_btn.setEnabled(False)

    def update_progress(self, value, text):
        self.progress.setValue(value)

    def on_finished(self, status):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.open_folder_btn.setEnabled(True)
        QMessageBox.information(self, "Download Complete", f"Status: {status}")


class ExcelDownloaderGUI(BaseDownloaderGUI):
    """Image downloader from Excel file."""
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        self.excel_path = QLineEdit()
        excel_btn = QPushButton("Browse")
        excel_btn.clicked.connect(lambda: self.browse_file(self.excel_path, "Excel Files (*.xlsx *.xls)"))
        
        excel_layout = QHBoxLayout()
        excel_layout.addWidget(QLabel("Excel File:"))
        excel_layout.addWidget(self.excel_path)
        excel_layout.addWidget(excel_btn)
        layout.addLayout(excel_layout)

        for widget in self.create_common_widgets():
            if isinstance(widget, QLayout):
                layout.addLayout(widget)
            else:
                layout.addWidget(widget)

        self.process_button.clicked.connect(self.start_processing)
        self.stop_button.clicked.connect(self.stop_processing)

    def start_processing(self):
        if not self.excel_path.text() or not self.output_folder.text():
            QMessageBox.warning(self, "Input Error", "Please select an Excel file and an output folder.")
            return
        self.common_start_logic("excel")

    def common_start_logic(self, mode, urls=None):
        self.status_label.setText("Status: Processing...")
        self.process_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar_download.setValue(0)
        self.progress_bar_compress.setValue(0)

        self.image_thread = ImageProcessorThread(
            mode=mode, excel_path=self.excel_path.text(), urls=urls,
            source_folder="", output_folder=self.output_folder.text(),
            image_format=self.format_combo.currentText(), quality=self.quality_spin.value()
        )
        self.image_thread.download_progress.connect(self.progress_bar_download.setValue)
        self.image_thread.compress_progress.connect(self.progress_bar_compress.setValue)
        self.image_thread.status_update.connect(lambda msg: self.status_label.setText(f"Status: {msg}"))
        self.image_thread.finished_processing.connect(self.processing_finished)
        self.image_thread.start()


class URLDownloaderGUI(BaseDownloaderGUI):
    """Image downloader from URL list."""
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        self.url_text = QTextEdit(placeholderText="Enter one image URL per line")
        layout.addWidget(QLabel("Image URLs:"))
        layout.addWidget(self.url_text)

        for widget in self.create_common_widgets():
            if isinstance(widget, QLayout):
                layout.addLayout(widget)
            else:
                layout.addWidget(widget)
            
        self.process_button.clicked.connect(self.start_processing)
        self.stop_button.clicked.connect(self.stop_processing)
    
    def start_processing(self):
        urls = [u.strip() for u in self.url_text.toPlainText().strip().splitlines() if u.strip()]
        if not urls or not self.output_folder.text():
            QMessageBox.warning(self, "Input Error", "Please enter at least one URL and select an output folder.")
            return
        self.common_start_logic("url", urls=urls)
        
    def common_start_logic(self, mode, urls=None):
        self.status_label.setText("Status: Processing...")
        self.process_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar_download.setValue(0)
        self.progress_bar_compress.setValue(0)

        self.image_thread = ImageProcessorThread(
            mode=mode, excel_path="", urls=urls,
            source_folder="", output_folder=self.output_folder.text(),
            image_format=self.format_combo.currentText(), quality=self.quality_spin.value()
        )
        self.image_thread.download_progress.connect(self.progress_bar_download.setValue)
        self.image_thread.compress_progress.connect(self.progress_bar_compress.setValue)
        self.image_thread.status_update.connect(lambda msg: self.status_label.setText(f"Status: {msg}"))
        self.image_thread.finished_processing.connect(self.processing_finished)
        self.image_thread.start()


class ImageDownloaderGUI(QWidget):
    """Main tab for all image downloading functionalities."""
    
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        
        self.all_images_tab = AllImagesDownloaderGUI()
        self.excel_tab = ExcelDownloaderGUI()
        self.url_tab = URLDownloaderGUI()

        self.tabs.addTab(self.all_images_tab, "Download All Images from Page")
        self.tabs.addTab(self.excel_tab, "Download from Excel")
        self.tabs.addTab(self.url_tab, "Download from URL List")
        
        layout.addWidget(self.tabs)


class ImageCompressorGUI(BaseDownloaderGUI):
    """Simplified GUI for compressing local images only."""
    
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        
        self.source_folder = QLineEdit()
        source_btn = QPushButton("Browse")
        source_btn.clicked.connect(lambda: self.browse_folder(self.source_folder))
        
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Source Folder (Images):"))
        source_layout.addWidget(self.source_folder)
        source_layout.addWidget(source_btn)
        layout.addLayout(source_layout)

        for widget in self.create_common_widgets():
            if isinstance(widget, QLayout):
                layout.addLayout(widget)
            else:
                layout.addWidget(widget)
            
        self.process_button.clicked.connect(self.start_processing)
        self.stop_button.clicked.connect(self.stop_processing)

    def start_processing(self):
        if not self.source_folder.text() or not self.output_folder.text():
            QMessageBox.warning(self, "Input Error", "Please select source and output folders.")
            return

        self.status_label.setText("Status: Compressing...")
        self.process_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar_compress.setValue(0)

        self.image_thread = ImageProcessorThread(
            mode="local", excel_path="", urls=None,
            source_folder=self.source_folder.text(),
            output_folder=self.output_folder.text(),
            image_format=self.format_combo.currentText(),
            quality=self.quality_spin.value()
        )
        self.image_thread.compress_progress.connect(self.progress_bar_compress.setValue)
        self.image_thread.status_update.connect(lambda msg: self.status_label.setText(f"Status: {msg}"))
        self.image_thread.finished_processing.connect(self.processing_finished)
        self.image_thread.start()


class ImageResizerGUI(QWidget):
    """GUI for the Image Resizer tool."""
    
    def __init__(self):
        super().__init__()
        self.preset_ratios = {
            "1:1 (Square)": 1.0,
            "4:3 (Standard)": 3.0 / 4.0,
            "16:9 (Widescreen)": 9.0 / 16.0,
            "3:2 (Photo)": 2.0 / 3.0,
            "Original Ratio": None,
            "Free (no constraint)": None,
        }
        self.current_aspect_ratio = None
        self._is_updating_dimensions = False
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Mode selection
        mode_layout = QHBoxLayout()
        self.mode_folder_radio = QRadioButton("Folder Mode (batch)")
        self.mode_single_radio = QRadioButton("Single File Mode")
        self.mode_folder_radio.setChecked(True)
        mode_layout.addWidget(self.mode_folder_radio)
        mode_layout.addWidget(self.mode_single_radio)
        layout.addLayout(mode_layout)

        self.mode_folder_radio.toggled.connect(self.toggle_mode_widgets)

        # Folder mode widgets
        self.folder_widgets = QWidget()
        folder_layout = QVBoxLayout(self.folder_widgets)
        
        self.input_folder = QLineEdit()
        browse_input_folder_btn = QPushButton("Browse")
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Input Folder:"))
        input_layout.addWidget(self.input_folder)
        input_layout.addWidget(browse_input_folder_btn)
        folder_layout.addLayout(input_layout)

        self.output_folder = QLineEdit()
        browse_output_folder_btn = QPushButton("Browse")
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output Folder:"))
        output_layout.addWidget(self.output_folder)
        output_layout.addWidget(browse_output_folder_btn)
        folder_layout.addLayout(output_layout)
        layout.addWidget(self.folder_widgets)

        # Single file mode widgets
        self.single_file_widgets = QWidget()
        single_layout = QVBoxLayout(self.single_file_widgets)
        
        self.input_file = QLineEdit()
        browse_input_file_btn = QPushButton("Browse")
        input_file_layout = QHBoxLayout()
        input_file_layout.addWidget(QLabel("Input File:"))
        input_file_layout.addWidget(self.input_file)
        input_file_layout.addWidget(browse_input_file_btn)
        single_layout.addLayout(input_file_layout)

        self.output_file = QLineEdit()
        browse_output_file_btn = QPushButton("Browse")
        output_file_layout = QHBoxLayout()
        output_file_layout.addWidget(QLabel("Output File:"))
        output_file_layout.addWidget(self.output_file)
        output_file_layout.addWidget(browse_output_file_btn)
        single_layout.addLayout(output_file_layout)
        layout.addWidget(self.single_file_widgets)

        # Ratio mode
        ratio_layout = QHBoxLayout()
        ratio_layout.addWidget(QLabel("Ratio Mode:"))
        self.ratio_mode_combo = QComboBox()
        self.ratio_mode_combo.addItems(self.preset_ratios.keys())
        ratio_layout.addWidget(self.ratio_mode_combo)
        layout.addLayout(ratio_layout)

        # Dimensions
        dim_layout = QHBoxLayout()
        self.width_spinbox = QSpinBox(minimum=1, maximum=10000, value=512)
        self.height_spinbox = QSpinBox(minimum=1, maximum=10000, value=512)
        dim_layout.addWidget(QLabel("Width:"))
        dim_layout.addWidget(self.width_spinbox)
        dim_layout.addWidget(QLabel("Height:"))
        dim_layout.addWidget(self.height_spinbox)
        layout.addLayout(dim_layout)

        # Progress
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # Process button
        process_btn = QPushButton("Process Images")
        layout.addWidget(process_btn)

        # Connections
        browse_input_folder_btn.clicked.connect(self.select_input_folder)
        browse_output_folder_btn.clicked.connect(lambda: self.browse_folder(self.output_folder))
        browse_input_file_btn.clicked.connect(self.select_input_file)
        browse_output_file_btn.clicked.connect(self.select_output_file)
        self.ratio_mode_combo.currentTextChanged.connect(self.mode_changed)
        self.width_spinbox.valueChanged.connect(self.width_changed)
        self.height_spinbox.valueChanged.connect(self.height_changed)
        process_btn.clicked.connect(self.process)

        self.setLayout(layout)
        self.toggle_mode_widgets()

    def _create_h_layout(self, widgets):
        h_layout = QHBoxLayout()
        for w in widgets:
            h_layout.addWidget(w)
        return h_layout

    def toggle_mode_widgets(self):
        is_folder_mode = self.mode_folder_radio.isChecked()
        self.folder_widgets.setVisible(is_folder_mode)
        self.single_file_widgets.setVisible(not is_folder_mode)
        self.mode_changed()

    def select_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder:
            self.input_folder.setText(folder)
            self._update_ratio_from_folder(folder)

    def select_input_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if file:
            self.input_file.setText(file)
            self._update_ratio_from_file(file)

    def select_output_file(self):
        file, _ = QFileDialog.getSaveFileName(self, "Save Image As...", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if file:
            self.output_file.setText(file)

    def browse_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            line_edit.setText(folder)

    def _update_ratio_from_folder(self, folder_path):
        supported = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')
        try:
            for file_name in os.listdir(folder_path):
                if file_name.lower().endswith(supported):
                    self._update_ratio_from_file(os.path.join(folder_path, file_name))
                    return
        except Exception:
            self.current_aspect_ratio = None
            
    def _update_ratio_from_file(self, file_path):
        try:
            with Image.open(file_path) as img:
                w, h = img.size
                self.current_aspect_ratio = h / w if w > 0 else None
        except Exception:
            self.current_aspect_ratio = None
        self.mode_changed()

    def _get_active_ratio(self):
        mode = self.ratio_mode_combo.currentText()
        if mode == "Original Ratio":
            return self.current_aspect_ratio
        return self.preset_ratios.get(mode)

    def mode_changed(self):
        self._is_updating_dimensions = True
        is_free_mode = self.ratio_mode_combo.currentText() == "Free (no constraint)"
        self.height_spinbox.setEnabled(is_free_mode)
        if not is_free_mode:
            self.width_changed(self.width_spinbox.value())
        self._is_updating_dimensions = False

    def width_changed(self, new_width):
        ratio = self._get_active_ratio()
        if ratio is not None and not self._is_updating_dimensions:
            self._is_updating_dimensions = True
            self.height_spinbox.setValue(int(new_width * ratio))
            self._is_updating_dimensions = False

    def height_changed(self, new_height):
        pass
    
    def process(self):
        if self.mode_folder_radio.isChecked():
            self.process_folder()
        else:
            self.process_single_file()

    def _resize_image(self, img_path, output_path):
        target_width = self.width_spinbox.value()
        target_height = self.height_spinbox.value()
        
        with Image.open(img_path) as img:
            ratio = self._get_active_ratio()
            if ratio is not None:
                target_height = int(target_width * ratio)

            new_size = (target_width, target_height)
            
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
            resized_img.save(output_path)

    def process_folder(self):
        input_path = self.input_folder.text()
        output_path = self.output_folder.text()
        if not os.path.isdir(input_path) or not os.path.isdir(output_path):
            QMessageBox.warning(self, "Error", "Both input and output folders must be valid.")
            return

        supported = ('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp')
        files = [f for f in os.listdir(input_path) if f.lower().endswith(supported)]
        if not files:
            QMessageBox.information(self, "Info", "No supported images found in the input folder.")
            return

        self.progress.setValue(0)
        total = len(files)
        for i, filename in enumerate(files, 1):
            try:
                self._resize_image(os.path.join(input_path, filename), os.path.join(output_path, filename))
            except Exception as e:
                print(f"Error processing {filename}: {e}")
            self.progress.setValue(int(i / total * 100))
        
        QMessageBox.information(self, "Completed", "All images have been resized successfully.")

    def process_single_file(self):
        input_path = self.input_file.text()
        output_path = self.output_file.text()
        if not os.path.isfile(input_path) or not output_path:
            QMessageBox.warning(self, "Error", "Input and output file paths must be valid.")
            return
            
        try:
            self.progress.setValue(0)
            self._resize_image(input_path, output_path)
            self.progress.setValue(100)
            QMessageBox.information(self, "Completed", "Image resized successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while resizing:\n{e}")
