import unittest
from unittest.mock import Mock, patch, MagicMock

from src.view.view_models.main_window_vm import MainWindowViewModel
from src.model.store.token_store import TokenStore


class TestMainWindowViewModel(unittest.TestCase):

    def setUp(self):
        self.token_store = Mock(spec=TokenStore)
        self.vm = MainWindowViewModel(token_store=self.token_store)

    def test_initialization(self):
        """Test that ViewModel initializes correctly"""
        self.assertIsNotNone(self.vm.source_vm)
        self.assertIsNotNone(self.vm.dest_vm)
        self.assertIsNotNone(self.vm.transfer_vm)
        self.assertIsNotNone(self.vm.service_registry)
        self.assertEqual(self.vm.token_store, self.token_store)

    def test_authenticate_service_success(self):
        """Test successful service authentication"""
        mock_service = Mock()
        mock_service.authenticate = Mock()

        with patch.object(self.vm.service_registry, 'get_service', return_value=mock_service) as mock_get_service:
            result = self.vm.authenticate_service("spotify", {"token": "test_token"})

            self.assertTrue(result)
            mock_get_service.assert_called_once_with("spotify", {"token": "test_token"})
            mock_service.authenticate.assert_called_once()
            self.token_store.save_token.assert_called_once_with("spotify", "test_token")

    def test_authenticate_service_failure(self):
        """Test failed service authentication"""
        with patch.object(self.vm.service_registry, 'get_service', side_effect=Exception("Auth failed")):
            result = self.vm.authenticate_service("spotify", {"token": "invalid"})

            self.assertFalse(result)

    def test_get_authenticated_service_with_token(self):
        """Test getting authenticated service using stored token"""
        mock_service = Mock()
        mock_service.authenticate = Mock()

        self.token_store.get_token.return_value = "stored_token"

        with patch.object(self.vm.service_registry, 'get_service', return_value=mock_service) as mock_get_service:
            service = self.vm.get_authenticated_service("spotify")

            self.assertEqual(service, mock_service)
            mock_get_service.assert_called_once_with("spotify", {"token": "stored_token"})
            mock_service.authenticate.assert_called_once()

    def test_get_authenticated_service_cached(self):
        """Test getting cached authenticated service"""
        mock_service = Mock()
        self.vm._auth_services["spotify"] = mock_service

        service = self.vm.get_authenticated_service("spotify")

        self.assertEqual(service, mock_service)

    def test_can_transfer_true(self):
        """Test can_transfer returns True when conditions met"""
        self.vm._source_vm._current_playlist = "Source Playlist"
        self.vm._dest_vm._current_playlist = "Dest Playlist"
        self.vm._source_vm._selected_service = "spotify"
        self.vm._dest_vm._selected_service = "vk"
        self.vm._auth_services["spotify"] = Mock()
        self.vm._auth_services["vk"] = Mock()

        self.assertTrue(self.vm.can_transfer())

    def test_can_transfer_false_no_playlist(self):
        """Test can_transfer returns False when no playlist selected"""
        self.assertFalse(self.vm.can_transfer())

    def test_start_transfer(self):
        """Test starting transfer"""
        # Mock services and playlists
        mock_source_service = Mock()
        mock_dest_service = Mock()
        mock_source_playlist = Mock()
        mock_dest_playlist = Mock()

        self.vm._source_vm._selected_service = "spotify"
        self.vm._dest_vm._selected_service = "vk"
        self.vm._source_vm._current_playlist_object = mock_source_playlist
        self.vm._dest_vm._current_playlist_object = mock_dest_playlist

        with patch.object(self.vm, 'get_authenticated_service') as mock_get_auth:
            mock_get_auth.side_effect = [mock_source_service, mock_dest_service]

            with patch.object(self.vm._transfer_vm, 'set_service_instances') as mock_set_instances:
                with patch.object(self.vm._transfer_vm, 'start_transfer') as mock_start:
                    self.vm.start_transfer()

                    mock_set_instances.assert_called_once_with(
                        mock_source_service, mock_dest_service,
                        mock_source_playlist, mock_dest_playlist
                    )
                    mock_start.assert_called_once()


if __name__ == '__main__':
    unittest.main()