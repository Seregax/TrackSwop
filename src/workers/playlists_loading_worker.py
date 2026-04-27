"""
Worker for loading playlists in a background thread.

This prevents the UI from freezing while fetching playlists from services.
"""

from typing import List, Optional
from PySide6.QtCore import QThread, Signal

from src.model.entities.playlist import Playlist
from src.model.services.interfaces.istreaming_service import IStreamingService
from src.common.logger import get_logger

logger = get_logger(__name__)


class PlaylistsLoadingWorker(QThread):
    """
    Worker thread for loading playlists from a service.
    
    Signals:
        - finished(List[Playlist]): Emitted when playlists are successfully loaded
        - error(str): Emitted when an error occurs during loading
    """
    
    # Signals
    finished = Signal(list)  # List[Playlist]
    error = Signal(str)
    
    def __init__(self, service: IStreamingService, parent=None):
        """
        Initialize the worker.
        
        Args:
            service: IStreamingService instance to load playlists from
            parent: Parent QObject
        """
        super().__init__(parent)
        self._service = service
        
    def run(self):
        """
        Run the worker thread.
        
        This method is called when the thread starts.
        Loads playlists and emits appropriate signals.
        """
        try:
            logger.info(f"Starting playlist loading from service...")
            playlists = self._service.get_playlists()
            logger.info(f"Successfully loaded {len(playlists)} playlists")
            self.finished.emit(playlists)
        except Exception as e:
            error_msg = f"Failed to load playlists: {str(e)}"
            logger.error(error_msg)
            self.error.emit(error_msg)
