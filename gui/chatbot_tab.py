"""
ChatbotTab - Assistant interface for the web crawler application.

Provides a chat-style interface for users to interact with the application
through natural language commands. Currently supports image downloading from URLs.
"""

import re
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QScrollArea, QFrame, QProgressBar, QFileDialog
)
from PyQt6.QtCore import Qt

from workers.image_downloader_worker import AllImagesDownloaderThread


class ChatbotTab(QWidget):
    """
    Assistant tab with dashboard style:
    - Chat card with message bubbles
    - Status pill at top right
    - Shortcuts as mini-cards
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent
        self.downloader_thread = None
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)

        # ---------- Top: title + status pill on right ----------
        top_layout = QHBoxLayout()
        title = QLabel("Assistant")
        title.setObjectName("Title")
        top_layout.addWidget(title)

        self.top_status_pill = QLabel("Ready")
        self.top_status_pill.setObjectName("chatStatusPill")
        self.top_status_pill.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addStretch()
        top_layout.addWidget(self.top_status_pill)
        main_layout.addLayout(top_layout)

        # ---------- Main chat card ----------
        chat_card = QWidget()
        chat_card.setObjectName("card")
        chat_layout = QVBoxLayout(chat_card)
        chat_layout.setContentsMargins(16, 16, 16, 16)
        chat_layout.setSpacing(8)

        # Message scroll area with vertical layout
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.messages_container)

        chat_layout.addWidget(self.scroll_area)
        main_layout.addWidget(chat_card)

        # ---------- Shortcuts in mini-cards ----------
        shortcuts_card = QWidget()
        shortcuts_card.setObjectName("card")
        shortcuts_layout = QHBoxLayout(shortcuts_card)
        shortcuts_layout.setContentsMargins(16, 10, 16, 10)
        shortcuts_layout.setSpacing(10)

        lbl = QLabel("Sugestões:")
        lbl.setStyleSheet("color: #9CA3AF;")
        shortcuts_layout.addWidget(lbl)

        btn_example = QPushButton("Baixar imagens de URLs")
        btn_example.setProperty("accent", True)
        btn_example.clicked.connect(self.fill_example_download)
        shortcuts_layout.addWidget(btn_example)

        shortcuts_layout.addStretch()
        main_layout.addWidget(shortcuts_card)

        # ---------- Bottom input pill ----------
        input_card = QWidget()
        input_card.setObjectName("card")
        input_layout = QHBoxLayout(input_card)
        input_layout.setContentsMargins(16, 10, 16, 10)
        input_layout.setSpacing(10)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(
            "Ex: Baixe as imagens de https://site1.com, https://site2.com"
        )
        send_button = QPushButton("Enviar")
        send_button.setProperty("accent", True)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(send_button)
        main_layout.addWidget(input_card)

        # ---------- Discreet status / progress ----------
        self.status_label = QLabel("Status: Aguardando comando")
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.progress_bar)

        # Connections
        send_button.clicked.connect(self.handle_user_message)
        self.input_field.returnPressed.connect(self.handle_user_message)

    # ---------- UI helpers ----------

    def fill_example_download(self):
        self.input_field.setText(
            "Baixe as imagens de https://www.exemplo1.com, https://www.exemplo2.com"
        )
        self.input_field.setFocus()

    def _add_bubble(self, text, kind="bot"):
        label = QLabel(text)
        label.setWordWrap(True)
        if kind == "user":
            label.setObjectName("userBubble")
            # Align visually left/right via layout wrapper
            wrapper = QHBoxLayout()
            wrapper.setContentsMargins(0, 0, 0, 0)
            wrapper.addStretch()
            wrapper.addWidget(label)
            cont = QWidget()
            cont.setLayout(wrapper)
            self.messages_layout.addWidget(cont)
        elif kind == "log":
            label.setObjectName("logBubble")
            self.messages_layout.addWidget(label)
        else:
            label.setObjectName("botBubble")
            wrapper = QHBoxLayout()
            wrapper.setContentsMargins(0, 0, 0, 0)
            wrapper.addWidget(label)
            wrapper.addStretch()
            cont = QWidget()
            cont.setLayout(wrapper)
            self.messages_layout.addWidget(cont)

        # Auto-scroll to end
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def append_message(self, sender, text):
        if sender.lower().startswith("você"):
            self._add_bubble(text, "user")
        elif sender.lower().startswith("log"):
            self._add_bubble(text, "log")
        else:
            self._add_bubble(text, "bot")

    # ---------- Command logic ----------

    def handle_user_message(self):
        text = self.input_field.text().strip()
        if not text:
            return
        self.append_message("Você", text)
        self.input_field.clear()
        self.process_command(text)

    def process_command(self, text):
        lower = text.lower()

        if "baixe as imagens" in lower or "baixar as imagens" in lower:
            urls = self._extract_urls(text)
            if not urls:
                self.append_message(
                    "Assistant",
                    "Não encontrei URLs no comando.\n"
                    "Exemplo: Baixe as imagens de https://site1.com, https://site2.com"
                )
                return
            self.start_download_images_from_urls(urls)
            return

        self.append_message(
            "Assistant",
            "Ainda não aprendi esse tipo de comando 😅\n"
            "No momento você pode pedir, por exemplo:\n"
            "Baixe as imagens de https://site1.com, https://site2.com"
        )

    def _extract_urls(self, text):
        pattern = r'https?://[^\s,;"]+' 
        return re.findall(pattern, text)

    def start_download_images_from_urls(self, urls):
        self.append_message(
            "Assistant",
            "Beleza, vou baixar as imagens destas URLs:\n- " + "\n- ".join(urls)
        )

        output_folder = QFileDialog.getExistingDirectory(
            self, "Selecione a pasta para salvar as imagens"
        )
        if not output_folder:
            self.append_message("Assistant", "Operação cancelada: nenhuma pasta selecionada.")
            return

        compress_options = {
            'enabled': False,
            'format': 'jpg',
            'quality': 85
        }

        if self.downloader_thread and self.downloader_thread.isRunning():
            self.downloader_thread.stop()
            self.downloader_thread.wait()

        self.downloader_thread = AllImagesDownloaderThread(
            urls=urls,
            save_folder=output_folder,
            auth=None,
            compress_options=compress_options
        )

        self.downloader_thread.progress.connect(self.update_progress)
        self.downloader_thread.log.connect(lambda msg: self.append_message("Log", msg))
        self.downloader_thread.finished.connect(self.download_finished)

        self.status_label.setText("Status: Baixando imagens...")
        self.top_status_pill.setText("Running")
        self.progress_bar.setValue(0)
        self.downloader_thread.start()

    def update_progress(self, percent, status_text):
        self.progress_bar.setValue(percent)
        self.status_label.setText(f"Status: {status_text}")

    def download_finished(self, status):
        self.append_message("Assistant", f"Tarefa concluída com status: {status}")
        self.status_label.setText(f"Status: {status}")
        self.top_status_pill.setText("Ready")
        self.progress_bar.setValue(100)
