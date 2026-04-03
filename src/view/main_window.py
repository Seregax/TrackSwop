from typing import Optional, Dict, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QGroupBox,
    QSplitter,
    QTabWidget,
    QStackedWidget,
    QDialog,
    QMessageBox,
)

from src.common.logger import get_logger
from src.view.playlist_widget import PlaylistWidget
from src.view.transfer_widget import TransferWidget
from src.view.dynamic_form import DynamicForm
from src.view.view_models.main_window_vm import MainWindowViewModel
from src.model.store.token_store import TokenStore
from src.view.view_model import ViewModel

logger = get_logger(__name__)


class AuthDialog(QDialog):
    """Dialog for service authentication using DynamicForm"""

    def __init__(self, service_name: str, fields_spec, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Аутентификация: {service_name}")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        self._auth_data = {}
        self._setup_ui(service_name, fields_spec)

    def _setup_ui(self, service_name: str, fields_spec):
        """Setup dialog UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel(f"Введите данные для {service_name}")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(title)

        # Create ViewModel for form
        form_vm = ViewModel()

        # Create DynamicForm and get the widget
        fields = fields_spec.get_fields()
        self._dynamic_form = DynamicForm(fields, form_vm, self)
        form_widget = self._dynamic_form.create_widget()
        form_widget.setStyleSheet("QGroupBox { border: 1px solid #ccc; border-radius: 5px; margin-top: 10px; }")
        layout.addWidget(form_widget)

        # Connect validation signal
        self._dynamic_form.form_validated.connect(self._on_form_validated)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._ok_btn = QPushButton("Авторизоваться")
        self._ok_btn.setMinimumWidth(150)
        self._ok_btn.setMinimumHeight(40)
        self._ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1ed760;
            }
        """)
        self._ok_btn.clicked.connect(self._on_ok_clicked)
        btn_layout.addWidget(self._ok_btn)

        self._cancel_btn = QPushButton("Отмена")
        self._cancel_btn.setMinimumWidth(120)
        self._cancel_btn.setMinimumHeight(40)
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        layout.addLayout(btn_layout)

    def _on_form_validated(self, is_valid: bool):
        """Handle form validation"""
        if is_valid:
            self.accept()

    def _on_ok_clicked(self):
        """Trigger form validation"""
        self._dynamic_form._on_validate_clicked()

    def get_auth_data(self) -> Dict[str, Any]:
        """Get authentication data from form"""
        return self._dynamic_form.get_values()


