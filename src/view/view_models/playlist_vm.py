from PySide6.QtCore import QObject, Signal, Property
from typing import List, Optional


class PlaylistViewModel(QObject):
    """ViewModel for PlaylistWidget"""

    # Signals
    service_changed = Signal(str)
    playlists_loaded = Signal()
    playlist_selected = Signal(str)
    tracks_loaded = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._services: List[str] = []
        self._current_service: Optional[str] = None
        self._playlists: List[str] = []
        self._current_playlist: Optional[str] = None
        self._tracks: List[dict] = []
        self._is_authenticated: bool = False

        self._load_mock_services()

    def _load_mock_services(self):
        """Load mock services - later will use ServiceRegistry"""
        self._services = ["local", "vk", "spotify"]

    # Properties

    @Property(list, constant=True)
    def services(self) -> List[str]:
        """List of available services"""
        return self._services

    @Property(str, notify=service_changed)
    def current_service(self) -> Optional[str]:
        """Currently selected service"""
        return self._current_service

    @current_service.setter
    def current_service(self, service: str):
        if self._current_service != service:
            self._current_service = service
            self.service_changed.emit(service)
            self._load_playlists_for_service(service)

    @Property(list, notify=playlists_loaded)
    def playlists(self) -> List[str]:
        """List of playlists for current service"""
        return self._playlists

    @Property(str, notify=playlist_selected)
    def current_playlist(self) -> Optional[str]:
        """Currently selected playlist"""
        return self._current_playlist

    @current_playlist.setter
    def current_playlist(self, playlist: str):
        if self._current_playlist != playlist:
            self._current_playlist = playlist
            self.playlist_selected.emit(playlist)
            self._load_tracks_for_playlist(playlist)

    @Property(list, notify=tracks_loaded)
    def tracks(self) -> List[dict]:
        """List of tracks in current playlist"""
        return self._tracks

    @Property(bool, notify=service_changed)
    def is_authenticated(self) -> bool:
        """Authentication status for current service"""
        return self._is_authenticated

    # Methods

    def _load_playlists_for_service(self, service: str):
        """Load playlists for selected service - mock implementation"""
        mock_playlists = {
            "spotify": [
                "a",
                "b",
                "c",
                "d",
            ],
            "vk": [
                "1",
                "2",
                "3",
            ],
            "local": [
                "/Music/1",
                "/Music/2",
            ],
        }
        self._playlists = mock_playlists.get(service, [])
        self._current_playlist = None
        self._tracks = []
        self.playlists_loaded.emit()

    def _load_tracks_for_playlist(self, playlist: str):
        """Load tracks for selected playlist - mock implementation"""
        mock_tracks = [
            {"title": "Song 1", "artist": "Artist A", "duration": "3:45"},
            {"title": "Song 2", "artist": "Artist B", "duration": "4:12"},
            {"title": "Song 3", "artist": "Artist C", "duration": "2:58"},
            {"title": "Song 4", "artist": "Artist D", "duration": "5:01"},
            {"title": "Song 5", "artist": "Artist E", "duration": "3:30"},
        ]
        self._tracks = mock_tracks
        self.tracks_loaded.emit()

    def authenticate(self):
        """Authenticate with current service - mock implementation"""
        self._is_authenticated = True
        self.service_changed.emit(self._current_service)

    def select_service(self, service: str):
        """Select a service"""
        self.current_service = service

    def select_playlist(self, playlist: str):
        """Select a playlist"""
        self.current_playlist = playlist
