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

from src.common.logger import get_logger

logger = get_logger(__name__)

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
        self._playlist_metadata: Dict[str, Dict[str, Any]] = {}  # Кэш метаданных плейлистов
        self._track_metadata: Dict[str, Dict[str, Any]] = {}  # Кэш метаданных треков

    # IStreamingService Interface Methods

    def get_service_info(self) -> ServiceInfo:
        """Returns meta-information about the service"""
        return ServiceInfo(
            name="VK Music",
            icon_path=None,
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
            logger.error(f"VKontakte authorization error: {str(e)}")
            raise RuntimeError(f"VKontakte authorization error: {str(e)}")

    def get_playlists(self) -> List[Playlist]:
        """
        Get the list of user playlists.

        Returns:
            List[Playlist]: List of playlists
        """
        vk = self._get_vk_api()
        try:
            response = vk.audio.getPlaylists(owner_id=int(self.user_id), count=100)
            playlists = []
            for item in response.get("items", []):
                playlist = self._map_vk_playlist_to_entity(item)
                playlists.append(playlist)
            
            # Сохраняем метаданные для всех плейлистов
            self._save_playlist_metadata(response.get("items", []))
            
            return playlists
        except Exception as e:
            logger.error(f"Error getting playlists: {str(e)}")
            raise RuntimeError(f"Error getting playlists: {str(e)}")
    
    def _save_playlist_metadata(self, vk_playlists: List[Dict[str, Any]]):
        """
        Save playlist metadata for later use.
        
        Args:
            vk_playlists: List of playlist data from VK API
        """
        for item in vk_playlists:
            playlist_id = item.get("id")
            owner_id = item.get("owner_id")
            access_key = item.get("access_key")
            title = item.get("title", "Unknown Playlist")
            
            # Сохраняем метаданные по названию (ключ)
            self._playlist_metadata[title] = {
                "vk_playlist_id": playlist_id,
                "owner_id": owner_id,
                "access_key": access_key,
                "photo": item.get("photo"),
                "count": item.get("count", 0)
            }

    def get_tracks_from_playlist(self, playlist: Playlist) -> List[Track]:
        """
        Get tracks from playlist.

        VK API LIMITATION: audio.get may not work with all tokens.
        Falls back to search-based approach if direct access fails.
        """
        vk = self._get_vk_api()

        # Получаем метаданные плейлиста по названию
        metadata = self._playlist_metadata.get(playlist.name, {})

        vk_playlist_id = metadata.get("vk_playlist_id")
        owner_id = metadata.get("owner_id", self.user_id)
        access_key = metadata.get("access_key")

        # 🔹 Попытка 1: Прямой запрос (работает с полными токенами)
        if vk_playlist_id:
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
                logger.exception("Ignored exception occurred")
                # Fallback to search
                pass

        # 🔹 Попытка 2: Поиск по названию плейлиста (костыль)
        try:
            search_query = playlist.name[:50]  # Ограничение VK
            response = vk.audio.search(q=search_query, count=50)
            tracks = [self._map_vk_track_to_entity(t) for t in response.get("items", [])]
            return tracks

        except Exception as e:

            logger.exception(f"Cannot get tracks: {str(e)}") from e
            raise RuntimeError(f"Cannot get tracks: {str(e)}") from e

    def add_playlist(self, playlist: Playlist) -> None:
        """
        Create a new playlist in VKontakte.

        Args:
            playlist: Playlist to create

        Note:
            After creation, vk_playlist_id is saved in internal cache
        """
        vk = self._get_vk_api()
        try:
            response = vk.playlist.create(
                title=playlist.name,
                description=""
            )
            playlist_id = response.get("playlist_id")
            
            # Сохраняем метаданные во внутренний кэш
            self._playlist_metadata[playlist.name] = {
                "vk_playlist_id": playlist_id,
                "owner_id": self.user_id,
            }
        except Exception as e:

            logger.exception(f"Error creating playlist: {str(e)}")
            raise RuntimeError(f"Error creating playlist: {str(e)}")

    def add_track_to_playlist(self, playlist: Playlist, track: Track) -> None:
        """
        Add track to playlist.
        Uses audio.search to find track if vk_audio_id not available.
        """
        vk = self._get_vk_api()

        # Ищем метаданные трека по названию и артисту
        track_key = f"{track.title}_{track.artists[0] if track.artists else ''}"
        track_meta = self._track_metadata.get(track_key, {})
        
        vk_audio_id = track_meta.get("vk_audio_id")
        track_owner_id = track_meta.get("owner_id")

        # Если нет ID трека — ищем по названию
        if not vk_audio_id:
            artist_name = track.artists[0] if track.artists else ""
            search_query = f"{artist_name} {track.title}"[:100]

            search = vk.audio.search(q=search_query, count=1)
            if search.get("items"):
                found = search["items"][0]
                vk_audio_id = found["id"]
                track_owner_id = found["owner_id"]
                
                # Сохраняем метаданные трека
                self._track_metadata[track_key] = {
                    "vk_audio_id": vk_audio_id,
                    "owner_id": track_owner_id,
                }
                logger.info(f"🔍 Found track via search: {vk_audio_id}")
            else:
                raise ValueError(f"Track '{track.title}' not found in VK")

        # Получаем метаданные плейлиста
        playlist_meta = self._playlist_metadata.get(playlist.name, {})
        vk_playlist_id = playlist_meta.get("vk_playlist_id")
        
        if not vk_playlist_id:
            raise ValueError("Playlist does not have vk_playlist_id")

        try:
            vk.audio.add(
                album_id=int(vk_playlist_id),
                audio_id=int(vk_audio_id),
                owner_id=int(track_owner_id)
            )
        except Exception as e:

            logger.exception(f"Error adding track: {str(e)}") from e
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
                logger.info(f"Failed to add track '{track.title}': {e}")
            
            # Rate limiting: VK ~3 requests/sec
            if i < len(tracks) - 1:
                time.sleep(0.4)
        
        logger.info(f"Export completed: {success_count} successful, {fail_count} errors")

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

        # Извлекаем год из даты, если есть
        year = None
        if "date" in vk_track and vk_track["date"]:
            try:
                import datetime
                dt = datetime.datetime.fromtimestamp(int(vk_track["date"]))
                year = dt.year
            except (ValueError, OSError) as e:
                logger.exception("Ignored ValueError or OSError")

        track = Track(
            title=vk_track.get("title", "Unknown"),
            artists=artists,
            album=vk_track.get("album", "") or None,
            year=year,
            duration=float(vk_track.get("duration", 0)) if vk_track.get("duration") else None,
        )
        
        # Сохраняем метаданные трека во внутренний кэш
        track_key = f"{track.title}_{artists[0]}"
        self._track_metadata[track_key] = {
            "vk_audio_id": vk_track.get("id"),
            "owner_id": vk_track.get("owner_id"),
            "url": vk_track.get("url"),
            "access_key": vk_track.get("access_key")
        }
        
        return track

    def _map_vk_playlist_to_entity(self, vk_playlist: Dict[str, Any]) -> Playlist:
        """Convert playlist from VK API to internal Playlist entity."""
        
        playlist_id = vk_playlist.get("id")
        owner_id = vk_playlist.get("owner_id")
        access_key = vk_playlist.get("access_key")
        
        # Создаём Playlist только с базовыми полями
        playlist = Playlist(
            name=vk_playlist.get("title", "Unknown Playlist"),
            tracks=None,
        )
        
        # Сохраняем метаданные в отдельном словаре (для внутреннего использования)
        # Используем название плейлиста как ключ (упрощение)
        self._playlist_metadata[playlist.name] = {
            "vk_playlist_id": playlist_id,
            "owner_id": owner_id,
            "access_key": access_key,
            "photo": vk_playlist.get("photo"),
            "count": vk_playlist.get("count", 0)
        }
        
        return playlist