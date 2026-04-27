import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.view.view_models.transfer_vm import TransferViewModel, TransferStatus, TransferStatistics, TransferLogEntry


class TestTransferViewModel(unittest.TestCase):

    def setUp(self):
        self.vm = TransferViewModel()

    def test_initialization(self):
        """Test that ViewModel initializes correctly"""
        self.assertEqual(self.vm.status, TransferStatus.IDLE.value)
        self.assertEqual(self.vm.progress, 0)
        self.assertEqual(self.vm.total_tracks, 0)
        self.assertEqual(self.vm.processed_tracks, 0)
        self.assertEqual(self.vm.failed_tracks, 0)
        self.assertEqual(self.vm.log, [])

    def test_set_service_instances(self):
        """Test setting service instances and playlists"""
        mock_source_service = Mock()
        mock_dest_service = Mock()
        mock_source_playlist = Mock()
        mock_dest_playlist = Mock()

        self.vm.set_service_instances(
            mock_source_service, mock_dest_service,
            mock_source_playlist, mock_dest_playlist
        )

        self.assertEqual(self.vm._source_service_instance, mock_source_service)
        self.assertEqual(self.vm._dest_service_instance, mock_dest_service)
        self.assertEqual(self.vm._source_playlist_object, mock_source_playlist)
        self.assertEqual(self.vm._dest_playlist_object, mock_dest_playlist)

    def test_start_transfer_missing_instances(self):
        """Test starting transfer with missing instances"""
        self.vm.start_transfer()

        self.assertEqual(self.vm.status, TransferStatus.ERROR.value)
        self.assertGreater(len(self.vm.log), 0)

    @patch('src.view.view_models.transfer_vm.QThread')
    @patch('src.view.view_models.transfer_vm.TransferWorker')
    def test_start_transfer_success(self, mock_worker_class, mock_thread_class):
        """Test successful transfer start"""
        # Setup mocks
        mock_source_service = Mock()
        mock_dest_service = Mock()
        mock_source_playlist = Mock()
        mock_dest_playlist = Mock()
        mock_worker = Mock()
        mock_thread = Mock()

        mock_worker_class.return_value = mock_worker
        mock_thread_class.return_value = mock_thread

        self.vm.set_service_instances(
            mock_source_service, mock_dest_service,
            mock_source_playlist, mock_dest_playlist
        )
        self.vm.source_service = "spotify"
        self.vm.destination_service = "vk"
        self.vm.source_playlist = "Source Playlist"
        self.vm.destination_playlist = "Dest Playlist"

        self.vm.start_transfer()

        self.assertEqual(self.vm.status, TransferStatus.RUNNING.value)
        mock_thread_class.assert_called_once()
        mock_worker_class.assert_called_once_with(
            mock_source_service, mock_dest_service,
            mock_source_playlist, mock_dest_playlist
        )
        mock_worker.moveToThread.assert_called_once_with(mock_thread)
        mock_thread.start.assert_called_once()

    def test_cancel_transfer(self):
        """Test cancelling transfer"""
        self.vm._status = TransferStatus.RUNNING
        mock_worker = Mock()
        self.vm._worker = mock_worker

        self.vm.cancel_transfer()

        self.assertEqual(self.vm.status, TransferStatus.CANCELLED.value)
        mock_worker.cancel.assert_called_once()
        self.assertGreater(len(self.vm.log), 0)

    def test_reset(self):
        """Test resetting transfer state"""
        self.vm._status = TransferStatus.COMPLETED
        self.vm._log = [TransferLogEntry("10:00:00", "Test", "info")]
        self.vm._statistics = TransferStatistics(total_tracks=10, processed_tracks=10)

        self.vm.reset()

        self.assertEqual(self.vm.status, TransferStatus.IDLE.value)
        self.assertEqual(self.vm.log, [])
        self.assertEqual(self.vm.total_tracks, 0)

    def test_add_log(self):
        """Test adding log entry"""
        initial_log_count = len(self.vm.log)

        self.vm._add_log("Test message", "warning")

        self.assertEqual(len(self.vm.log), initial_log_count + 1)
        self.assertEqual(self.vm.log[-1]["message"], "Test message")
        self.assertEqual(self.vm.log[-1]["level"], "warning")

    def test_clear_log(self):
        """Test clearing log"""
        self.vm._add_log("Test")
        self.assertGreater(len(self.vm.log), 0)

        self.vm.clear_log()

        self.assertEqual(self.vm.log, [])

    def test_statistics_progress(self):
        """Test statistics progress calculation"""
        stats = TransferStatistics(total_tracks=10, processed_tracks=5)
        self.assertEqual(stats.progress, 50)

        stats = TransferStatistics(total_tracks=0, processed_tracks=0)
        self.assertEqual(stats.progress, 0)

    def test_statistics_duration(self):
        """Test statistics duration calculation"""
        start_time = "2023-01-01T10:00:00"
        end_time = "2023-01-01T10:01:30"
        stats = TransferStatistics(start_time=start_time, end_time=end_time)
        self.assertEqual(stats.duration, "1:30")

        stats_no_end = TransferStatistics(start_time=start_time)
        self.assertNotEqual(stats_no_end.duration, "0:00")


if __name__ == '__main__':
    unittest.main()