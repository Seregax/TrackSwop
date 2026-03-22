from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

from PySide6.QtCore import QObject, Signal, Property, QTimer


class TransferStatus(Enum):
    """Transfer status enum"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class TransferLogEntry:
    """Log entry for transfer operation"""
    timestamp: str
    message: str
    level: str = "info"  # info, warning, error


@dataclass
class TransferStatistics:
    """Statistics for transfer operation"""
    total_tracks: int = 0
    processed_tracks: int = 0
    failed_tracks: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    @property
    def progress(self) -> int:
        """Calculate progress percentage"""
        if self.total_tracks == 0:
            return 0
        return int((self.processed_tracks / self.total_tracks) * 100)

    @property
    def duration(self) -> str:
        """Calculate transfer duration"""
        if not self.start_time:
            return "0:00"
        
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time) if self.end_time else datetime.now()
        delta = end - start
        minutes = int(delta.total_seconds() // 60)
        seconds = int(delta.total_seconds() % 60)
        return f"{minutes}:{seconds:02d}"


class TransferViewModel(QObject):
    """ViewModel for TransferWidget"""

    # Signals
    status_changed = Signal()
    progress_changed = Signal()
    statistics_changed = Signal()
    log_updated = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._status: TransferStatus = TransferStatus.IDLE
        self._statistics = TransferStatistics()
        self._log: List[TransferLogEntry] = []
        self._source_service: Optional[str] = None
        self._destination_service: Optional[str] = None
        self._source_playlist: Optional[str] = None
        self._destination_playlist: Optional[str] = None
        
        # Mock timer for simulating transfer
        self._mock_timer: Optional[QTimer] = None
        self._mock_counter: int = 0

    # Properties

    @Property(str, notify=status_changed)
    def status(self) -> str:
        """Current transfer status"""
        return self._status.value

    @Property(int, notify=progress_changed)
    def progress(self) -> int:
        """Current progress percentage"""
        return self._statistics.progress

    @Property(int, notify=statistics_changed)
    def total_tracks(self) -> int:
        """Total tracks to transfer"""
        return self._statistics.total_tracks

    @Property(int, notify=statistics_changed)
    def processed_tracks(self) -> int:
        """Processed tracks count"""
        return self._statistics.processed_tracks

    @Property(int, notify=statistics_changed)
    def failed_tracks(self) -> int:
        """Failed tracks count"""
        return self._statistics.failed_tracks

    @Property(str, notify=statistics_changed)
    def duration(self) -> str:
        """Transfer duration"""
        return self._statistics.duration

    @Property(list, notify=log_updated)
    def log(self) -> List[dict]:
        """Transfer log entries"""
        return [
            {"timestamp": entry.timestamp, "message": entry.message, "level": entry.level}
            for entry in self._log
        ]

    @Property(str, notify=status_changed)
    def source_service(self) -> Optional[str]:
        """Source service name"""
        return self._source_service

    @source_service.setter
    def source_service(self, value: str):
        if self._source_service != value:
            self._source_service = value
            self.status_changed.emit()

    @Property(str, notify=status_changed)
    def destination_service(self) -> Optional[str]:
        """Destination service name"""
        return self._destination_service

    @destination_service.setter
    def destination_service(self, value: str):
        if self._destination_service != value:
            self._destination_service = value
            self.status_changed.emit()

    @Property(str, notify=status_changed)
    def source_playlist(self) -> Optional[str]:
        """Source playlist name"""
        return self._source_playlist

    @source_playlist.setter
    def source_playlist(self, value: str):
        if self._source_playlist != value:
            self._source_playlist = value
            self.status_changed.emit()

    @Property(str, notify=status_changed)
    def destination_playlist(self) -> Optional[str]:
        """Destination playlist name"""
        return self._destination_playlist

    @destination_playlist.setter
    def destination_playlist(self, value: str):
        if self._destination_playlist != value:
            self._destination_playlist = value
            self.status_changed.emit()

    # Methods

    def start_transfer(self):
        """Start the transfer process"""
        if self._status == TransferStatus.RUNNING:
            return

        self._status = TransferStatus.RUNNING
        self._statistics = TransferStatistics(
            total_tracks=50,  # Mock value
            start_time=datetime.now().isoformat(),
        )
        self._log = []
        self._mock_counter = 0

        self._add_log("Начало переноса")
        self._add_log(f"Источник: {self._source_service} -> {self._source_playlist}")
        self._add_log(f"Назначение: {self._destination_service} -> {self._destination_playlist}")

        self.status_changed.emit()
        self.statistics_changed.emit()
        self.log_updated.emit()

        # Start mock transfer simulation
        self._mock_timer = QTimer()
        self._mock_timer.timeout.connect(self._mock_transfer_step)
        self._mock_timer.start(200)  # Update every 200ms

    def cancel_transfer(self):
        """Cancel the transfer process"""
        if self._status != TransferStatus.RUNNING:
            return

        if self._mock_timer:
            self._mock_timer.stop()
            self._mock_timer = None

        self._status = TransferStatus.CANCELLED
        self._statistics.end_time = datetime.now().isoformat()
        self._add_log("Перенос отменён пользователем", "warning")

        self.status_changed.emit()
        self.statistics_changed.emit()
        self.log_updated.emit()

    def _mock_transfer_step(self):
        """Mock transfer step - simulates progress"""
        self._mock_counter += 1
        self._statistics.processed_tracks = min(self._mock_counter, self._statistics.total_tracks)
        
        # Mock some failures
        if self._mock_counter % 10 == 0:
            self._statistics.failed_tracks += 1
            self._add_log(f"Ошибка обработки трека {self._mock_counter}", "error")

        self.progress_changed.emit()
        self.statistics_changed.emit()

        if self._mock_counter >= self._statistics.total_tracks:
            self._complete_transfer()

    def _complete_transfer(self):
        """Complete the transfer process"""
        if self._mock_timer:
            self._mock_timer.stop()
            self._mock_timer = None

        self._status = TransferStatus.COMPLETED
        self._statistics.end_time = datetime.now().isoformat()
        self._add_log(f"Перенос завершён. Успешно: {self._statistics.processed_tracks - self._statistics.failed_tracks}, Ошибок: {self._statistics.failed_tracks}")

        self.status_changed.emit()
        self.progress_changed.emit()
        self.statistics_changed.emit()
        self.log_updated.emit()

    def _add_log(self, message: str, level: str = "info"):
        """Add log entry"""
        entry = TransferLogEntry(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            message=message,
            level=level,
        )
        self._log.append(entry)
        self.log_updated.emit()

    def clear_log(self):
        """Clear the transfer log"""
        self._log = []
        self.log_updated.emit()

    def reset(self):
        """Reset transfer state"""
        if self._mock_timer:
            self._mock_timer.stop()
            self._mock_timer = None

        self._status = TransferStatus.IDLE
        self._statistics = TransferStatistics()
        self._log = []
        self._mock_counter = 0

        self.status_changed.emit()
        self.progress_changed.emit()
        self.statistics_changed.emit()
        self.log_updated.emit()
