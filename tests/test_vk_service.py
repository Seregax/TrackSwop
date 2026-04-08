"""Tests for VK Music service"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.model.services.providers.vk.vk_service import VkService
from src.model.services.providers.vk.vk_auth_spec import VkAuthSpecification
from src.model.services.providers.vk.vk_import_spec import VkImportSpecification
from src.model.services.providers.vk.vk_export_spec import VkExportSpecification
from src.model.entities.playlist import Playlist
from src.model.entities.track import Track


class TestVkService(unittest.TestCase):
    """Test cases for VkService"""

    def setUp(self):
        """Set up test fixtures"""
        self.vk_service = VkService()
        self.test_token = "test_vk_token_123"
        self.test_user_id = 123456789

    def test_get_service_info(self):
        """Test get_service_info method"""
        info = self.vk_service.get_service_info()
        self.assertEqual(info.name, "VK Music")

    def test_set_auth_data(self):
        """Test set_auth_data stores token and user_id"""
        self.vk_service.set_auth_data(self.test_token, self.test_user_id)
        
        self.assertEqual(self.vk_service.token, self.test_token)
        self.assertEqual(self.vk_service.user_id, self.test_user_id)

    def test_authenticate_requires_token(self):
        """Test authenticate raises exception without token"""
        with self.assertRaises(ValueError) as context:
            self.vk_service.authenticate()
        
        self.assertIn("Token and user_id must be set", str(context.exception))

    def test_authenticate_requires_user_id(self):
        """Test authenticate raises exception without user_id"""
        self.vk_service.token = self.test_token
        
        with self.assertRaises(ValueError) as context:
            self.vk_service.authenticate()
        
        self.assertIn("Token and user_id must be set", str(context.exception))

    @patch.object(VkService, '_get_vk_api')
    def test_authenticate_success(self, mock_get_vk_api):
        """Test successful authentication"""
        mock_api = MagicMock()
        mock_api.users.get.return_value = [{"id": self.test_user_id, "first_name": "Test"}]
        mock_get_vk_api.return_value = mock_api
        
        self.vk_service.set_auth_data(self.test_token, self.test_user_id)
        self.vk_service.authenticate()
        
        mock_api.users.get.assert_called_with(user_ids=self.test_user_id)

    @patch.object(VkService, '_get_vk_api')
    def test_authenticate_invalid_token(self, mock_get_vk_api):
        """Test authentication with invalid token"""
        mock_api = MagicMock()
        mock_api.users.get.return_value = []
        mock_get_vk_api.return_value = mock_api
        
        self.vk_service.set_auth_data(self.test_token, self.test_user_id)
        
        with self.assertRaises(RuntimeError):
            self.vk_service.authenticate()

    @patch.object(VkService, '_get_vk_api')
    def test_authenticate_api_error(self, mock_get_vk_api):
        """Test authentication with API error"""
        mock_api = MagicMock()
        mock_api.users.get.side_effect = Exception("API Error")
        mock_get_vk_api.return_value = mock_api
        
        self.vk_service.set_auth_data(self.test_token, self.test_user_id)
        
        with self.assertRaises(RuntimeError):
            self.vk_service.authenticate()

    def test_get_auth_specs(self):
        """Test get_auth_specs returns VkAuthSpecification"""
        specs = self.vk_service.get_auth_specs()
        self.assertIsInstance(specs, VkAuthSpecification)
        
        fields = specs.get_fields()
        self.assertTrue(len(fields) > 0)
        
        field_names = [f.name for f in fields]
        self.assertIn("token", field_names)
        self.assertIn("user_id", field_names)

    def test_get_import_specs(self):
        """Test get_import_specs returns VkImportSpecification"""
        specs = self.vk_service.get_import_specs()
        self.assertIsInstance(specs, VkImportSpecification)

    def test_get_export_specs(self):
        """Test get_export_specs returns VkExportSpecification"""
        specs = self.vk_service.get_export_specs()
        self.assertIsInstance(specs, VkExportSpecification)

    @patch.object(VkService, '_get_vk_api')
    def test_get_playlists_success(self, mock_get_vk_api):
        """Test successful playlist retrieval"""
        mock_api = MagicMock()
        mock_api.audio.getPlaylists.return_value = {
            "items": [
                {
                    "id": "playlist1",
                    "owner_id": self.test_user_id,
                    "title": "Favorites",
                    "count": 10,
                    "photo": None,
                    "access_key": None
                },
                {
                    "id": "playlist2",
                    "owner_id": self.test_user_id,
                    "title": "Rock Hits",
                    "count": 20,
                    "photo": None,
                    "access_key": "abc123"
                }
            ],
            "next": None
        }
        mock_get_vk_api.return_value = mock_api
        
        self.vk_service.set_auth_data(self.test_token, self.test_user_id)
        playlists = self.vk_service.get_playlists()
        
        self.assertEqual(len(playlists), 2)
        self.assertEqual(playlists[0].name, "Favorites")
        self.assertEqual(playlists[1].name, "Rock Hits")

    @patch.object(VkService, '_get_vk_api')
    def test_get_playlists_empty(self, mock_get_vk_api):
        """Test getting playlists when none exist"""
        mock_api = MagicMock()
        mock_api.audio.getPlaylists.return_value = {"items": [], "next": None}
        mock_get_vk_api.return_value = mock_api
        
        self.vk_service.set_auth_data(self.test_token, self.test_user_id)
        playlists = self.vk_service.get_playlists()
        
        self.assertEqual(len(playlists), 0)

    @patch.object(VkService, '_get_vk_api')
    def test_get_playlists_api_error(self, mock_get_vk_api):
        """Test error handling in get_playlists"""
        mock_api = MagicMock()
        mock_api.audio.getPlaylists.side_effect = Exception("API Error")
        mock_get_vk_api.return_value = mock_api
        
        self.vk_service.set_auth_data(self.test_token, self.test_user_id)
        
        with self.assertRaises(RuntimeError):
            self.vk_service.get_playlists()

    @patch.object(VkService, '_get_vk_api')
    def test_get_tracks_from_playlist_direct_access(self, mock_get_vk_api):
        """Test getting tracks from playlist with direct API access"""
        mock_api = MagicMock()
        mock_api.audio.get.return_value = {
            "items": [
                {
                    "id": "123",
                    "owner_id": self.test_user_id,
                    "title": "Song 1",
                    "artist": "Artist 1",
                    "album": "Album 1",
                    "duration": 180
                },
                {
                    "id": "124",
                    "owner_id": self.test_user_id,
                    "title": "Song 2",
                    "artist": "Artist 2",
                    "duration": 200
                }
            ]
        }
        mock_get_vk_api.return_value = mock_api
        
        self.vk_service.set_auth_data(self.test_token, self.test_user_id)
        self.vk_service._playlist_metadata["Test Playlist"] = {
            "vk_playlist_id": 1,
            "owner_id": self.test_user_id,
            "access_key": None
        }
        
        playlist = Playlist(name="Test Playlist", tracks=None)
        tracks = self.vk_service.get_tracks_from_playlist(playlist)
        
        self.assertEqual(len(tracks), 2)
        self.assertEqual(tracks[0].title, "Song 1")
        self.assertEqual(tracks[0].artists, ["Artist 1"])
        self.assertEqual(tracks[1].title, "Song 2")

    @patch.object(VkService, '_get_vk_api')
    def test_get_tracks_from_playlist_fallback_to_search(self, mock_get_vk_api):
        """Test getting tracks with fallback to search when direct access fails"""
        mock_api = MagicMock()
        mock_api.audio.get.side_effect = Exception("Direct access failed")
        mock_api.audio.search.return_value = {
            "items": [
                {
                    "id": "125",
                    "owner_id": self.test_user_id,
                    "title": "Searched Song",
                    "artist": "Searched Artist",
                    "duration": 250
                }
            ]
        }
        mock_get_vk_api.return_value = mock_api
        
        self.vk_service.set_auth_data(self.test_token, self.test_user_id)
        self.vk_service._playlist_metadata["Search Playlist"] = {
            "vk_playlist_id": 2,
            "owner_id": self.test_user_id,
            "access_key": None
        }
        
        playlist = Playlist(name="Search Playlist", tracks=None)
        tracks = self.vk_service.get_tracks_from_playlist(playlist)
        
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].title, "Searched Song")

    @patch.object(VkService, '_get_vk_api')
    def test_add_track_to_playlist(self, mock_get_vk_api):
        """Test adding track to playlist"""
        mock_api = MagicMock()
        mock_get_vk_api.return_value = mock_api
        
        self.vk_service.set_auth_data(self.test_token, self.test_user_id)
        self.vk_service._playlist_metadata["My Playlist"] = {
            "vk_playlist_id": 123,
            "owner_id": self.test_user_id,
            "access_key": None
        }
        self.vk_service._track_metadata["Song A_Artist A"] = {
            "vk_audio_id": 456,
            "owner_id": self.test_user_id
        }
        
        playlist = Playlist(name="My Playlist", tracks=None)
        track = Track(title="Song A", artists=["Artist A"], album=None, year=None, duration=180)
        
        self.vk_service.add_track_to_playlist(playlist, track)
        
        mock_api.audio.add.assert_called_once()

    @patch.object(VkService, '_get_vk_api')
    def test_add_track_to_playlist_with_search(self, mock_get_vk_api):
        """Test adding track to playlist when track not found in metadata"""
        mock_api = MagicMock()
        mock_api.audio.search.return_value = {
            "items": [
                {
                    "id": 789,
                    "owner_id": self.test_user_id,
                    "title": "Song B",
                    "artist": "Artist B"
                }
            ]
        }
        mock_get_vk_api.return_value = mock_api
        
        self.vk_service.set_auth_data(self.test_token, self.test_user_id)
        self.vk_service._playlist_metadata["My Playlist"] = {
            "vk_playlist_id": 123,
            "owner_id": self.test_user_id,
            "access_key": None
        }
        
        playlist = Playlist(name="My Playlist", tracks=None)
        track = Track(title="Song B", artists=["Artist B"], album=None, year=None, duration=200)
        
        self.vk_service.add_track_to_playlist(playlist, track)
        
        mock_api.audio.search.assert_called_once()
        mock_api.audio.add.assert_called_once()

    @patch.object(VkService, '_get_vk_api')
    def test_add_track_to_playlist_track_not_found(self, mock_get_vk_api):
        """Test error when track is not found"""
        mock_api = MagicMock()
        mock_api.audio.search.return_value = {"items": []}
        mock_get_vk_api.return_value = mock_api
        
        self.vk_service.set_auth_data(self.test_token, self.test_user_id)
        self.vk_service._playlist_metadata["My Playlist"] = {
            "vk_playlist_id": 123,
            "owner_id": self.test_user_id,
            "access_key": None
        }
        
        playlist = Playlist(name="My Playlist", tracks=None)
        track = Track(title="Non Existent Song", artists=["Non Existent Artist"], 
                     album=None, year=None, duration=0)
        
        with self.assertRaises(ValueError):
            self.vk_service.add_track_to_playlist(playlist, track)

    @patch.object(VkService, '_get_vk_api')
    def test_add_playlist(self, mock_get_vk_api):
        """Test creating a new playlist"""
        mock_api = MagicMock()
        mock_api.playlist.create.return_value = {"playlist_id": 999}
        mock_get_vk_api.return_value = mock_api
        
        self.vk_service.set_auth_data(self.test_token, self.test_user_id)
        
        playlist = Playlist(name="New Playlist", tracks=None)
        self.vk_service.add_playlist(playlist)
        
        mock_api.playlist.create.assert_called_once_with(
            title="New Playlist",
            description=""
        )
        # Verify metadata was cached
        self.assertIn("New Playlist", self.vk_service._playlist_metadata)

    @patch.object(VkService, '_get_vk_api')
    def test_add_playlist_api_error(self, mock_get_vk_api):
        """Test error when creating playlist fails"""
        mock_api = MagicMock()
        mock_api.playlist.create.side_effect = Exception("Creation failed")
        mock_get_vk_api.return_value = mock_api
        
        self.vk_service.set_auth_data(self.test_token, self.test_user_id)
        
        playlist = Playlist(name="Failed Playlist", tracks=None)
        
        with self.assertRaises(RuntimeError):
            self.vk_service.add_playlist(playlist)

    def test_map_vk_track_to_entity(self):
        """Test mapping VK track to Track entity"""
        vk_track = {
            "id": "123",
            "owner_id": self.test_user_id,
            "title": "Test Song",
            "artist": "Test Artist",
            "album": "Test Album",
            "duration": 180,
            "date": 1609459200  # 2021-01-01
        }
        
        track = self.vk_service._map_vk_track_to_entity(vk_track)
        
        self.assertEqual(track.title, "Test Song")
        self.assertEqual(track.artists, ["Test Artist"])
        self.assertEqual(track.album, "Test Album")
        self.assertEqual(track.year, 2021)
        self.assertEqual(track.duration, 180.0)

    def test_map_vk_track_to_entity_minimal_data(self):
        """Test mapping track with minimal data"""
        vk_track = {
            "title": "Minimal Song",
            "artist": "",
            "duration": 0
        }
        
        track = self.vk_service._map_vk_track_to_entity(vk_track)
        
        self.assertEqual(track.title, "Minimal Song")
        self.assertEqual(track.artists, ["Unknown Artist"])
        self.assertIsNone(track.album)
        self.assertIsNone(track.year)
        self.assertIsNone(track.duration)

    def test_map_vk_track_to_entity_missing_artist(self):
        """Test mapping track with missing artist"""
        vk_track = {
            "title": "Song Without Artist",
            "duration": 200
        }
        
        track = self.vk_service._map_vk_track_to_entity(vk_track)
        
        self.assertEqual(track.title, "Song Without Artist")
        self.assertEqual(track.artists, ["Unknown Artist"])
        self.assertEqual(track.duration, 200.0)

    def test_map_vk_playlist_to_entity(self):
        """Test mapping VK playlist to Playlist entity"""
        vk_playlist = {
            "id": "pl_123",
            "owner_id": self.test_user_id,
            "title": "Rock Classics",
            "count": 50,
            "photo": "https://example.com/photo.jpg",
            "access_key": "key_123"
        }
        
        playlist = self.vk_service._map_vk_playlist_to_entity(vk_playlist)
        
        self.assertEqual(playlist.name, "Rock Classics")
        # Verify metadata was cached
        self.assertIn("Rock Classics", self.vk_service._playlist_metadata)
        
        metadata = self.vk_service._playlist_metadata["Rock Classics"]
        self.assertEqual(metadata["vk_playlist_id"], "pl_123")
        self.assertEqual(metadata["owner_id"], self.test_user_id)
        self.assertEqual(metadata["access_key"], "key_123")

    def test_map_vk_playlist_to_entity_minimal_data(self):
        """Test mapping playlist with minimal data"""
        vk_playlist = {
            "id": "pl_456",
            "owner_id": 987654321,
            "title": "My Playlist",
            "count": 0
        }
        
        playlist = self.vk_service._map_vk_playlist_to_entity(vk_playlist)
        
        self.assertEqual(playlist.name, "My Playlist")

    def test_save_playlist_metadata(self):
        """Test saving playlist metadata"""
        vk_playlists = [
            {
                "id": "pl_1",
                "owner_id": self.test_user_id,
                "title": "Playlist 1",
                "count": 10,
                "photo": None,
                "access_key": None
            },
            {
                "id": "pl_2",
                "owner_id": self.test_user_id,
                "title": "Playlist 2",
                "count": 20,
                "photo": "photo_url",
                "access_key": "key"
            }
        ]
        
        self.vk_service._save_playlist_metadata(vk_playlists)
        
        self.assertEqual(len(self.vk_service._playlist_metadata), 2)
        self.assertIn("Playlist 1", self.vk_service._playlist_metadata)
        self.assertIn("Playlist 2", self.vk_service._playlist_metadata)
        
        self.assertEqual(
            self.vk_service._playlist_metadata["Playlist 1"]["vk_playlist_id"],
            "pl_1"
        )

    @patch.object(VkService, '_get_vk_api')
    def test_export_playlist_success(self, mock_get_vk_api):
        """Test exporting playlist with successful track additions"""
        mock_api = MagicMock()
        
        # Mock getting tracks from source playlist
        mock_api.audio.get.return_value = {
            "items": [
                {
                    "id": 888,
                    "owner_id": self.test_user_id,
                    "title": "Export Song 1",
                    "artist": "Artist 1",
                    "duration": 180
                }
            ]
        }
        
        # Mock adding track to destination
        mock_api.audio.add.return_value = True
        
        mock_get_vk_api.return_value = mock_api
        
        self.vk_service.set_auth_data(self.test_token, self.test_user_id)
        self.vk_service._playlist_metadata["Source"] = {
            "vk_playlist_id": 1001,
            "owner_id": self.test_user_id,
            "access_key": None
        }
        self.vk_service._playlist_metadata["Destination"] = {
            "vk_playlist_id": 1002,
            "owner_id": self.test_user_id,
            "access_key": None
        }
        
        source = Playlist(name="Source", tracks=None)
        destination = Playlist(name="Destination", tracks=None)
        
        # Should not raise exceptions
        self.vk_service.export_playlist(source, destination)


class TestVkAuthSpecification(unittest.TestCase):
    """Test cases for VkAuthSpecification"""

    def setUp(self):
        """Set up test fixtures"""
        self.spec = VkAuthSpecification()

    def test_auth_spec_fields(self):
        """Test that auth spec has required fields"""
        fields = self.spec.get_fields()
        field_names = [f.name for f in fields]

        self.assertIn("token", field_names)
        self.assertIn("user_id", field_names)

    def test_token_is_password_field(self):
        """Test that token is a password field"""
        fields = self.spec.get_fields()
        token_field = next(f for f in fields if f.name == "token")
        self.assertTrue(token_field.field_type.value == "password" or 
                       token_field.field_type.name == "PASSWORD")

    def test_user_id_is_number_field(self):
        """Test that user_id is a number field"""
        fields = self.spec.get_fields()
        user_id_field = next(f for f in fields if f.name == "user_id")
        self.assertTrue(user_id_field.field_type.value == "number" or 
                       user_id_field.field_type.name == "NUMBER")

    def test_token_field_required(self):
        """Test that token field is required"""
        fields = self.spec.get_fields()
        token_field = next(f for f in fields if f.name == "token")
        self.assertTrue(token_field.required)

    def test_user_id_field_required(self):
        """Test that user_id field is required"""
        fields = self.spec.get_fields()
        user_id_field = next(f for f in fields if f.name == "user_id")
        self.assertTrue(user_id_field.required)


class TestVkImportSpecification(unittest.TestCase):
    """Test cases for VkImportSpecification"""

    def setUp(self):
        """Set up test fixtures"""
        self.spec = VkImportSpecification()

    def test_import_spec_has_fields(self):
        """Test that import spec has required fields"""
        fields = self.spec.get_fields()
        field_names = [f.name for f in fields]

        self.assertIn("playlist_id", field_names)

    def test_playlist_id_field_required(self):
        """Test that playlist_id field is required"""
        fields = self.spec.get_fields()
        playlist_id_field = next(f for f in fields if f.name == "playlist_id")
        self.assertTrue(playlist_id_field.required)

    def test_owner_id_field_optional(self):
        """Test that owner_id field is optional"""
        fields = self.spec.get_fields()
        owner_id_field = next(f for f in fields if f.name == "owner_id")
        self.assertFalse(owner_id_field.required)


class TestVkExportSpecification(unittest.TestCase):
    """Test cases for VkExportSpecification"""

    def setUp(self):
        """Set up test fixtures"""
        self.spec = VkExportSpecification()

    def test_export_spec_has_fields(self):
        """Test that export spec has required fields"""
        fields = self.spec.get_fields()
        field_names = [f.name for f in fields]

        self.assertIn("destination_playlist_id", field_names)

    def test_destination_playlist_id_field_required(self):
        """Test that destination_playlist_id field is required"""
        fields = self.spec.get_fields()
        dest_field = next(f for f in fields if f.name == "destination_playlist_id")
        self.assertTrue(dest_field.required)

    def test_create_if_not_exists_has_default(self):
        """Test that create_if_not_exists field has default value"""
        fields = self.spec.get_fields()
        create_field = next(f for f in fields if f.name == "create_if_not_exists")
        self.assertIsNotNone(create_field.default)
        self.assertEqual(create_field.default, True)


if __name__ == "__main__":
    unittest.main()
