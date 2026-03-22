from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QProgressBar,
    QLabel,
    QPushButton,
    QGroupBox,
    QTextEdit,
    QGridLayout,
)

from src.view.view_models.transfer_vm import TransferViewModel


class TransferWidget(QWidget):
    """Widget for displaying transfer progress and statistics"""

    # Signal for back button - parent can connect to switch view
    back_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._viewModel: Optional[TransferViewModel] = None
        self._setup_ui()

    def _setup_ui(self):
        """Setup the widget UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # Transfer info group
        info_group = self._create_info_group()
        layout.addWidget(info_group)

        # Progress group
        progress_group = self._create_progress_group()
        layout.addWidget(progress_group)

        # Statistics group
        stats_group = self._create_statistics_group()
        layout.addWidget(stats_group)

        # Log group
        log_group = self._create_log_group()
        layout.addWidget(log_group, stretch=1)

        # Control buttons
        buttons_layout = self._create_buttons_layout()
        layout.addLayout(buttons_layout)

    def _create_info_group(self) -> QGroupBox:
        """Create transfer info group"""
        group = QGroupBox("Информация о переносе")
        layout = QGridLayout(group)

        # Source
        layout.addWidget(QLabel("Источник:"), 0, 0)
        self.source_label = QLabel("—")
        self.source_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        layout.addWidget(self.source_label, 0, 1)

        # Destination
        layout.addWidget(QLabel("Назначение:"), 1, 0)
        self.dest_label = QLabel("—")
        self.dest_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        layout.addWidget(self.dest_label, 1, 1)

        # Status
        layout.addWidget(QLabel("Статус:"), 2, 0)
        self.status_label = QLabel("Ожидание")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.status_label, 2, 1)

        return group

    def _create_progress_group(self) -> QGroupBox:
        """Create progress group"""
        group = QGroupBox("Прогресс")
        layout = QVBoxLayout(group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setMinimumHeight(25)
        layout.addWidget(self.progress_bar)

        # Progress text
        self.progress_text = QLabel("0 / 0 треков")
        self.progress_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.progress_text)

        return group

    def _create_statistics_group(self) -> QGroupBox:
        """Create statistics group"""
        group = QGroupBox("Статистика")
        layout = QGridLayout(group)

        # Total tracks
        layout.addWidget(QLabel("Всего треков:"), 0, 0)
        self.total_label = QLabel("0")
        layout.addWidget(self.total_label, 0, 1)

        # Processed
        layout.addWidget(QLabel("Обработано:"), 0, 2)
        self.processed_label = QLabel("0")
        self.processed_label.setStyleSheet("color: green;")
        layout.addWidget(self.processed_label, 0, 3)

        # Failed
        layout.addWidget(QLabel("Ошибки:"), 1, 0)
        self.failed_label = QLabel("0")
        self.failed_label.setStyleSheet("color: red;")
        layout.addWidget(self.failed_label, 1, 1)

        # Duration
        layout.addWidget(QLabel("Время:"), 1, 2)
        self.duration_label = QLabel("0:00")
        layout.addWidget(self.duration_label, 1, 3)

        return group

    def _create_log_group(self) -> QGroupBox:
        """Create log group"""
        group = QGroupBox("Журнал операций")
        layout = QVBoxLayout(group)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFont(QFont("Consolas", 9))
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.log_output)

        # Clear log button
        self.clear_log_btn = QPushButton("Очистить журнал")
        self.clear_log_btn.setMaximumWidth(150)
        self.clear_log_btn.clicked.connect(self._on_clear_log_clicked)
        layout.addWidget(self.clear_log_btn)

        return group

    def _create_buttons_layout(self) -> QHBoxLayout:
        """Create control buttons layout"""
        layout = QHBoxLayout()

        # Back button
        self.back_btn = QPushButton("← Назад к плейлистам")
        self.back_btn.setMaximumWidth(180)
        self.back_btn.clicked.connect(self._on_back_clicked)
        layout.addWidget(self.back_btn)

        layout.addStretch()

        # Start button
        self.start_btn = QPushButton("Начать перенос")
        self.start_btn.setMinimumSize(150, 40)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #1DB954;
                color: white;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1ed760;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.start_btn.clicked.connect(self._on_start_clicked)
        layout.addWidget(self.start_btn)

        # Cancel button
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setMinimumSize(120, 40)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.cancel_btn.clicked.connect(self._on_cancel_clicked)
        self.cancel_btn.setEnabled(False)
        layout.addWidget(self.cancel_btn)

        return layout

    def set_view_model(self, viewModel: TransferViewModel):
        """Set the ViewModel and connect signals"""
        self._viewModel = viewModel

        # Connect signals
        viewModel.status_changed.connect(self._on_status_changed)
        viewModel.progress_changed.connect(self._on_progress_changed)
        viewModel.statistics_changed.connect(self._on_statistics_changed)
        viewModel.log_updated.connect(self._on_log_updated)

        # Update initial state
        self._update_from_vm()

    def _update_from_vm(self):
        """Update UI from ViewModel"""
        if not self._viewModel:
            return

        # Update info
        source = self._viewModel.source_service or "—"
        playlist = self._viewModel.source_playlist or ""
        self.source_label.setText(f"{source} → {playlist}" if playlist else source)

        dest = self._viewModel.destination_service or "—"
        dest_playlist = self._viewModel.destination_playlist or ""
        self.dest_label.setText(f"{dest} → {dest_playlist}" if dest_playlist else dest)

        # Update progress
        self.progress_bar.setValue(self._viewModel.progress)
        processed = self._viewModel.processed_tracks
        total = self._viewModel.total_tracks
        self.progress_text.setText(f"{processed} / {total} треков")

        # Update statistics
        self.total_label.setText(str(total))
        self.processed_label.setText(str(processed))
        self.failed_label.setText(str(self._viewModel.failed_tracks))
        self.duration_label.setText(self._viewModel.duration)

        # Update status
        self._update_status_display()

        # Update buttons
        self._update_buttons()

    def _update_status_display(self):
        """Update status label appearance"""
        if not self._viewModel:
            return

        status = self._viewModel.status
        self.status_label.setText(status)

        colors = {
            "idle": "gray",
            "running": "blue",
            "completed": "green",
            "cancelled": "orange",
            "error": "red",
        }
        color = colors.get(status, "gray")
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def _update_buttons(self):
        """Update button states"""
        if not self._viewModel:
            return

        is_running = self._viewModel.status == "running"
        self.start_btn.setEnabled(not is_running)
        self.cancel_btn.setEnabled(is_running)

    def _on_status_changed(self):
        """Handle status change from ViewModel"""
        self._update_status_display()
        self._update_buttons()

    def _on_progress_changed(self):
        """Handle progress change from ViewModel"""
        if self._viewModel:
            self.progress_bar.setValue(self._viewModel.progress)
            processed = self._viewModel.processed_tracks
            total = self._viewModel.total_tracks
            self.progress_text.setText(f"{processed} / {total} треков")

    def _on_statistics_changed(self):
        """Handle statistics change from ViewModel"""
        if self._viewModel:
            self.total_label.setText(str(self._viewModel.total_tracks))
            self.processed_label.setText(str(self._viewModel.processed_tracks))
            self.failed_label.setText(str(self._viewModel.failed_tracks))
            self.duration_label.setText(self._viewModel.duration)

    def _on_log_updated(self):
        """Handle log update from ViewModel"""
        if not self._viewModel:
            return

        self.log_output.clear()
        for entry in self._viewModel.log:
            timestamp = entry["timestamp"]
            message = entry["message"]
            level = entry["level"]

            colors = {
                "info": "#d4d4d4",
                "warning": "#f39c12",
                "error": "#e74c3c",
            }
            color = colors.get(level, "#d4d4d4")

            self.log_output.append(
                f'<span style="color: #888;">[{timestamp}]</span> '
                f'<span style="color: {color};">{message}</span>'
            )

        # Scroll to bottom
        scrollbar = self.log_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_start_clicked(self):
        """Handle start button click"""
        if self._viewModel:
            self._viewModel.start_transfer()

    def _on_cancel_clicked(self):
        """Handle cancel button click"""
        if self._viewModel:
            self._viewModel.cancel_transfer()

    def _on_clear_log_clicked(self):
        """Handle clear log button click"""
        if self._viewModel:
            self._viewModel.clear_log()

    def _on_back_clicked(self):
        """Handle back button click - emit signal for parent to handle"""
        self.back_requested.emit()
