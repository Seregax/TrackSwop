"""Tests for Spotify service"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.model.services.providers.spotify.spotify_service import (
    SpotifyService,
    SpotifyAuthSpec,
    SpotifyImportSpec,
    SpotifyExportSpec,
)
from src.model.entities.playlist import Playlist
from src.model.entities.track import Track
from src.model.store.token_store import TokenStore


class TestSpotifyService(unittest.TestCase):
    """Test cases for SpotifyService"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_token_store = Mock(spec=TokenStore)
        self.spotify_service = SpotifyService(
            client_id="test_client_id",
            client_secret="test_client_secret",
            redirect_uri="http://localhost:8888/callback",
            token_store=self.mock_token_store,
        )

    def test_get_service_info(self):
        """Test get_service_info method"""
        info = self.spotify_service.get_service_info()
        self.assertEqual(info.name, "Spotify")
        self.assertTrue(info.icon_path)

    @patch("spotipy.Spotify")
    def test_authenticate_with_cached_token(self, mock_spotify_class):
        """Test authentication with cached token"""
        mock_token = "cached_access_token"
        self.mock_token_store.get_token.return_value = mock_token

        mock_sp_instance = MagicMock()
        mock_spotify_class.return_value = mock_sp_instance

        self.spotify_service.authenticate()

        self.mock_token_store.get_token.assert_called_with("spotify")
        self.assertIsNotNone(self.spotify_service.sp)

    def test_get_auth_specs(self):
        """Test get_auth_specs returns SpotifyAuthSpec"""
        specs = self.spotify_service.get_auth_specs()
        self.assertIsInstance(specs, SpotifyAuthSpec)
        fields = specs.get_fields()
        self.assertTrue(len(fields) > 0)
        self.assertEqual(fields[0].name, "client_id")

    def test_get_import_specs(self):
        """Test get_import_specs returns SpotifyImportSpec"""
        specs = self.spotify_service.get_import_specs()
        self.assertIsInstance(specs, SpotifyImportSpec)

    def test_get_export_specs(self):
        """Test get_export_specs returns SpotifyExportSpec"""
        specs = self.spotify_service.get_export_specs()
        self.assertIsInstance(specs, SpotifyExportSpec)

    @patch("spotipy.Spotify")
    def test_get_playlists_requires_authentication(self, mock_spotify_class):
        """Test that get_playlists raises exception without authentication"""
        with self.assertRaises(Exception):
            self.spotify_service.get_playlists()

    @patch("spotipy.Spotify")
    def test_get_playlists_success(self, mock_spotify_class):
        """Test successful playlist retrieval"""
        self.spotify_service.sp = MagicMock()
        self.spotify_service.sp.current_user_playlists.return_value = {
            "items": [
                {"name": "Playlist 1", "id": "id1"},
                {"name": "Playlist 2", "id": "id2"},
            ],
            "next": None,
        }

        playlists = self.spotify_service.get_playlists()

        self.assertEqual(len(playlists), 2)
        self.assertEqual(playlists[0].name, "Playlist 1")
        self.assertEqual(playlists[1].name, "Playlist 2")

    @patch("spotipy.Spotify")
    def test_parse_spotify_track(self, mock_spotify_class):
        """Test parsing spotify track response"""
        spotify_track = {
            "name": "Test Song",
            "artists": [{"name": "Test Artist"}],
            "album": {"name": "Test Album", "release_date": "2024-01-01"},
            "duration_ms": 180000,
        }

        track = self.spotify_service._parse_spotify_track(spotify_track)

        self.assertEqual(track.title, "Test Song")
        self.assertEqual(track.artists, ["Test Artist"])
        self.assertEqual(track.album, "Test Album")
        self.assertEqual(track.year, 2024)
        self.assertEqual(track.duration, 180.0)

    def test_parse_spotify_track_with_missing_data(self):
        """Test parsing track with missing optional fields"""
        spotify_track = {
            "name": "Minimal Song",
            "artists": [],
        }

        track = self.spotify_service._parse_spotify_track(spotify_track)

        self.assertEqual(track.title, "Minimal Song")
        self.assertEqual(track.artists, [])
        self.assertIsNone(track.album)
        self.assertIsNone(track.year)


class TestSpotifyAuthSpec(unittest.TestCase):
    """Test cases for SpotifyAuthSpec"""

    def setUp(self):
        """Set up test fixtures"""
        self.spec = SpotifyAuthSpec()

    def test_auth_spec_fields(self):
        """Test that auth spec has required fields"""
        fields = self.spec.get_fields()
        field_names = [f.name for f in fields]

        self.assertIn("client_id", field_names)
        self.assertIn("client_secret", field_names)
        self.assertIn("redirect_uri", field_names)

    def test_client_secret_is_password_field(self):
        """Test that client_secret is a password field"""
        fields = self.spec.get_fields()
        secret_field = next(f for f in fields if f.name == "client_secret")
        self.assertEqual(secret_field.field_type.value, "password")

    def test_redirect_uri_has_default(self):
        """Test that redirect_uri has a default value"""
        fields = self.spec.get_fields()
        redirect_field = next(f for f in fields if f.name == "redirect_uri")
        self.assertIsNotNone(redirect_field.default)


if __name__ == "__main__":
    unittest.main()
