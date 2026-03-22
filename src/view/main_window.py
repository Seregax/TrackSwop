from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QGroupBox,
    QSplitter,
    QTabWidget,
)

from src.common.logger import get_logger
from src.view.playlist_widget import PlaylistWidget
from src.view.view_models.playlist_vm import PlaylistViewModel

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
        self._source_vm: Optional[PlaylistViewModel] = None
        self._dest_vm: Optional[PlaylistViewModel] = None
        self._setup_ui()

    def _setup_ui(self):
        """Set up the main window UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header = QLabel("TrackSwop")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
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
        self.transfer_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
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

        # Right panel - PlaylistWidget tabs
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(right_panel)

        # Tabs for source and destination playlists
        self.tabs = QTabWidget()

        # Source playlist widget
        self.source_playlist_widget = PlaylistWidget()
        self._source_vm = PlaylistViewModel()
        self.source_playlist_widget.set_view_model(self._source_vm)
        self.tabs.addTab(self.source_playlist_widget, "Источник")

        # Destination playlist widget
        self.dest_playlist_widget = PlaylistWidget()
        self._dest_vm = PlaylistViewModel()
        self.dest_playlist_widget.set_view_model(self._dest_vm)
        self.tabs.addTab(self.dest_playlist_widget, "Назначение")

        right_layout.addWidget(self.tabs)

        splitter.setSizes([400, 600])
        logger.info("MainWindow initialized")

    @staticmethod
    def _create_service_group(title: str) -> QGroupBox:
        """Create service selection group"""
        group = QGroupBox(title)
        layout = QVBoxLayout(group)

        info_label = QLabel(f"Выберите сервис во вкладке \"{title}\"")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(info_label)

        return group

    def _on_transfer_clicked(self):
        """Handle transfer button click"""
        logger.info("Transfer requested")
        self.transfer_requested.emit(None, None)
