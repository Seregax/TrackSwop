from abc import ABC, abstractmethod
from typing import List

from src.model.entities.playlist import Playlist
from src.model.entities.track import Track
from src.model.services.interfaces.service_info import ServiceInfo
from src.model.specifications.base import BaseSpecification


class IStreamingService(ABC):
    """Abstract class for all services"""

    @abstractmethod
    def get_service_info(self) -> ServiceInfo:
        pass

    @abstractmethod
    def authenticate(self) -> None:
        pass

    @abstractmethod
    def get_playlists(self) -> List[Playlist]:
        pass

    @abstractmethod
    def get_tracks_from_playlist(self, playlist: Playlist) -> List[Track]:
        pass

    @abstractmethod
    def add_playlist(self, playlist: Playlist) -> None:
        pass

    @abstractmethod
    def add_track_to_playlist(self, playlist: Playlist, track: Track) -> None:
        pass

    @abstractmethod
    def export_playlist(self, source: Playlist, destination: Playlist) -> None:
        pass

    @abstractmethod
    def get_import_specs(self) -> BaseSpecification:
        pass

    @abstractmethod
    def get_export_specs(self) -> BaseSpecification:
        pass

    @abstractmethod
    def get_auth_specs(self) -> BaseSpecification:
        pass
