import unittest
from unittest.mock import Mock, patch

from src.view.view_models.playlist_vm import PlaylistViewModel


class TestPlaylistViewModel(unittest.TestCase):

    def setUp(self):
        self.vm = PlaylistViewModel(service_name="source")

    def test_service_selected_signal_emits_service_name(self):
        """Test that selecting service emits signal"""
        mock_callback = Mock()
        self.vm.service_selected.connect(mock_callback)

        self.vm.select_service("spotify")

        mock_callback.assert_called_once_with("spotify")

    def test_select_service_updates_selected_service(self):
        """Test that service name is updated"""
        self.vm.select_service("vk")

        self.assertEqual(self.vm.selected_service, "vk")

    def test_has_playlist_selected_false_by_default(self):
        """Test initial state"""
        self.assertFalse(self.vm.has_playlist_selected)

    def test_has_playlist_selected_true_after_selection(self):
        """Test state after playlist selection"""
        self.vm.current_playlist = "My Playlist"

        self.assertTrue(self.vm.has_playlist_selected)

    def test_load_playlists(self):
        """Test playlist loading"""
        from src.model.entities.playlist import Playlist

        playlists = [
            Playlist(name="Playlist 1", tracks=None),
            Playlist(name="Playlist 2", tracks=None),
        ]

        self.vm.load_playlists(playlists)

        self.assertEqual(len(self.vm.playlists), 2)
        self.assertEqual(self.vm.playlists[0], "Playlist 1")


if __name__ == '__main__':
    unittest.main()