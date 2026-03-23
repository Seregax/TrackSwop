from typing import List, Optional, Dict, Any
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

from src.model.entities.playlist import Playlist
from src.model.entities.track import Track
from src.model.services.interfaces.istreaming_service import IStreamingService
from src.model.services.interfaces.service_info import ServiceInfo
from src.model.specifications.base import BaseSpecification, Field, FieldType
from src.model.store.token_store import TokenStore
from src.common.logger import get_logger

logger = get_logger(__name__)


class SpotifyAuthSpec(BaseSpecification):
    """Spotify authentication specification"""

    def get_fields(self) -> List[Field]:
        return [
            Field(
                name="client_id",
                label="Spotify Client ID",
                field_type=FieldType.STRING,
                required=True,
                placeholder="Your Spotify Client ID",
                help_text="Get from https://developer.spotify.com/dashboard",
            ),
            Field(
                name="client_secret",
                label="Spotify Client Secret",
                field_type=FieldType.PASSWORD,
                required=True,
                placeholder="Your Spotify Client Secret",
            ),
            Field(
                name="redirect_uri",
                label="Redirect URI",
                field_type=FieldType.STRING,
                required=False,
                default="http://127.0.0.1:8888/callback",
                placeholder="http://127.0.0.1:8888/callback",
            ),
        ]


class SpotifyImportSpec(BaseSpecification):
    """Spotify import specification"""

    def get_fields(self) -> List[Field]:
        return [
            Field(
                name="playlist_name",
                label="Target Playlist",
                field_type=FieldType.STRING,
                required=True,
                placeholder="My Imported Playlist",
            ),
        ]


class SpotifyExportSpec(BaseSpecification):
    """Spotify export specification"""

    def get_fields(self) -> List[Field]:
        return [
            Field(
                name="playlist_name",
                label="Source Playlist",
                field_type=FieldType.STRING,
                required=True,
                placeholder="My Playlist",
            ),
        ]


