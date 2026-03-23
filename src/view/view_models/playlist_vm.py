"""
Playlist ViewModel

Manages playlist UI state. Does not handle authentication or service creation.
"""

from typing import List, Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, Property

from src.model.entities.playlist import Playlist
from src.model.entities.track import Track
from src.model.services.interfaces.istreaming_service import IStreamingService


class PlaylistViewModel(QObject):
    """
    ViewModel for PlaylistWidget.
    
    Manages UI state only. Authentication and service management
    are handled by MainWindowViewModel.
    """

    # Signals
    service_selected = Signal(str)  # Service selected by user
    playlists_loaded = Signal()
    playlist_selected = Signal(str)
    tracks_loaded = Signal()

    def __init__(self, service_name: str = "", parent=None):
        super().__init__(parent)
        self._panel_name = service_name  # "source" or "dest"
        self._services: List[str] = []  # Set by parent
        self._selected_service: Optional[str] = None
        self._playlists: List[str] = []
        self._current_playlist: Optional[str] = None
        self._tracks: List[dict] = []
        self._is_authenticated: bool = False
        
        # Cache entities
        self._playlist_objects: Dict[str, Playlist] = {}
        self._track_objects: Dict[str, List[Track]] = {}

    # Properties

    @Property(list, notify=playlists_loaded)
    def services(self) -> List[str]:
        """List of available services (set by parent)"""
        return self._services
    
    @services.setter
    def services(self, value: List[str]):
        self._services = value

    @Property(str, notify=service_selected)
    def selected_service(self) -> Optional[str]:
        """Currently selected service"""
        return self._selected_service

    @Property(str, notify=playlist_selected)
    def current_playlist(self) -> Optional[str]:
        """Currently selected playlist"""
        return self._current_playlist

    @current_playlist.setter
    def current_playlist(self, playlist: str):
        if self._current_playlist != playlist:
            self._current_playlist = playlist
            self.playlist_selected.emit(playlist)

    @Property(list, notify=playlists_loaded)
    def playlists(self) -> List[str]:
        """List of playlists for current service"""
        return self._playlists

    @Property(list, notify=tracks_loaded)
    def tracks(self) -> List[dict]:
        """List of tracks in current playlist"""
        return self._tracks

    @Property(bool)
    def is_authenticated(self) -> bool:
        """Authentication status"""
        return self._is_authenticated

    @Property(bool)
    def has_playlist_selected(self) -> bool:
        """True if a playlist is selected"""
        return self._current_playlist is not None

    @Property(object)
    def current_playlist_object(self) -> Optional[Playlist]:
        """Get current Playlist entity"""
        if self._current_playlist:
            return self._playlist_objects.get(self._current_playlist)
        return None

    # Methods

    def set_authenticated(self, is_auth: bool):
        """Set authentication status"""
        self._is_authenticated = is_auth

    def select_service(self, service: str):
        """User selected a service"""
        if self._selected_service != service:
            self._selected_service = service
            self.service_selected.emit(service)

    def load_playlists(self, playlists: List[Playlist]):
        """
        Load playlists from service.
        
        Args:
            playlists: List of Playlist entities
        """
        self._playlists = [p.name for p in playlists]
        self._playlist_objects = {p.name: p for p in playlists}
        self._current_playlist = None
        self._tracks = []
        self._track_objects.clear()
        self.playlists_loaded.emit()

    def load_tracks(self, tracks: List[Track]):
        """
        Load tracks for current playlist.
        
        Args:
            tracks: List of Track entities
        """
        self._tracks = [
            {
                "title": track.title,
                "artist": ", ".join(track.artists) if track.artists else "Unknown",
                "duration": self._format_duration(track.duration) if track.duration else "Unknown",
            }
            for track in tracks
        ]
        if self._current_playlist:
            self._track_objects[self._current_playlist] = tracks
        self.tracks_loaded.emit()

    def get_track_objects(self) -> List[Track]:
        """Get current Track entities"""
        if self._current_playlist:
            return self._track_objects.get(self._current_playlist, [])
        return []

    @staticmethod
    def _format_duration(duration_seconds: float) -> str:
        """Format duration in seconds to MM:SS"""
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def reset(self):
        """Reset state"""
        self._playlists = []
        self._current_playlist = None
        self._tracks = []
        self._playlist_objects.clear()
        self._track_objects.clear()
        self._is_authenticated = False
        self.playlists_loaded.emit()
