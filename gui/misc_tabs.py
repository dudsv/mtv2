"""
Miscellaneous GUI tabs - About and Assistant tabs.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class AboutTab(QWidget):
    """A simple tab to display information about the application."""
    
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        title_label = QLabel("About Multitool - Websites & Search")
        font = title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)
        layout.addWidget(title_label)

        # Use QLabel with rich text for simple formatting
        info_text = """
        <p><b>Version:</b> 2</p>
        <p><b>Release Date:</b> November 25, 2025</p>
        <hr>
        <h3>Creators</h3>
        <p>
            <b>Developed and idealized by:</b><br>
            Eduardo Vetromille (Carlos.Brito@br.nestle.com)<br><br>
            <b>In collaboration with:</b><br>
            Aislan Pavanello (Aislan.Pavanello@br.nestle.com)<br>
            Felipe Martins (Felipe.Martins2@br.nestle.com)
            Tomás Mera (Tomas.Mera@py.nestle.com)
            Guillermo Caceres (Guillermo.Caceres@py.nestle.com)
            Lorena Fernandez (Lorena.Fernandez@py.nestle.com)
        </p>
        <hr>
        <h3>Project Description</h3>
        <p>
            This multi-functional tool is designed to automate and simplify routine web and image-related tasks. It combines four powerful utilities into a single, user-friendly interface:
        </p>
        <p>
            -<b>Web Crawler:</b> Automatically extracts information from web pages, such as text, titles, and other data, saving everything into organized spreadsheets.
            <br>
            - <b>Image Downloader:</b> Downloads images in bulk, whether from an entire webpage, a list of links in an Excel file, or direct URLs.
            <br>
            - <b>Image Compressor:</b> Optimizes images by reducing their file size, ideal for speeding up website load times without significant quality loss.
            <br>
            - <b>Image Resizer:</b> Changes the dimensions of images, either individually or in batches, to fit new requirements while maintaining the correct aspect ratio.
        </p>
        <hr>
        <p><i>Multitool - Websites & Search - Automation tool for marketing and content tasks.</i></p>
        """

        info_label = QLabel(info_text)
        info_label.setWordWrap(True)
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setAlignment(Qt.AlignmentFlag.AlignTop)

        layout.addWidget(info_label)
        self.setLayout(layout)