class SpotifyService(IStreamingService):
    """Spotify streaming service implementation with user credentials authentication"""

    SERVICE_NAME = "spotify"
    SCOPES = [
        "playlist-read-private",
        "playlist-read-collaborative",
        "playlist-modify-public",
        "playlist-modify-private",
    ]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://127.0.0.1:8888/callback",
        token_store: Optional[TokenStore] = None,
    ):
        """
        Initialize Spotify service with credentials.

        Args:
            client_id: Spotify app client ID
            client_secret: Spotify app client secret
            redirect_uri: OAuth2 redirect URI
            token_store: TokenStore instance for saving tokens
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.token_store = token_store or TokenStore()
        self.sp: Optional[spotipy.Spotify] = None
        self.username: Optional[str] = None

    def get_service_info(self) -> ServiceInfo:
        """Get service information"""
        return ServiceInfo(
            name="Spotify",
            icon_path="resources/icons/spotify.png",
        )

    def authenticate(self) -> None:
        """
        Authenticate with Spotify using OAuth2 flow.
        Saves the token to TokenStore for future use.
        """
        try:
            # Check if we have a cached token
            cached_token = self.token_store.get_token(self.SERVICE_NAME)

            if cached_token:
                logger.info("Using cached Spotify token")
                self.sp = spotipy.Spotify(auth=cached_token)
                # Verify token is still valid
                self._verify_token()
                return

            # Create OAuth2 handler
            auth_manager = SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope=self.SCOPES,
            )

            # Get the token (this will open browser for user to authenticate)
            token_info = auth_manager.get_access_token()

            if not token_info:
                raise Exception("Failed to obtain Spotify access token")

            access_token = token_info.get("access_token")
            if not access_token:
                raise Exception("No access token in response")

            # Save token for future use
            self.token_store.save_token(self.SERVICE_NAME, access_token)

            # Create Spotify client
            self.sp = spotipy.Spotify(auth=access_token)

            # Get username for reference
            self.username = self.sp.current_user()["display_name"]
            logger.info(f"Successfully authenticated as {self.username}")

        except Exception as e:
            logger.error(f"Spotify authentication failed: {str(e)}")
            raise

    def _verify_token(self) -> None:
        """Verify that cached token is still valid"""
        try:
            if self.sp:
                self.sp.current_user()
        except spotipy.exceptions.SpotifyException:
            logger.warning("Cached token is invalid, clearing it")
            self.token_store.delete_token(self.SERVICE_NAME)
            self.sp = None
            raise

    def get_playlists(self) -> List[Playlist]:
        """Get all user playlists"""
        if not self.sp:
            raise Exception("Not authenticated. Call authenticate() first.")

        try:
            playlists: List[Playlist] = []
            results = self.sp.current_user_playlists()

            while results:
                for item in results["items"]:
                    playlist = Playlist(
                        name=item["name"],
                        tracks=None,  # Will be loaded on demand
                    )
                    playlists.append(playlist)

                # Handle pagination
                if results["next"]:
                    results = self.sp.next(results)
                else:
                    break

            logger.info(f"Retrieved {len(playlists)} playlists from Spotify")
            return playlists

        except Exception as e:
            logger.error(f"Failed to get playlists: {str(e)}")
            raise

    def get_tracks_from_playlist(self, playlist: Playlist) -> List[Track]:
        """Get all tracks from a specific playlist"""
        if not self.sp:
            raise Exception("Not authenticated. Call authenticate() first.")

        try:
            tracks: List[Track] = []

            # Find playlist ID by name
            playlist_id = self._find_playlist_id(playlist.name)
            if not playlist_id:
                raise ValueError(f"Playlist '{playlist.name}' not found")

            # Get tracks from playlist with pagination
            results = self.sp.playlist_tracks(playlist_id)

            while results:
                for item in results["items"]:
                    # Handle cases where track is None (e.g., local tracks, unavailable tracks)
                    if item.get("track") is None:
                        logger.debug(f"Skipping unavailable track in '{playlist.name}'")
                        continue
                    
                    track = self._parse_spotify_track(item["track"])
                    if track:
                        tracks.append(track)

                # Handle pagination
                if results["next"]:
                    results = self.sp.next(results)
                else:
                    break

            logger.info(
                f"Retrieved {len(tracks)} tracks from playlist '{playlist.name}'"
            )
            return tracks

        except ValueError as e:
            logger.error(f"Invalid playlist: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to get tracks from playlist: {str(e)}")
            raise

    def add_playlist(self, playlist: Playlist) -> None:
        """Create new playlist"""
        if not self.sp:
            raise Exception("Not authenticated. Call authenticate() first.")

        try:
            current_user = self.sp.current_user()
            self.sp.user_playlist_create(
                user=current_user["id"],
                name=playlist.name,
                public=False,
            )
            logger.info(f"Created playlist '{playlist.name}'")
        except Exception as e:
            logger.error(f"Failed to create playlist: {str(e)}")
            raise

    def add_track_to_playlist(self, playlist: Playlist, track: Track) -> None:
        """Add track to playlist"""
        if not self.sp:
            raise Exception("Not authenticated. Call authenticate() first.")

        try:
            # Find playlist ID
            playlist_id = self._find_playlist_id(playlist.name)
            if not playlist_id:
                raise ValueError(f"Playlist '{playlist.name}' not found")

            # Search for track
            track_id = self._find_track_id(track)
            if not track_id:
                logger.warning(f"Track '{track.title}' not found on Spotify")
                return

            self.sp.playlist_add_items(playlist_id, [track_id])
            logger.info(f"Added '{track.title}' to '{playlist.name}'")

        except Exception as e:
            logger.error(f"Failed to add track to playlist: {str(e)}")
            raise

    def export_playlist(self, source: Playlist, destination: Playlist) -> None:
        """Export playlist from Spotify to another service"""
        if not self.sp:
            raise Exception("Not authenticated. Call authenticate() first.")

        try:
            # Get tracks from source
            tracks = self.get_tracks_from_playlist(source)

            # These would be implemented by the destination service
            logger.info(
                f"Ready to export {len(tracks)} tracks from '{source.name}' "
                f"to '{destination.name}'"
            )

        except Exception as e:
            logger.error(f"Failed to export playlist: {str(e)}")
            raise

    def get_import_specs(self) -> BaseSpecification:
        """Get import specifications"""
        return SpotifyImportSpec()

    def get_export_specs(self) -> BaseSpecification:
        """Get export specifications"""
        return SpotifyExportSpec()

    def get_auth_specs(self) -> BaseSpecification:
        """Get authentication specifications"""
        return SpotifyAuthSpec()

    # Helper methods

    def _find_playlist_id(self, playlist_name: str) -> Optional[str]:
        """Find Spotify playlist ID by name"""
        results = self.sp.current_user_playlists()

        while results:
            for item in results["items"]:
                if item["name"].lower() == playlist_name.lower():
                    return item["id"]

            if results["next"]:
                results = self.sp.next(results)
            else:
                break

        return None

    def _find_track_id(self, track: Track) -> Optional[str]:
        """Find Spotify track ID by track info"""
        try:
            query = f"track:{track.title}"
            if track.artists:
                query += f" artist:{track.artists[0]}"

            results = self.sp.search(q=query, type="track", limit=1)

            if results["tracks"]["items"]:
                return results["tracks"]["items"][0]["id"]

            return None

        except Exception as e:
            logger.error(f"Failed to search for track: {str(e)}")
            return None

    def _parse_spotify_track(self, spotify_track: dict) -> Optional[Track]:
        """Parse Spotify track response to Track entity"""
        try:
            if not spotify_track:
                return None

            return Track(
                title=spotify_track.get("name", ""),
                artists=[
                    artist["name"] for artist in spotify_track.get("artists", [])
                ],
                album=spotify_track.get("album", {}).get("name"),
                year=int(
                    spotify_track.get("album", {})
                    .get("release_date", "")[:4]
                )
                if spotify_track.get("album", {}).get("release_date")
                else None,
                duration=spotify_track.get("duration_ms", 0) / 1000 if spotify_track.get("duration_ms") else None,
            )
        except Exception as e:
            logger.error(f"Failed to parse Spotify track: {str(e)}")
            return None
