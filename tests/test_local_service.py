import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from src.model.entities.playlist import Playlist
from src.model.entities.track import Track
from src.model.services.providers.local.local_service import LocalService
from src.model.services.providers.local.local_directory_parser import LocalDirectoryParser
from src.model.services.providers.local.local_import_spec import LocalImportSpec
from src.model.services.providers.local.local_export_spec import LocalExportSpec
from src.model.services.providers.local.local_auth_spec import LocalAuthSpec


def make_track(title="Song", artists=None, album=None, year=None, duration=None):
    return Track(
        title=title,
        artists=[] if artists is None else artists,
        album=album,
        year=year,
        duration=duration,
    )


class TestLocalService(unittest.TestCase):
    def setUp(self):
        self.service = LocalService()
        self.mock_parser = Mock()
        self.service.parser = self.mock_parser

    def test_get_service_info(self):
        info = self.service.get_service_info()
        self.assertEqual(info.name, "Local Files")
        self.assertIsNone(info.icon_path)

    def test_get_import_specs(self):
        specs = self.service.get_import_specs()
        self.assertIsInstance(specs, LocalImportSpec)

    def test_get_export_specs(self):
        specs = self.service.get_export_specs()
        self.assertIsInstance(specs, LocalExportSpec)

    def test_get_auth_specs(self):
        specs = self.service.get_auth_specs()
        self.assertIsInstance(specs, LocalAuthSpec)

    def test_authenticate_sets_directory_and_clears_cache(self):
        self.service._playlists_cache = {".": [make_track("Cached")]}
        with patch.object(Path, "exists", return_value=True), patch.object(Path, "is_dir", return_value=True):
            self.service.authenticate("/tmp/music")
        self.assertEqual(self.service.directory, Path("/tmp/music"))
        self.assertEqual(self.service._playlists_cache, {})

    def test_authenticate_missing_directory_raises(self):
        with patch.object(Path, "exists", return_value=False):
            with self.assertRaises(ValueError):
                self.service.authenticate("/tmp/missing")

    def test_authenticate_non_directory_raises(self):
        with patch.object(Path, "exists", return_value=True), patch.object(Path, "is_dir", return_value=False):
            with self.assertRaises(ValueError):
                self.service.authenticate("/tmp/file.mp3")

    def test_reauthenticate_clears_cache(self):
        self.service._playlists_cache = {
            ".": [make_track("Cached Song")]
        }

        with patch.object(Path, "exists", return_value=True), patch.object(Path, "is_dir", return_value=True):
            self.service.authenticate("/tmp/music")
            self.service._playlists_cache["."] = [make_track("Another Song")]
            self.service.authenticate("/tmp/music")

        self.assertEqual(self.service._playlists_cache, {})    

    def test_get_playlists_without_authentication_raises(self):
        with self.assertRaises(Exception):
            self.service.get_playlists()

    def test_get_playlists_with_root_and_subdirectory(self):
        self.service.directory = Path("/music")
        root_tracks = [make_track("Root Song")]
        sub_tracks = [make_track("Sub Song")]
        self.mock_parser.parse_directory.side_effect = [root_tracks, sub_tracks]

        subdir = Mock(spec=Path)
        subdir.name = "Rock"
        subdir.is_dir.return_value = True

        hidden_dir = Mock(spec=Path)
        hidden_dir.name = ".hidden"
        hidden_dir.is_dir.return_value = True

        file_path = Mock(spec=Path)
        file_path.name = "note.txt"
        file_path.is_dir.return_value = False

        with patch.object(Path, "iterdir", return_value=[subdir, hidden_dir, file_path]):
            playlists = self.service.get_playlists()

        self.assertEqual(len(playlists), 2)
        self.assertEqual(playlists[0].name, ".")
        self.assertEqual(playlists[0].tracks, root_tracks)
        self.assertEqual(playlists[1].name, "Rock")
        self.assertEqual(playlists[1].tracks, sub_tracks)

    def test_get_playlists_skips_empty_subdirectories(self):
        self.service.directory = Path("/music")
        root_tracks = [make_track("Root Song")]
        self.mock_parser.parse_directory.side_effect = [root_tracks, []]

        subdir = Mock(spec=Path)
        subdir.name = "EmptyDir"
        subdir.is_dir.return_value = True

        with patch.object(Path, "iterdir", return_value=[subdir]):
            playlists = self.service.get_playlists()

        self.assertEqual(len(playlists), 1)
        self.assertEqual(playlists[0].name, ".")
    
    def test_get_playlists_empty_directory(self):
        self.service.directory = Path("/music")
        self.mock_parser.parse_directory.return_value = []

        empty_dir = Mock(spec=Path)
        empty_dir.name = "EmptyDir"
        empty_dir.is_dir.return_value = True

        with patch.object(Path, "iterdir", return_value=[empty_dir]):
            playlists = self.service.get_playlists()

        self.assertEqual(len(playlists), 1)
        self.assertEqual(playlists[0].name, ".")
        self.assertEqual(playlists[0].tracks, [])

    def test_get_tracks_from_playlist_root(self):
        self.service.directory = Path("/music")
        root_tracks = [make_track("Root Song")]
        self.mock_parser.parse_directory.return_value = root_tracks

        result = self.service.get_tracks_from_playlist(Playlist(name=".", tracks=[]))

        self.assertEqual(result, root_tracks)
        self.mock_parser.parse_directory.assert_called_once_with(self.service.directory)

    def test_get_tracks_from_playlist_subdirectory(self):
        self.service.directory = Path("/music")
        sub_tracks = [make_track("Sub Song")]
        self.mock_parser.parse_directory.return_value = sub_tracks

        subdir = Mock(spec=Path)
        subdir.name = "Jazz"
        subdir.is_dir.return_value = True

        with patch.object(Path, "iterdir", return_value=[subdir]):
            result = self.service.get_tracks_from_playlist(Playlist(name="Jazz", tracks=[]))

        self.assertEqual(result, sub_tracks)
        self.mock_parser.parse_directory.assert_called_once_with(subdir)

    def test_get_tracks_from_playlist_not_found(self):
        self.service.directory = Path("/music")

        subdir = Mock(spec=Path)
        subdir.name = "Jazz"
        subdir.is_dir.return_value = True

        with patch.object(Path, "iterdir", return_value=[subdir]):
            with self.assertRaises(ValueError):
                self.service.get_tracks_from_playlist(Playlist(name="Unknown", tracks=[]))

    def test_add_playlist_not_supported(self):
        with self.assertRaises(NotImplementedError):
            self.service.add_playlist(Playlist(name="New", tracks=[]))

    def test_add_track_to_playlist_not_supported(self):
        with self.assertRaises(NotImplementedError):
            self.service.add_track_to_playlist(Playlist(name="New", tracks=[]), make_track("Song"))

    def test_export_playlist_not_supported(self):
        with self.assertRaises(NotImplementedError):
            self.service.export_playlist(Playlist(name="Source", tracks=[]), Playlist(name="Dest", tracks=[]))

    def test_get_root_tracks_uses_cache(self):
        self.service.directory = Path("/music")
        root_tracks = [make_track("Cached Song")]
        self.mock_parser.parse_directory.return_value = root_tracks

        first = self.service._get_root_tracks()
        second = self.service._get_root_tracks()

        self.assertEqual(first, root_tracks)
        self.assertEqual(second, root_tracks)
        self.mock_parser.parse_directory.assert_called_once_with(self.service.directory)

    def test_get_subdirectories_ignores_hidden_and_files(self):
        self.service.directory = Path("/music")

        visible_dir = Mock(spec=Path)
        visible_dir.name = "Rock"
        visible_dir.is_dir.return_value = True

        hidden_dir = Mock(spec=Path)
        hidden_dir.name = ".hidden"
        hidden_dir.is_dir.return_value = True

        file_path = Mock(spec=Path)
        file_path.name = "track.mp3"
        file_path.is_dir.return_value = False

        with patch.object(Path, "iterdir", return_value=[visible_dir, hidden_dir, file_path]):
            result = self.service._get_subdirectories()

        self.assertEqual(result, [visible_dir])

    def test_get_subdirectory_tracks_uses_cache(self):
        self.service.directory = Path("/music")
        subdir = Mock(spec=Path)
        subdir.name = "Jazz"

        tracks = [make_track("Jazz Song")]
        self.mock_parser.parse_directory.return_value = tracks

        first = self.service._get_subdirectory_tracks(subdir)
        second = self.service._get_subdirectory_tracks(subdir)

        self.assertEqual(first, tracks)
        self.assertEqual(second, tracks)
        self.mock_parser.parse_directory.assert_called_once_with(subdir)


