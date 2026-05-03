"""Tests for Yandex Music public playlist import service."""

import unittest
from unittest.mock import Mock, patch

import requests

from src.common.exceptions import AuthError, ServiceError
from src.model.entities.playlist import Playlist
from src.model.entities.track import Track
from src.model.services.providers.yandex.yandex_auth_spec import YandexAuthSpec
from src.model.services.providers.yandex.yandex_export_spec import YandexExportSpec
from src.model.services.providers.yandex.yandex_import_spec import YandexImportSpec
from src.model.services.providers.yandex.yandex_service import YandexMusicService


class MockResponse:
    def __init__(self, data=None, status_code=200, text="", url="https://music.yandex.ru/mock"):
        self._data = data if data is not None else {}
        self.status_code = status_code
        self.text = text
        self.url = url

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.HTTPError(f"HTTP {self.status_code}")
            error.response = self
            raise error

    def json(self):
        return self._data


class TestYandexMusicService(unittest.TestCase):
    """Test cases for YandexMusicService."""

    def setUp(self):
        self.session = Mock()
        self.service = YandexMusicService(
            playlist_url="https://music.yandex.ru/users/test-user/playlists/1000",
            session=self.session,
        )

    def test_get_service_info(self):
        info = self.service.get_service_info()

        self.assertEqual(info.name, "Yandex Music")
        self.assertIsNone(info.icon_path)

    def test_get_specs(self):
        self.assertIsInstance(self.service.get_auth_specs(), YandexAuthSpec)
        self.assertIsInstance(self.service.get_import_specs(), YandexImportSpec)
        self.assertIsInstance(self.service.get_export_specs(), YandexExportSpec)

    def test_parse_playlist_url(self):
        ref = YandexMusicService._parse_playlist_url(
            "https://music.yandex.com/users/some-user/playlists/42?utm_source=share"
        )

        self.assertEqual(ref.owner, "some-user")
        self.assertEqual(ref.kind, "42")
        self.assertEqual(ref.host, "music.yandex.com")

    def test_parse_playlist_url_new_share_format(self):
        ref = YandexMusicService._parse_playlist_url(
            "https://music.yandex.ru/playlists/lk.a010eeb5-5c3a-4b85-8dc2-b3838e175056"
        )

        self.assertIsNone(ref.owner)
        self.assertIsNone(ref.kind)
        self.assertEqual(ref.share_id, "lk.a010eeb5-5c3a-4b85-8dc2-b3838e175056")
        self.assertEqual(ref.host, "music.yandex.ru")

    def test_extract_playlist_url_from_embed_code(self):
        html = (
            '<iframe frameborder="0" allow="clipboard-write" '
            'src="https://music.yandex.ru/iframe/playlist/timafeibogdanoff/1007">'
            "</iframe>"
        )

        extracted = YandexMusicService._extract_playlist_url_from_embed_code(html)

        self.assertEqual(
            extracted,
            "https://music.yandex.ru/iframe/playlist/timafeibogdanoff/1007",
        )

    def test_extract_playlist_url_from_embed_code_without_quotes(self):
        html = (
            "<iframe frameborder=0 allow=clipboard-write "
            "src=https://music.yandex.ru/iframe/playlist/timafeibogdanoff/1007>"
            "</iframe>"
        )

        extracted = YandexMusicService._extract_playlist_url_from_embed_code(html)

        self.assertEqual(
            extracted,
            "https://music.yandex.ru/iframe/playlist/timafeibogdanoff/1007",
        )

    def test_parse_playlist_url_iframe_format(self):
        ref = YandexMusicService._parse_playlist_url(
            "https://music.yandex.ru/iframe/playlist/timafeibogdanoff/1007"
        )

        self.assertEqual(ref.owner, "timafeibogdanoff")
        self.assertEqual(ref.kind, "1007")
        self.assertEqual(
            ref.original_url,
            "https://music.yandex.ru/users/timafeibogdanoff/playlists/1007",
        )

    def test_parse_playlist_url_rejects_other_hosts(self):
        with self.assertRaises(ValueError):
            YandexMusicService._parse_playlist_url(
                "https://example.com/users/user/playlists/42"
            )

    def test_authenticate_requires_playlist_url(self):
        service = YandexMusicService()

        with self.assertRaises(AuthError):
            service.authenticate()

    def test_authenticate_loads_public_playlist(self):
        self.session.get.return_value = MockResponse(
            {
                "playlist": {
                    "title": "Public Playlist",
                    "tracks": [
                        {
                            "id": "1",
                            "title": "Song One",
                            "artists": [{"name": "Artist One"}],
                            "albums": [{"title": "Album One", "year": 2024}],
                            "durationMs": 180000,
                        }
                    ],
                    "trackIds": ["1"],
                }
            }
        )

        self.service.authenticate()
        playlists = self.service.get_playlists()
        tracks = self.service.get_tracks_from_playlist(playlists[0])

        self.assertEqual(len(playlists), 1)
        self.assertEqual(playlists[0].name, "Public Playlist")
        self.assertEqual(len(tracks), 1)
        self.assertEqual(tracks[0].title, "Song One")
        self.assertEqual(tracks[0].artists, ["Artist One"])
        self.assertEqual(tracks[0].album, "Album One")
        self.assertEqual(tracks[0].year, 2024)
        self.assertEqual(tracks[0].duration, 180.0)

    def test_authenticate_loads_new_share_format(self):
        service = YandexMusicService(
            playlist_url="https://music.yandex.ru/playlists/lk.a010eeb5-5c3a-4b85-8dc2-b3838e175056",
            session=self.session,
        )
        self.session.get.side_effect = [
            MockResponse(
                text=(
                    '...'
                    '"preloadedPlaylistByUuid":{"owner":{"uid":917505736,'
                    '"login":"timafeibogdanoff","name":"User"},'
                    '"playlistUuid":"lk.a010eeb5-5c3a-4b85-8dc2-b3838e175056",'
                    '"available":true,"uid":917505736,"kind":3,"title":"Мне нравится"}'
                    '...'
                )
            ),
            MockResponse(
                {
                    "playlist": {
                        "title": "Мне нравится",
                        "tracks": [
                            {
                                "id": "1",
                                "title": "Song One",
                                "artists": [{"name": "Artist One"}],
                            }
                        ],
                        "trackIds": ["1"],
                    }
                }
            ),
        ]

        service.authenticate()
        playlists = service.get_playlists()

        self.assertEqual(len(playlists), 1)
        self.assertEqual(playlists[0].name, "Мне нравится")
        self.assertEqual(self.session.get.call_count, 2)

    def test_authenticate_html_embed_uses_iframe_source(self):
        html = (
            '<iframe src="https://music.yandex.ru/iframe/playlist/timafeibogdanoff/1007">'
            "</iframe>"
        )
        service = YandexMusicService(
            playlist_url=html,
            session=self.session,
        )
        self.session.get.return_value = MockResponse(
            {
                "playlist": {
                    "title": "Тренировка",
                    "tracks": [
                        {
                            "id": "1",
                            "title": "Song One",
                            "artists": [{"name": "Artist One"}],
                        }
                    ],
                    "trackIds": ["1"],
                }
            }
        )

        service.authenticate()

        self.assertEqual(service.get_playlists()[0].name, "Тренировка")
        call_kwargs = self.session.get.call_args.kwargs
        self.assertIn("/users/timafeibogdanoff/playlists/1007", call_kwargs["headers"]["Referer"])

    def test_authenticate_loads_missing_track_entries(self):
        self.session.get.side_effect = [
            MockResponse(
                {
                    "playlist": {
                        "title": "Large Playlist",
                        "tracks": [
                            {
                                "id": "1",
                                "title": "Loaded Song",
                                "artists": [{"name": "Artist"}],
                            }
                        ],
                        "trackIds": ["1", "2"],
                    }
                }
            ),
            MockResponse(
                [
                    {
                        "track": {
                            "id": "2",
                            "title": "Missing Song",
                            "artists": [{"name": "Artist"}],
                        }
                    }
                ]
            ),
        ]

        self.service.authenticate()
        tracks = self.service.get_tracks_from_playlist(
            Playlist(name="Large Playlist", tracks=None)
        )

        self.assertEqual([track.title for track in tracks], ["Loaded Song", "Missing Song"])
        self.assertEqual(self.session.get.call_count, 2)

    def test_authenticate_handles_timeout(self):
        self.session.get.side_effect = requests.Timeout()

        with self.assertRaises(ServiceError):
            self.service.authenticate()

    def test_authenticate_handles_unavailable_playlist(self):
        self.session.get.return_value = MockResponse(status_code=404)

        with self.assertRaises(ServiceError):
            self.service.authenticate()

    def test_authenticate_new_share_format_reports_captcha(self):
        service = YandexMusicService(
            playlist_url="https://music.yandex.ru/playlists/lk.a010eeb5-5c3a-4b85-8dc2-b3838e175056",
            session=self.session,
        )
        self.session.get.return_value = MockResponse(
            text="captcha",
            url="https://music.yandex.ru/showcaptcha?x=1",
        )
        retry_session_1 = Mock()
        retry_session_1.get.return_value = MockResponse(
            text="captcha",
            url="https://music.yandex.ru/showcaptcha?x=2",
        )
        retry_session_2 = Mock()
        retry_session_2.get.return_value = MockResponse(
            text="captcha",
            url="https://music.yandex.ru/showcaptcha?x=3",
        )

        with patch(
            "src.model.services.providers.yandex.yandex_service.requests.Session",
            side_effect=[retry_session_1, retry_session_2],
        ):
            with self.assertRaises(ServiceError) as ctx:
                service.authenticate()

        self.assertIn("captcha", str(ctx.exception).lower())

    def test_add_and_export_are_not_supported(self):
        playlist = Playlist(name="Playlist", tracks=[])
        track = Track(title="Song", artists=[], album=None, year=None, duration=None)

        with self.assertRaises(NotImplementedError):
            self.service.add_playlist(playlist)
        with self.assertRaises(NotImplementedError):
            self.service.add_track_to_playlist(playlist, track)
        with self.assertRaises(NotImplementedError):
            self.service.export_playlist(playlist, playlist)


if __name__ == "__main__":
    unittest.main()
