from pathlib import Path
from typing import List, Optional, Dict

from src.model.entities.playlist import Playlist
from src.model.entities.track import Track
from src.model.services.interfaces.istreaming_service import IStreamingService
from src.model.services.interfaces.service_info import ServiceInfo
from src.model.specifications.base import BaseSpecification
from src.model.services.providers.local.local_directory_parser import LocalDirectoryParser
from src.model.services.providers.local.local_auth_spec import LocalAuthSpec
from src.model.services.providers.local.local_import_spec import LocalImportSpec
from src.model.services.providers.local.local_export_spec import LocalExportSpec
from src.common.logger import get_logger

logger = get_logger(__name__)


class LocalService(IStreamingService):
    """
    Local file service for importing playlists from local directories.
    
    Supports:
    - Import from single directory (playlist ".")
    - Import from subdirectories (one level deep, each subdirectory = separate playlist)
    
    Export is not supported.
    """

    SERVICE_NAME = "local"

    def __init__(self, directory: Optional[str] = None):
        """
        Initialize LocalService.
        
        Args:
            directory: Path to music directory (set via authenticate())
        """
        self.directory: Optional[Path] = Path(directory) if directory else None
        self.parser = LocalDirectoryParser()
        self._playlists_cache: Dict[str, List[Track]] = {}

    def get_service_info(self) -> ServiceInfo:
        """Get service information"""
        return ServiceInfo(
            name="Local Files",
            icon_path=None,  # No icon for local files
        )

    def authenticate(self, directory: Optional[str] = None) -> None:
        """
        Authenticate by setting the music directory.
        
        Args:
            directory: Path to music directory
        """
        if directory:
            self.directory = Path(directory)
        
        if not self.directory or not self.directory.exists():
            raise ValueError(f"Directory does not exist: {self.directory}")
        
        if not self.directory.is_dir():
            raise ValueError(f"Path is not a directory: {self.directory}")
        
        # Clear cache on re-authentication
        self._playlists_cache = {}
        logger.info(f"LocalService authenticated with directory: {self.directory}")

    def get_playlists(self) -> List[Playlist]:
        """
        Get all playlists from the directory.
        
        Returns:
            List of playlists:
            - "." playlist with all tracks from root directory
            - Subdirectory playlists (one level deep)
        """
        if not self.directory:
            logger.error("Not authenticated. Call authenticate() first.")
            raise Exception("Not authenticated. Call authenticate() first.")
        
        playlists: List[Playlist] = []
        
        # Root directory playlist ("." - all tracks from root)
        root_tracks = self._get_root_tracks()
        playlists.append(Playlist(name=".", tracks=root_tracks))
        
        # Subdirectory playlists (one level deep)
        for subdir in self._get_subdirectories():
            sub_tracks = self._get_subdirectory_tracks(subdir)
            if sub_tracks:  # Only add if there are tracks
                playlists.append(Playlist(name=subdir.name, tracks=sub_tracks))
        
        logger.info(f"Found {len(playlists)} playlists in {self.directory}")
        return playlists

    def get_tracks_from_playlist(self, playlist: Playlist) -> List[Track]:
        """
        Get tracks from a specific playlist.
        
        Args:
            playlist: Playlist object
            
        Returns:
            List of tracks
        """
        if not self.directory:
            logger.error("Not authenticated. Call authenticate() first.")
            raise Exception("Not authenticated. Call authenticate() first.")
        
        # Root playlist
        if playlist.name == ".":
            return self._get_root_tracks()
        
        # Subdirectory playlist
        for subdir in self._get_subdirectories():
            if subdir.name == playlist.name:
                return self._get_subdirectory_tracks(subdir)
        
        raise ValueError(f"Playlist '{playlist.name}' not found")

    def add_playlist(self, playlist: Playlist) -> None:
        """
        Create new playlist - not supported for local files.
        
        Raises:
            NotImplementedError: LocalService does not support creating playlists
        """
        raise NotImplementedError("LocalService does not support creating playlists")

    def add_track_to_playlist(self, playlist: Playlist, track: Track) -> None:
        """
        Add track to playlist - not supported for local files.
        
        Raises:
            NotImplementedError: LocalService does not support adding tracks
        """
        raise NotImplementedError("LocalService does not support adding tracks to playlists")

    def export_playlist(self, source: Playlist, destination: Playlist) -> None:
        """
        Export playlist - not supported for local files.
        
        Raises:
            NotImplementedError: LocalService does not support export
        """
        raise NotImplementedError("LocalService does not support export")

    def get_import_specs(self) -> BaseSpecification:
        """Get import specifications"""
        return LocalImportSpec()

    def get_export_specs(self) -> BaseSpecification:
        """Get export specifications"""
        return LocalExportSpec()

    def get_auth_specs(self) -> BaseSpecification:
        """Get authentication specifications"""
        return LocalAuthSpec()

    # Helper methods

    def _get_root_tracks(self) -> List[Track]:
        """Get tracks from root directory (non-recursive)"""
        if not self.directory:
            return []
        
        cache_key = "."
        if cache_key in self._playlists_cache:
            return self._playlists_cache[cache_key]
        
        tracks = self.parser.parse_directory(self.directory)
        self._playlists_cache[cache_key] = tracks
        return tracks

    def _get_subdirectories(self) -> List[Path]:
        """Get immediate subdirectories (one level deep)"""
        if not self.directory:
            return []
        
        return [
            d for d in self.directory.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

    def _get_subdirectory_tracks(self, subdir: Path) -> List[Track]:
        """Get tracks from a subdirectory (non-recursive)"""
        cache_key = subdir.name
        if cache_key in self._playlists_cache:
            return self._playlists_cache[cache_key]
        
        tracks = self.parser.parse_directory(subdir)
        self._playlists_cache[cache_key] = tracks
        return tracks
