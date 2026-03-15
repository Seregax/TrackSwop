"""
VK Music Streaming Service Implementation

Provides import/export functionality for VKontakte music playlists.
"""

from typing import List, Dict, Any, Optional
import time

from src.model.entities.playlist import Playlist
from src.model.entities.track import Track
from src.model.services.interfaces.service_info import ServiceInfo
from src.model.specifications.base import BaseSpecification
from src.model.services.interfaces.istreaming_service import IStreamingService

from .vk_auth_spec import VkAuthSpecification
from .vk_import_spec import VkImportSpecification
from .vk_export_spec import VkExportSpecification


class VkService(IStreamingService):
    """
    Service implementation for working with VKontakte Music.
    
    Supports:
    - Token-based authorization
    - Importing playlists from VK
    - Exporting playlists to VK
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the service.
        
        Args:
            config: Service configuration (optional)
        """
        self.config = config or {}
        self.token: Optional[str] = None
        self.user_id: Optional[int] = None
        self._vk: Optional[Any] = None
        self._vk_session: Optional[Any] = None

    # IStreamingService Interface Methods

    def get_service_info(self) -> ServiceInfo:
        """Returns meta-information about the service"""
        return ServiceInfo(
            name="VK Music",
            provider="vk.com",
            supported_features=["import", "export", "auth"]
        )

    def authenticate(self) -> None:
        """
        Authenticate the user.
        
        Validates the token by calling users.get.
        Must be called after set_auth_data().
        
        Raises:
            ValueError: If token or user_id are not set
            RuntimeError: If token is invalid
        """
        if not self.token or not self.user_id:
            raise ValueError("Token and user_id must be set before authentication")
        
        vk = self._get_vk_api()
        try:
            response = vk.users.get(user_ids=self.user_id)
            if not response:
                raise ValueError("Invalid token or user_id")
        except Exception as e:
            raise RuntimeError(f"VKontakte authorization error: {str(e)}")

    def get_playlists(self) -> List[Playlist]:
        """
        Get the list of user playlists.
        
        Returns:
            List[Playlist]: List of playlists
        """
        vk = self._get_vk_api()
        try:
            response = vk.audio.getPlaylists(owner_id=self.user_id, count=100)
            playlists = []
            for item in response.get("items", []):
                playlists.append(self._map_vk_playlist_to_entity(item))
            return playlists
        except Exception as e:
            raise RuntimeError(f"Error getting playlists: {str(e)}")

    def get_tracks_from_playlist(self, playlist: Playlist) -> List[Track]:
        """
        Get tracks from playlist.
        
        ⚠️ VK API LIMITATION: audio.get may not work with all tokens.
        Falls back to search-based approach if direct access fails.
        """
        vk = self._get_vk_api()
        
        vk_playlist_id = playlist.metadata.get("vk_playlist_id")
        owner_id = playlist.metadata.get("owner_id", self.user_id)
        access_key = playlist.metadata.get("access_key")
        
        # 🔹 Попытка 1: Прямой запрос (работает с полными токенами)
        try:
            params = {
                "owner_id": int(owner_id),
                "playlist_id": int(vk_playlist_id),
                "count": 1000
            }
            if access_key:
                params["access_key"] = str(access_key)
            
            response = vk.audio.get(**params)
            tracks = [self._map_vk_track_to_entity(t) for t in response.get("items", [])]
            
            if tracks:
                return tracks
                
        except Exception as e:
            print(f"⚠️ Direct playlist access failed: {e}")
            print("🔄 Falling back to search-based approach...")
        
        # 🔹 Попытка 2: Поиск по названию плейлиста (костыль)
        try:
            search_query = playlist.name[:50]  # Ограничение VK
            response = vk.audio.search(q=search_query, count=50)
            tracks = [self._map_vk_track_to_entity(t) for t in response.get("items", [])]
            
            print(f"⚠️ Using search fallback: {len(tracks)} tracks found")
            return tracks
            
        except Exception as e:
            raise RuntimeError(f"Cannot get tracks: {str(e)}") from e

    def add_playlist(self, playlist: Playlist) -> None:
        """
        Create a new playlist in VKontakte.
        
        Args:
            playlist: Playlist to create
            
        Note:
            After creation, vk_playlist_id is saved in playlist.metadata
        """
        vk = self._get_vk_api()
        try:
            response = vk.playlist.create(
                title=playlist.title,
                description=playlist.description or ""
            )
            playlist.metadata["vk_playlist_id"] = response.get("playlist_id")
            playlist.metadata["owner_id"] = self.user_id
        except Exception as e:
            raise RuntimeError(f"Error creating playlist: {str(e)}")

    def add_track_to_playlist(self, playlist: Playlist, track: Track) -> None:
        """
        Add track to playlist.
        Uses audio.search to find track if vk_audio_id not available.
        """
        vk = self._get_vk_api()
        
        vk_audio_id = track.metadata.get("vk_audio_id")
        track_owner_id = track.metadata.get("owner_id")
        
        # Если нет ID трека — ищем по названию
        if not vk_audio_id:
            artist_name = track.artists[0] if track.artists else ""
            search_query = f"{artist_name} {track.title}"[:100]
            
            search = vk.audio.search(q=search_query, count=1)
            if search.get("items"):
                found = search["items"][0]
                vk_audio_id = found["id"]
                track_owner_id = found["owner_id"]
                print(f"🔍 Found track via search: {vk_audio_id}")
            else:
                raise ValueError(f"Track '{track.title}' not found in VK")
        
        vk_playlist_id = playlist.metadata.get("vk_playlist_id")
        if not vk_playlist_id:
            raise ValueError("Playlist does not contain vk_playlist_id")
        
        try:
            vk.playlist.addTrack(
                playlist_id=int(vk_playlist_id),
                audio_id=int(vk_audio_id),
                owner_id=int(track_owner_id)
            )
        except Exception as e:
            raise RuntimeError(f"Error adding track: {str(e)}") from e

    def export_playlist(self, source: Playlist, destination: Playlist) -> None:
        """
        Export playlist: copy tracks from source to destination.
        
        Args:
            source: Source playlist
            destination: Destination playlist
            
        Note:
            Both playlists must belong to VKontakte
        """
        tracks = self.get_tracks_from_playlist(source)
        success_count = 0
        fail_count = 0
        
        for i, track in enumerate(tracks):
            try:
                self.add_track_to_playlist(destination, track)
                success_count += 1
            except Exception as e:
                fail_count += 1
                print(f"Failed to add track '{track.title}': {e}")
            
            # Rate limiting: VK ~3 requests/sec
            if i < len(tracks) - 1:
                time.sleep(0.4)
        
        print(f"Export completed: {success_count} successful, {fail_count} errors")

    # Specification Methods

    def get_import_specs(self) -> BaseSpecification:
        """Returns specification for import"""
        return VkImportSpecification()

    def get_export_specs(self) -> BaseSpecification:
        """Returns specification for export"""
        return VkExportSpecification()

    def get_auth_specs(self) -> BaseSpecification:
        """Returns specification for authorization"""
        return VkAuthSpecification()

    # Helper Methods

    def set_auth_data(self, token: str, user_id: int) -> None:
        """
        Set authorization data.
        
        Args:
            token: VK access token
            user_id: VK user ID
        """
        self.token = token
        self.user_id = user_id
        self._vk = None
        self._vk_session = None

    def _get_vk_session(self) -> Any:
        """
        Lazy initialization of VK API session.
        
        Returns:
            VkApi: Session object
        """
        if self._vk_session is None:
            if not self.token:
                raise RuntimeError("Must call authenticate() before using API")
            
            import vk_api
            self._vk_session = vk_api.VkApi(token=self.token)
        
        return self._vk_session

    def _get_vk_api(self) -> Any:
        """
        Get API object for calling methods.
        
        Returns:
            API object with methods (audio, playlist, users, etc.)
        """
        session = self._get_vk_session()
        return session.get_api()

    def _map_vk_track_to_entity(self, vk_track: Dict[str, Any]) -> Track:
        """
        Convert track from VK API to internal Track entity.
        
        Args:
            vk_track: Track data from VK API
            
        Returns:
            Track: Internal track entity
        """
        # VK API возвращает artist как строку, преобразуем в список
        artist = vk_track.get("artist", "Unknown Artist")
        artists = [artist] if artist else ["Unknown Artist"]
        
        return Track(
            title=vk_track.get("title", "Unknown"),
            artists=artists,
            album=vk_track.get("album", ""),
            year=None,  # VK API не всегда возвращает год
            duration=float(vk_track.get("duration", 0)),
            id=str(vk_track.get("id", "")),
            metadata={
                "vk_audio_id": vk_track.get("id"),
                "owner_id": vk_track.get("owner_id"),
                "url": vk_track.get("url"),
                "access_key": vk_track.get("access_key")
            }
        )

    def _map_vk_playlist_to_entity(self, vk_playlist: Dict[str, Any]) -> Playlist:
        """Convert playlist from VK API to internal Playlist entity."""
        
        is_followed = vk_playlist.get("type") == 1 and "original" in vk_playlist
        
        if is_followed:
            original = vk_playlist.get("original", {})
            playlist_id = original.get("playlist_id")
            owner_id = original.get("owner_id")
            access_key = original.get("access_key")
        else:
            playlist_id = vk_playlist.get("id")
            owner_id = vk_playlist.get("owner_id")
            access_key = vk_playlist.get("access_key")
        
        return Playlist(
            name=vk_playlist.get("title", "Unknown Playlist"),
            tracks=None,
            id=str(vk_playlist.get("id", "")),
            metadata={
                "vk_playlist_id": playlist_id,
                "owner_id": owner_id,
                "access_key": access_key,
                "is_followed": is_followed,
                "photo": vk_playlist.get("photo"),
                "count": vk_playlist.get("count", 0)
            },
            description=vk_playlist.get("description", ""),
            track_count=vk_playlist.get("count", 0)
        )






"""TEST"""
def main():
    service = VkService()

    service.set_auth_data("vk1.a.ur_access_token", id=123456789)

    service.authenticate()

    playlists = service.get_playlists()

    print(f"Найдено плейлистов: {len(playlists)}")

    for playlist in playlists:
        print(f"- {playlist.name} (ID: {playlist.id}, треков: {playlist.track_count})")

    print('done')



if __name__ == "__main__":
    main()