class MainWindow(QMainWindow):
    """Main application window"""

    def __init__(self, token_store: Optional[TokenStore] = None):
        super().__init__()
        self.setWindowTitle("TrackSwop")
        self.setMinimumSize(1000, 700)

        self._token_store = token_store
        self._main_vm = MainWindowViewModel(token_store)

        # Set services list in ViewModels
        services = self._main_vm.service_registry.get_available_services()
        self._main_vm.source_vm.services = services
        self._main_vm.dest_vm.services = services

        self._setup_ui()
        self._connect_signals()

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

        # Right panel - PlaylistWidget and TransferWidget
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        splitter.addWidget(right_panel)

        # Stacked widget for switching between playlists and transfer
        self.content_stack = QStackedWidget()

        # Playlist tabs widget
        playlist_tabs_widget = QWidget()
        playlist_tabs_layout = QVBoxLayout(playlist_tabs_widget)
        playlist_tabs_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()

        # Source playlist widget
        self.source_playlist_widget = PlaylistWidget()
        self.source_playlist_widget.set_view_model(self._main_vm.source_vm)
        self.tabs.addTab(self.source_playlist_widget, "Источник")

        # Destination playlist widget
        self.dest_playlist_widget = PlaylistWidget()
        self.dest_playlist_widget.set_view_model(self._main_vm.dest_vm)
        self.tabs.addTab(self.dest_playlist_widget, "Назначение")

        playlist_tabs_layout.addWidget(self.tabs)
        self.content_stack.addWidget(playlist_tabs_widget)

        # Transfer widget
        self.transfer_widget = TransferWidget()
        self.transfer_widget.set_view_model(self._main_vm.transfer_vm)
        self.transfer_widget.back_requested.connect(self._on_back_requested)
        self.content_stack.addWidget(self.transfer_widget)

        right_layout.addWidget(self.content_stack)

        splitter.setSizes([400, 600])
        logger.info("MainWindow initialized")

    def _connect_signals(self):
        """Connect ViewModel signals"""
        # Service selection signals
        self._main_vm.source_vm.service_selected.connect(self._on_service_selected)
        self._main_vm.dest_vm.service_selected.connect(self._on_service_selected)
        
        # Playlist selection signals
        self.source_playlist_widget.playlist_list.itemSelectionChanged.connect(
            lambda: self._on_playlist_selected("source")
        )
        self.dest_playlist_widget.playlist_list.itemSelectionChanged.connect(
            lambda: self._on_playlist_selected("dest")
        )

    @staticmethod
    def _create_service_group(title: str) -> QGroupBox:
        """Create service selection group"""
        group = QGroupBox(title)
        layout = QVBoxLayout(group)

        info_label = QLabel(f"Выберите сервис во вкладке \"{title}\"")
        info_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(info_label)

        return group

    def _on_service_selected(self, service: str):
        """Handle service selection - show auth dialog if needed"""
        # Determine which panel
        panel = "source" if self._main_vm.source_vm.selected_service == service else "dest"
        widget = self.source_playlist_widget if panel == "source" else self.dest_playlist_widget

        # Get service instance to check if auth is needed
        service_instance = self._main_vm.service_registry.get_service(service)
        auth_spec = service_instance.get_auth_specs()

        # Show auth dialog
        dialog = AuthDialog(service, auth_spec, self)

        if dialog.exec() == QDialog.Accepted:
            auth_data = dialog.get_auth_data()

            # Authenticate via MainWindowViewModel
            success = self._main_vm.authenticate_service(service, auth_data)

            if success:
                widget.set_authenticated(True)

                # Load playlists
                authenticated_service = self._main_vm.get_authenticated_service(service)
                if authenticated_service:
                    try:
                        playlists = authenticated_service.get_playlists()
                        widget.load_playlists(playlists)
                    except Exception as e:
                        logger.error(f"Failed to load playlists: {e}")
                        QMessageBox.critical(
                            self,
                            "Ошибка",
                            f"Не удалось загрузить плейлисты: {e}"
                        )
            else:
                QMessageBox.critical(
                    self,
                    "Ошибка аутентификации",
                    "Не удалось авторизоваться. Проверьте данные."
                )
                widget.set_authenticated(False)

    def _on_playlist_selected(self, panel: str):
        """Handle playlist selection - load tracks"""
        widget = self.source_playlist_widget if panel == "source" else self.dest_playlist_widget
        view_model = widget._viewModel
        
        if not view_model or not view_model.current_playlist:
            return
        
        # Get service name
        service_name = view_model.selected_service
        if not service_name:
            return
        
        # Get authenticated service
        service = self._main_vm.get_authenticated_service(service_name)
        if not service:
            return
        
        # Get playlist object
        playlist = view_model.current_playlist_object
        if not playlist:
            return
        
        # Load tracks
        try:
            tracks = service.get_tracks_from_playlist(playlist)
            widget.load_tracks(tracks)
        except Exception as e:
            logger.error(f"Не удалось загрузить треки: {e}")
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось загрузить треки: {e}"
            )

    def _on_transfer_clicked(self):
        """Handle transfer button click"""
        # Check if transfer is possible
        if not self._main_vm.can_transfer():
            QMessageBox.warning(
                self,
                "Невозможно начать перенос",
                "Выберите сервисы и плейлисты для переноса"
            )
            return

        # Start transfer via MainWindowViewModel
        self._main_vm.start_transfer()

        # Switch to transfer view
        self.content_stack.setCurrentIndex(1)

        logger.info("Transfer started")

    def _on_back_requested(self):
        """Handle back request from TransferWidget"""
        self.content_stack.setCurrentIndex(0)
        logger.info("Switched back to playlist view")
