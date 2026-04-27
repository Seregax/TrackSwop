"""
Worker for loading tracks in a background thread.

This prevents the UI from freezing while fetching tracks from services.
"""

from typing import List
from PySide6.QtCore import QThread, Signal

from src.model.entities.playlist import Playlist
from src.model.entities.track import Track
from src.model.services.interfaces.istreaming_service import IStreamingService
from src.common.logger import get_logger

logger = get_logger(__name__)


class TracksLoadingWorker(QThread):
    """
    Worker thread for loading tracks from a playlist.
    
    Signals:
        - finished(List[Track]): Emitted when tracks are successfully loaded
        - error(str): Emitted when an error occurs during loading
    """
    
    # Signals
    finished = Signal(list)  # List[Track]
    error = Signal(str)
    
    def __init__(self, service: IStreamingService, playlist: Playlist, parent=None):
        """
        Initialize the worker.
        
        Args:
            service: IStreamingService instance to load tracks from
            playlist: Playlist entity to load tracks for
            parent: Parent QObject
        """
        super().__init__(parent)
        self._service = service
        self._playlist = playlist
        
    def run(self):
        """
        Run the worker thread.
        
        This method is called when the thread starts.
        Loads tracks and emits appropriate signals.
        """
        try:
            logger.info(f"Starting tracks loading from playlist: {self._playlist.name}")
            tracks = self._service.get_tracks_from_playlist(self._playlist)
            logger.info(f"Successfully loaded {len(tracks)} tracks")
            self.finished.emit(tracks)
        except Exception as e:
            error_msg = f"Failed to load tracks: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)
