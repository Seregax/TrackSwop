"""
Spotify API Integration Module

This module provides complete Spotify API integration for TrackSwop, including:
- OAuth2 authentication with user credentials
- Playlist management (read/write)
- Track operations
- Token management with encryption
- Specification-based configuration

Quick Start:
-----------
1. Get Spotify credentials: https://developer.spotify.com/dashboard
2. Use SpotifyServiceFactory to create a service
3. Call authenticate() - will open browser for login
4. Use the service to manage playlists and tracks

Example:
--------
from src.model.services.providers.spotify.factory import SpotifyServiceFactory

spotify = SpotifyServiceFactory.create(
    client_id="your_id",
    client_secret="your_secret"
)
spotify.authenticate()
playlists = spotify.get_playlists()

For detailed documentation, see README.md in this directory.
"""

__version__ = "1.0.0"
__author__ = "TrackSwop Team"

from src.model.services.providers.spotify.spotify_service import SpotifyService
from src.model.services.providers.spotify.factory import SpotifyServiceFactory
from src.model.services.providers.spotify.config import (
    SpotifyConfig,
    SpotifySetupWizard,
)

__all__ = [
    "SpotifyService",
    "SpotifyServiceFactory",
    "SpotifyConfig",
    "SpotifySetupWizard",
]
