"""Spotify service factory"""

from typing import Optional
from src.model.services.providers.spotify.spotify_service import SpotifyService
from src.model.store.token_store import TokenStore


class SpotifyServiceFactory:
    """Factory for creating Spotify service instances"""

    @staticmethod
    def create(
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://127.0.0.1:8888/callback",
        token_store: Optional[TokenStore] = None,
    ) -> SpotifyService:
        """
        Create a Spotify service instance.

        Args:
            client_id: Spotify app client ID
            client_secret: Spotify app client secret
            redirect_uri: OAuth2 redirect URI (default: 127.0.0.1:8888)
            token_store: TokenStore instance (optional)

        Returns:
            SpotifyService instance
        """
        return SpotifyService(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            token_store=token_store,
        )