class TestLocalDirectoryParser(unittest.TestCase):
    def setUp(self):
        self.parser = LocalDirectoryParser()

    def test_parse_directory_skips_non_files_and_unsupported_extensions(self):
        directory = Mock(spec=Path)

        audio_file = Mock(spec=Path)
        audio_file.is_file.return_value = True
        audio_file.suffix = ".wav"

        txt_file = Mock(spec=Path)
        txt_file.is_file.return_value = True
        txt_file.suffix = ".txt"

        folder = Mock(spec=Path)
        folder.is_file.return_value = False
        folder.suffix = ""

        directory.glob.return_value = [audio_file, txt_file, folder]

        with patch.object(self.parser, "_parse_file", return_value=make_track("Song")) as mock_parse:
            tracks = self.parser.parse_directory(directory)

        self.assertEqual(len(tracks), 1)
        mock_parse.assert_called_once_with(audio_file)

    def test_get_tag_returns_none_without_tags(self):
        self.assertIsNone(self.parser._get_tag(None, ["TIT2"]))

    def test_get_tag_works_with_list_value(self):
        tags = {"TIT2": ["Song Title"]}
        self.assertEqual(self.parser._get_tag(tags, ["TIT2"]), "Song Title")

    def test_get_tag_works_with_scalar_value(self):
        tags = {"TIT2": "Song Title"}
        self.assertEqual(self.parser._get_tag(tags, ["TIT2"]), "Song Title")

    def test_get_artists_returns_empty_list_when_missing(self):
        self.assertEqual(self.parser._get_artists({}), [])

    def test_get_artists_splits_comma_separated_values(self):
        tags = {"artist": "A, B, C"}
        self.assertEqual(self.parser._get_artists(tags), ["A", "B", "C"])

    def test_get_year_parses_int_year(self):
        tags = {"year": "2024-01-01"}
        self.assertEqual(self.parser._get_year(tags), 2024)

    def test_get_year_returns_none_for_invalid_value(self):
        tags = {"year": "unknown"}
        self.assertIsNone(self.parser._get_year(tags))

    def test_sample_data_directory(self):
        data_dir = Path("tests/data/local_service")
        if not data_dir.exists():
            self.skipTest("tests/data/local_service not found")

        tracks = self.parser.parse_directory(data_dir)

        self.assertIsInstance(tracks, list)
        self.assertGreaterEqual(len(tracks), 1)
        self.assertTrue(all(isinstance(t, Track) for t in tracks))
        self.assertIsNotNone(tracks[0].title)


if __name__ == "__main__":
    unittest.main()