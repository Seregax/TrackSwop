from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QListWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QLabel,
    QGroupBox,
)

from src.view.view_models.playlist_vm import PlaylistViewModel


class PlaylistWidget(QWidget):
    """Widget for displaying and managing playlists"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._viewModel: Optional[PlaylistViewModel] = None
        self._setup_ui()

    def _setup_ui(self):
        """Set up the widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Service selector
        service_group = QGroupBox("Сервис")
        service_layout = QHBoxLayout(service_group)

        self.service_combo = QComboBox()
        self.service_combo.currentTextChanged.connect(self._on_service_changed)
        service_layout.addWidget(self.service_combo)

        self.auth_btn = QPushButton("Авторизоваться")
        self.auth_btn.clicked.connect(self._on_auth_clicked)
        service_layout.addWidget(self.auth_btn)

        self.auth_status = QLabel("Не авторизован")
        self.auth_status.setStyleSheet("color: red;")
        service_layout.addWidget(self.auth_status)

        service_layout.addStretch()
        layout.addWidget(service_group)

        # Main content - playlists and tracks
        content_layout = QHBoxLayout()
        content_layout.setSpacing(10)

        # Playlists panel
        playlists_group = QGroupBox("Плейлисты")
        playlists_layout = QVBoxLayout(playlists_group)

        self.playlist_list = QListWidget()
        self.playlist_list.itemSelectionChanged.connect(self._on_playlist_selected)
        playlists_layout.addWidget(self.playlist_list)

        content_layout.addWidget(playlists_group, stretch=1)

        # Tracks panel
        tracks_group = QGroupBox("Треки")
        tracks_layout = QVBoxLayout(tracks_group)

        self.tracks_table = QTableWidget()
        self.tracks_table.setColumnCount(3)
        self.tracks_table.setHorizontalHeaderLabels(["Название", "Исполнитель", "Длительность"])
        self.tracks_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tracks_table.setAlternatingRowColors(True)
        self.tracks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tracks_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tracks_layout.addWidget(self.tracks_table)

        # Track count label
        self.track_count_label = QLabel("Треков: 0")
        tracks_layout.addWidget(self.track_count_label)

        content_layout.addWidget(tracks_group, stretch=2)

        layout.addLayout(content_layout)

    def set_view_model(self, view_model: PlaylistViewModel):
        """Set the ViewModel and connect signals"""
        self._viewModel = view_model

        # Populate service combo
        self.service_combo.clear()
        self.service_combo.addItems(view_model.services)

        # Connect ViewModel signals
        view_model.service_changed.connect(self._on_service_changed_vm)
        view_model.playlists_loaded.connect(self._on_playlists_loaded)
        view_model.playlist_selected.connect(self._on_playlist_selected_vm)
        view_model.tracks_loaded.connect(self._on_tracks_loaded)

        # Set initial state
        self._on_service_changed_vm(view_model.current_service)

    # ViewModel signal handlers

    def _on_service_changed_vm(self, service: str):
        """Handle service change from ViewModel"""
        if service:
            self.auth_status.setText("Авторизован")
            self.auth_status.setStyleSheet("color: green;")

    def _on_playlists_loaded(self):
        """Handle playlists loaded from ViewModel"""
        self.playlist_list.clear()
        self.playlist_list.addItems(self._viewModel.playlists)
        self.track_count_label.setText("Треков: 0")
        self.tracks_table.setRowCount(0)

    def _on_playlist_selected_vm(self, playlist: str):
        """Handle playlist selection from ViewModel"""
        pass  # Tracks will be updated in _on_tracks_loaded

    def _on_tracks_loaded(self):
        """Handle tracks loaded from ViewModel"""
        tracks = self._viewModel.tracks
        self.tracks_table.setRowCount(len(tracks))

        for row, track in enumerate(tracks):
            self.tracks_table.setItem(row, 0, QTableWidgetItem(track["title"]))
            self.tracks_table.setItem(row, 1, QTableWidgetItem(track["artist"]))
            self.tracks_table.setItem(row, 2, QTableWidgetItem(track["duration"]))

        self.track_count_label.setText(f"Треков: {len(tracks)}")

    # UI event handlers

    def _on_service_changed(self, service: str):
        """Handle service selection change"""
        if self._viewModel:
            self._viewModel.select_service(service)

    def _on_playlist_selected(self):
        """Handle playlist selection in UI"""
        current_item = self.playlist_list.currentItem()
        if current_item and self._viewModel:
            self._viewModel.select_playlist(current_item.text())

    def _on_auth_clicked(self):
        """Handle auth button click"""
        if self._viewModel:
            self._viewModel.authenticate()
