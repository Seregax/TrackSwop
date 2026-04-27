"""Tests for worker threads"""

import unittest
from unittest.mock import Mock, MagicMock
from PySide6.QtCore import QCoreApplication
import sys

from src.workers.playlists_loading_worker import PlaylistsLoadingWorker
from src.workers.tracks_loading_worker import TracksLoadingWorker
from src.model.entities.playlist import Playlist
from src.model.entities.track import Track


class TestPlaylistsLoadingWorker(unittest.TestCase):
    """Test PlaylistsLoadingWorker"""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests"""
        if not QCoreApplication.instance():
            QCoreApplication(sys.argv)
    
    def test_playlists_loaded_successfully(self):
        """Test successful playlist loading"""
        # Create mock service
        mock_service = Mock()
        mock_playlists = [
            Playlist(name="Playlist 1", playlist_id="1"),
            Playlist(name="Playlist 2", playlist_id="2"),
        ]
        mock_service.get_playlists.return_value = mock_playlists
        
        # Create worker
        worker = PlaylistsLoadingWorker(mock_service)
        
        # Track emitted signals
        finished_signal_received = []
        worker.finished.connect(lambda playlists: finished_signal_received.append(playlists))
        
        # Run worker
        worker.run()
        
        # Verify results
        self.assertEqual(len(finished_signal_received), 1)
        self.assertEqual(finished_signal_received[0], mock_playlists)
        mock_service.get_playlists.assert_called_once()
    
    def test_playlists_loading_error(self):
        """Test error handling during playlist loading"""
        # Create mock service that raises error
        mock_service = Mock()
        mock_service.get_playlists.side_effect = Exception("Network error")
        
        # Create worker
        worker = PlaylistsLoadingWorker(mock_service)
        
        # Track emitted signals
        error_signal_received = []
        worker.error.connect(lambda error: error_signal_received.append(error))
        
        # Run worker
        worker.run()
        
        # Verify error was emitted
        self.assertEqual(len(error_signal_received), 1)
        self.assertIn("Failed to load playlists", error_signal_received[0])


class TestTracksLoadingWorker(unittest.TestCase):
    """Test TracksLoadingWorker"""
    
    @classmethod
    def setUpClass(cls):
        """Set up QApplication for all tests"""
        if not QCoreApplication.instance():
            QCoreApplication(sys.argv)
    
    def test_tracks_loaded_successfully(self):
        """Test successful tracks loading"""
        # Create mock service
        mock_service = Mock()
        mock_playlist = Playlist(name="Test Playlist", playlist_id="1")
        mock_tracks = [
            Track(title="Song 1", artists=["Artist 1"], duration=180),
            Track(title="Song 2", artists=["Artist 2"], duration=200),
        ]
        mock_service.get_tracks_from_playlist.return_value = mock_tracks
        
        # Create worker
        worker = TracksLoadingWorker(mock_service, mock_playlist)
        
        # Track emitted signals
        finished_signal_received = []
        worker.finished.connect(lambda tracks: finished_signal_received.append(tracks))
        
        # Run worker
        worker.run()
        
        # Verify results
        self.assertEqual(len(finished_signal_received), 1)
        self.assertEqual(finished_signal_received[0], mock_tracks)
        mock_service.get_tracks_from_playlist.assert_called_once_with(mock_playlist)
    
    def test_tracks_loading_error(self):
        """Test error handling during tracks loading"""
        # Create mock service that raises error
        mock_service = Mock()
        mock_playlist = Playlist(name="Test Playlist", playlist_id="1")
        mock_service.get_tracks_from_playlist.side_effect = Exception("Service error")
        
        # Create worker
        worker = TracksLoadingWorker(mock_service, mock_playlist)
        
        # Track emitted signals
        error_signal_received = []
        worker.error.connect(lambda error: error_signal_received.append(error))
        
        # Run worker
        worker.run()
        
        # Verify error was emitted
        self.assertEqual(len(error_signal_received), 1)
        self.assertIn("Failed to load tracks", error_signal_received[0])


if __name__ == '__main__':
    unittest.main()
