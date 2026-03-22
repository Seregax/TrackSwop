from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QComboBox,
    QPushButton,
    QLabel,
    QGroupBox,
    QSplitter,
)

from src.common.logger import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Main application window"""

    source_service_changed = Signal(str)
    destination_service_changed = Signal(str)
    transfer_requested = Signal(object, object)  # source_playlist, dest_playlist

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TrackSwop")
        self.setMinimumSize(1000, 700)
        self._setup_ui()

    def _setup_ui(self):
        """Setup the main window UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header = QLabel("TrackSwop")
        header.setFont(QFont("Segoe UI", 18, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, stretch=1)

        # Left panel - Service selection
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(left_panel)

        # Source service
        source_group = self._create_service_group("Источник")
        left_layout.addWidget(source_group)

        # Destination service
        dest_group = self._create_service_group("Назначение")
        left_layout.addWidget(dest_group)

        # Transfer button
        self.transfer_btn = QPushButton("Начать перенос")
        self.transfer_btn.setMinimumHeight(45)
        self.transfer_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.transfer_btn.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1ed760;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.transfer_btn.clicked.connect(self._on_transfer_clicked)
        left_layout.addWidget(self.transfer_btn)
        left_layout.addStretch()

        # Right panel - Placeholder for PlaylistWidget and TransferWidget
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(right_panel)

        # Placeholder for PlaylistWidget
        self.playlist_widget_placeholder = QLabel("PlaylistWidget")
        self.playlist_widget_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.playlist_widget_placeholder.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: #888;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        right_layout.addWidget(self.playlist_widget_placeholder, stretch=1)

        # Placeholder for TransferWidget
        self.transfer_widget_placeholder = QLabel("TransferWidget")
        self.transfer_widget_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.transfer_widget_placeholder.setStyleSheet("""
            QLabel {
                background-color: #2d2d2d;
                color: #888;
                border-radius: 8px;
                padding: 20px;
            }
        """)
        right_layout.addWidget(self.transfer_widget_placeholder, stretch=1)

        splitter.setSizes([400, 600])
        logger.info("MainWindow initialized")

    def _create_service_group(self, title: str) -> QGroupBox:
        """Create service selection group"""
        group = QGroupBox(title)
        layout = QVBoxLayout(group)

        # Service selector
        service_combo = QComboBox()
        service_combo.addItems(["Spotify", "VK Music", "Local"])
        layout.addWidget(service_combo)

        # Auth button
        auth_btn = QPushButton("Авторизоваться")
        layout.addWidget(auth_btn)

        # Auth status
        auth_status = QLabel("Не авторизован")
        auth_status.setStyleSheet("color: red;")
        layout.addWidget(auth_status)

        # Playlist selector (placeholder)
        playlist_label = QLabel("Плейлист:")
        layout.addWidget(playlist_label)

        playlist_combo = QComboBox()
        playlist_combo.addItem("— Выберите плейлист —")
        playlist_combo.setEditable(True)
        layout.addWidget(playlist_combo)

        return group

    def _on_transfer_clicked(self):
        """Handle transfer button click"""
        logger.info("Transfer requested")
        self.transfer_requested.emit(None, None)
