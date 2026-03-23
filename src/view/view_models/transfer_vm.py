from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, Property, QTimer, QThread

from src.model.entities.playlist import Playlist
from src.model.entities.track import Track
from src.model.services.interfaces.istreaming_service import IStreamingService


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


class TransferWorker(QObject):
    """
    Worker for performing transfer in background thread.
    
    Emits signals for progress updates.
    """
    progress_updated = Signal(int, int)  # processed, total
    track_processed = Signal(str, bool, str)  # track_title, success, error_message
    transfer_completed = Signal(int, int)  # success_count, fail_count
    transfer_error = Signal(str)  # error_message
    
    def __init__(
        self,
        source_service: IStreamingService,
        dest_service: IStreamingService,
        source_playlist: Playlist,
        dest_playlist: Playlist,
    ):
        super().__init__()
        self.source_service = source_service
        self.dest_service = dest_service
        self.source_playlist = source_playlist
        self.dest_playlist = dest_playlist
        self._cancelled = False
    
    def run(self):
        """Execute the transfer"""
        try:
            success_count = 0
            fail_count = 0
            
            # Get tracks from source
            tracks = self.source_service.get_tracks_from_playlist(self.source_playlist)
            total = len(tracks)
            
            self.progress_updated.emit(0, total)
            
            for i, track in enumerate(tracks):
                if self._cancelled:
                    break
                    
                try:
                    self.dest_service.add_track_to_playlist(self.dest_playlist, track)
                    success_count += 1
                    self.track_processed.emit(track.title, True, "")
                except Exception as e:
                    fail_count += 1
                    self.track_processed.emit(track.title, False, str(e))
                
                self.progress_updated.emit(i + 1, total)
            
            if self._cancelled:
                self.transfer_error.emit("Transfer cancelled by user")
            else:
                self.transfer_completed.emit(success_count, fail_count)
                
        except Exception as e:
            self.transfer_error.emit(str(e))
    
    def cancel(self):
        """Cancel the transfer"""
        self._cancelled = True


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
        
        # Service instances and objects
        self._source_service_instance: Optional[IStreamingService] = None
        self._dest_service_instance: Optional[IStreamingService] = None
        self._source_playlist_object: Optional[Playlist] = None
        self._dest_playlist_object: Optional[Playlist] = None
        
        # Worker thread
        self._worker_thread: Optional[QThread] = None
        self._worker: Optional[TransferWorker] = None

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

    def set_service_instances(
        self,
        source_service: IStreamingService,
        dest_service: IStreamingService,
        source_playlist: Playlist,
        dest_playlist: Playlist,
    ):
        """
        Set service instances and playlist objects for transfer.
        
        Args:
            source_service: Source service instance
            dest_service: Destination service instance
            source_playlist: Source playlist entity
            dest_playlist: Destination playlist entity
        """
        self._source_service_instance = source_service
        self._dest_service_instance = dest_service
        self._source_playlist_object = source_playlist
        self._dest_playlist_object = dest_playlist

    def start_transfer(self):
        """Start the transfer process"""
        if self._status == TransferStatus.RUNNING:
            return

        if not all([
            self._source_service_instance,
            self._dest_service_instance,
            self._source_playlist_object,
            self._dest_playlist_object,
        ]):
            self._add_log("Ошибка: сервисы или плейлисты не настроены", "error")
            self._status = TransferStatus.ERROR
            self.status_changed.emit()
            return

        self._status = TransferStatus.RUNNING
        self._statistics = TransferStatistics(
            start_time=datetime.now().isoformat(),
        )
        self._log = []

        self._add_log("Начало переноса")
        self._add_log(f"Источник: {self._source_service} -> {self._source_playlist}")
        self._add_log(f"Назначение: {self._destination_service} -> {self._destination_playlist}")

        self.status_changed.emit()
        self.statistics_changed.emit()
        self.log_updated.emit()

        # Create and start worker thread
        self._worker_thread = QThread()
        self._worker = TransferWorker(
            self._source_service_instance,
            self._dest_service_instance,
            self._source_playlist_object,
            self._dest_playlist_object,
        )
        
        # Move worker to thread
        self._worker.moveToThread(self._worker_thread)
        
        # Connect signals
        self._worker_thread.started.connect(self._worker.run)
        self._worker.progress_updated.connect(self._on_progress_updated)
        self._worker.track_processed.connect(self._on_track_processed)
        self._worker.transfer_completed.connect(self._on_transfer_completed)
        self._worker.transfer_error.connect(self._on_transfer_error)
        
        # Start thread
        self._worker_thread.start()

    def cancel_transfer(self):
        """Cancel the transfer process"""
        if self._status != TransferStatus.RUNNING:
            return

        if self._worker:
            self._worker.cancel()
            
        self._add_log("Перенос отменён пользователем", "warning")
        self._status = TransferStatus.CANCELLED
        self._statistics.end_time = datetime.now().isoformat()

        self.status_changed.emit()
        self.statistics_changed.emit()
        self.log_updated.emit()

    def _on_progress_updated(self, processed: int, total: int):
        """Handle progress update from worker"""
        self._statistics.processed_tracks = processed
        self._statistics.total_tracks = total
        self.progress_changed.emit()
        self.statistics_changed.emit()

    def _on_track_processed(self, track_title: str, success: bool, error_message: str):
        """Handle track processed event from worker"""
        if success:
            self._add_log(f"✓ Добавлен трек: {track_title}")
        else:
            self._add_log(f"✗ Ошибка: {track_title} - {error_message}", "error")

    def _on_transfer_completed(self, success_count: int, fail_count: int):
        """Handle transfer completion"""
        self._status = TransferStatus.COMPLETED
        self._statistics.end_time = datetime.now().isoformat()
        self._add_log(
            f"Перенос завершён. Успешно: {success_count}, Ошибок: {fail_count}"
        )

        self.status_changed.emit()
        self.progress_changed.emit()
        self.statistics_changed.emit()
        self.log_updated.emit()

        # Cleanup thread
        self._cleanup_thread()

    def _on_transfer_error(self, error_message: str):
        """Handle transfer error"""
        self._status = TransferStatus.ERROR
        self._statistics.end_time = datetime.now().isoformat()
        self._add_log(f"Ошибка переноса: {error_message}", "error")

        self.status_changed.emit()
        self.statistics_changed.emit()
        self.log_updated.emit()

        # Cleanup thread
        self._cleanup_thread()

    def _cleanup_thread(self):
        """Cleanup worker thread"""
        if self._worker_thread:
            self._worker_thread.quit()
            self._worker_thread.wait(3000)  # Wait up to 3 seconds
            self._worker_thread = None
        self._worker = None

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
        if self._worker_thread:
            self._cleanup_thread()

        self._status = TransferStatus.IDLE
        self._statistics = TransferStatistics()
        self._log = []

        self.status_changed.emit()
        self.progress_changed.emit()
        self.statistics_changed.emit()
        self.log_updated.emit()
