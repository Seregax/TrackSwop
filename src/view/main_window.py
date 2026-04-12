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
    QProgressBar,
)

from src.common.logger import get_logger
from src.view.playlist_widget import PlaylistWidget
from src.view.transfer_widget import TransferWidget
from src.view.dynamic_form import DynamicForm
from src.view.view_models.main_window_vm import MainWindowViewModel
from src.model.store.token_store import TokenStore
from src.view.view_model import ViewModel
from src.workers.playlists_loading_worker import PlaylistsLoadingWorker
from src.workers.tracks_loading_worker import TracksLoadingWorker

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
        
        # Worker thread management
        self._playlist_loading_worker: Optional[PlaylistsLoadingWorker] = None
        self._tracks_loading_worker: Optional[TracksLoadingWorker] = None
        self._loading_panel: Optional[str] = None  # Track which panel is loading
        self._loading_for_panel: Optional[str] = None  # Track which panel is loading

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
        self.source_loading_indicator = self._create_loading_indicator()
        self.tabs.addTab(self.source_playlist_widget, "Источник")

        # Destination playlist widget
        self.dest_playlist_widget = PlaylistWidget()
        self.dest_playlist_widget.set_view_model(self._main_vm.dest_vm)
        self.dest_loading_indicator = self._create_loading_indicator()
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
    
    @staticmethod
    def _create_loading_indicator() -> QWidget:
        """Create a loading indicator widget with spinner animation"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        
        layout.addStretch()
        
        # Loading icon/label
        loading_label = QLabel("⏳ Загрузка плейлистов...")
        loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        loading_label.setFont(QFont("Segoe UI", 14))
        loading_label.setStyleSheet("color: #1DB954; font-weight: bold;")
        layout.addWidget(loading_label)
        
        # Progress bar
        progress = QProgressBar()
        progress.setRange(0, 0)  # Indeterminate progress
        progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #1DB954;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #1DB954;
            }
        """)
        progress.setMaximumWidth(300)
        
        # Center the progress bar
        progress_layout = QHBoxLayout()
        progress_layout.addStretch()
        progress_layout.addWidget(progress)
        progress_layout.addStretch()
        layout.addLayout(progress_layout)
        
        layout.addStretch()
        
        widget.setStyleSheet("background-color: white;")
        return widget

    def _on_service_selected(self, service: str):
        """Handle service selection - show auth dialog if needed"""
        # Determine which panel
        panel = "source" if self._main_vm.source_vm.selected_service == service else "dest"
        widget = self.source_playlist_widget if panel == "source" else self.dest_playlist_widget
        loading_indicator = self.source_loading_indicator if panel == "source" else self.dest_loading_indicator

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

                # Load playlists in background thread
                authenticated_service = self._main_vm.get_authenticated_service(service)
                if authenticated_service:
                    self._load_playlists_async(authenticated_service, panel, widget, loading_indicator)
                else:
                    QMessageBox.critical(
                        self,
                        "Ошибка",
                        "Не удалось получить аутентифицированный сервис"
                    )
            else:
                QMessageBox.critical(
                    self,
                    "Ошибка аутентификации",
                    "Не удалось авторизоваться. Проверьте данные."
                )
                widget.set_authenticated(False)
    
    def _load_playlists_async(self, service, panel: str, widget, loading_indicator):
        """
        Load playlists asynchronously using a worker thread.
        
        Args:
            service: Authenticated service instance
            panel: Panel identifier ("source" or "dest")
            widget: PlaylistWidget to update
            loading_indicator: Loading indicator widget
        """
        # Stop any existing worker
        if self._playlist_loading_worker:
            self._playlist_loading_worker.quit()
            self._playlist_loading_worker.wait()
        
        # Show loading indicator
        self.tabs.setCurrentWidget(widget)
        self._show_loading_indicator(panel, loading_indicator, widget)
        
        # Create and start worker
        self._playlist_loading_worker = PlaylistsLoadingWorker(service, self)
        self._loading_for_panel = panel
        
        # Connect signals
        self._playlist_loading_worker.finished.connect(
            lambda playlists: self._on_playlists_loaded_async(playlists, panel, widget, loading_indicator)
        )
        self._playlist_loading_worker.error.connect(
            lambda error: self._on_playlists_loading_error(error, panel, widget, loading_indicator)
        )
        
        # Start worker
        self._playlist_loading_worker.start()
    
    def _show_loading_indicator(self, panel: str, loading_indicator: QWidget, widget: PlaylistWidget):
        """Show loading indicator in place of the playlist widget"""
        self._loading_panel = panel
        # Replace widget content temporarily
        parent_layout = widget.parentWidget().layout() if widget.parentWidget() else None
        if parent_layout:
            # We'll overlay the loading indicator by using a stacked widget approach
            # For now, we'll just disable the widget and show a visual indicator
            widget.setEnabled(False)
            widget.setStyleSheet("opacity: 0.5;")
    
    def _on_playlists_loaded_async(self, playlists, panel: str, widget: PlaylistWidget, loading_indicator: QWidget):
        """Handle playlists loaded from worker thread"""
        try:
            # Hide loading indicator
            widget.setEnabled(True)
            widget.setStyleSheet("")
            
            # Load playlists into widget
            widget.load_playlists(playlists)
            
            logger.info(f"Playlists loaded successfully for {panel} panel")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось загрузить плейлисты: {e}"
            )
            widget.setEnabled(True)
            widget.setStyleSheet("")
        finally:
            self._playlist_loading_worker = None
            self._loading_for_panel = None
    
    def _on_playlists_loading_error(self, error: str, panel: str, widget: PlaylistWidget, loading_indicator: QWidget):
        """Handle error during playlist loading"""
        # Hide loading indicator
        widget.setEnabled(True)
        widget.setStyleSheet("")
        
        QMessageBox.critical(
            self,
            "Ошибка загрузки плейлистов",
            error
        )
        
        self._playlist_loading_worker = None
        self._loading_for_panel = None

    def _on_playlist_selected(self, panel: str):
        """Handle playlist selection - load tracks in background"""
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
        
        # Load tracks in background thread
        self._load_tracks_async(service, playlist, panel, widget)

    def _load_tracks_async(self, service, playlist, panel: str, widget: PlaylistWidget):
        """
        Load tracks asynchronously using a worker thread.
        
        Args:
            service: Authenticated service instance
            playlist: Playlist entity
            panel: Panel identifier ("source" or "dest")
            widget: PlaylistWidget to update
        """
        # Stop any existing worker
        if self._tracks_loading_worker:
            self._tracks_loading_worker.quit()
            self._tracks_loading_worker.wait()
        
        # Show loading state in the UI
        widget.tracks_table.setEnabled(False)
        widget.track_count_label.setText("⏳ Загрузка треков...")
        widget.track_count_label.setStyleSheet("color: #1DB954; font-weight: bold;")
        
        # Create and start worker
        self._tracks_loading_worker = TracksLoadingWorker(service, playlist, self)
        
        # Connect signals
        self._tracks_loading_worker.finished.connect(
            lambda tracks: self._on_tracks_loaded_async(tracks, widget)
        )
        self._tracks_loading_worker.error.connect(
            lambda error: self._on_tracks_loading_error(error, widget)
        )
        
        # Start worker
        self._tracks_loading_worker.start()

    def _on_tracks_loaded_async(self, tracks, widget: PlaylistWidget):
        """Handle tracks loaded from worker thread"""
        try:
            # Load tracks into widget
            widget.load_tracks(tracks)
            
            # Restore UI state
            widget.tracks_table.setEnabled(True)
            
            logger.info(f"Tracks loaded successfully")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось загрузить треки: {e}"
            )
            widget.tracks_table.setEnabled(True)
        finally:
            self._tracks_loading_worker = None

    def _on_tracks_loading_error(self, error: str, widget: PlaylistWidget):
        """Handle error during tracks loading"""
        widget.tracks_table.setEnabled(True)
        widget.track_count_label.setText("Ошибка при загрузке треков")
        widget.track_count_label.setStyleSheet("color: red; font-weight: bold;")
        
        QMessageBox.critical(
            self,
            "Ошибка загрузки треков",
            error
        )
        
        self._tracks_loading_worker = None

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
