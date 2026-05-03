import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import unquote, urlparse
import re

import requests

from src.common.exceptions import AuthError, ServiceError
from src.common.logger import get_logger
from src.model.entities.playlist import Playlist
from src.model.entities.track import Track
from src.model.services.interfaces.istreaming_service import IStreamingService
from src.model.services.interfaces.service_info import ServiceInfo
from src.model.services.providers.yandex.yandex_auth_spec import YandexAuthSpec
from src.model.services.providers.yandex.yandex_export_spec import YandexExportSpec
from src.model.services.providers.yandex.yandex_import_spec import YandexImportSpec
from src.model.specifications.base import BaseSpecification

logger = get_logger(__name__)


@dataclass(frozen=True)
class YandexPlaylistReference:
    """Parsed public Yandex Music playlist reference."""

    owner: Optional[str]
    kind: Optional[str]
    host: str
    original_url: str
    share_id: Optional[str] = None


class YandexMusicService(IStreamingService):
    """
    Yandex Music public playlist importer.

    Supports only importing tracks from a public playlist share link.
    Export, playlist creation, and track adding are intentionally unsupported.
    """

    SERVICE_NAME = "yandex"
    SUPPORTED_HOSTS = {"music.yandex.ru", "music.yandex.com"}
    REQUEST_TIMEOUT_SECONDS = 10
    TRACK_ENTRIES_BATCH_SIZE = 100
    SHARE_PAGE_ATTEMPTS = 3
    SHARE_PLAYLIST_PATTERNS = (
        re.compile(
            r'"preloadedPlaylistByUuid":\{"owner":\{.*?"login":"(?P<owner>[^"]+)".*?"kind":(?P<kind>\d+)',
            re.DOTALL,
        ),
        re.compile(
            r'\\"preloadedPlaylistByUuid\\":\{\\"owner\\":\{.*?\\"login\\":\\"(?P<owner>[^"]+)\\".*?\\"kind\\":(?P<kind>\d+)',
            re.DOTALL,
        ),
    )
    EMBED_IFRAME_SRC_PATTERN = re.compile(
        r'src\s*=\s*(?:"(?P<quoted>https?://music\.yandex\.(?:ru|com)/iframe/playlist/[^"]+)"|(?P<plain>https?://music\.yandex\.(?:ru|com)/iframe/playlist/[^\s>]+))',
        re.IGNORECASE,
    )

    def __init__(
        self,
        playlist_url: Optional[str] = None,
        session: Optional[requests.Session] = None,
    ):
        self.playlist_url = playlist_url
        self._session = session or requests.Session()
        self._playlist_ref: Optional[YandexPlaylistReference] = None
        self._playlist: Optional[Playlist] = None
        self._tracks: List[Track] = []

    def get_service_info(self) -> ServiceInfo:
        """Get service information."""
        return ServiceInfo(
            name="Yandex Music",
            icon_path=None,
        )

    def authenticate(self) -> None:
        """
        Validate and load the public playlist.

        The app uses an auth form for provider setup, so the public share link is
        accepted there even though no Yandex account authentication is performed.
        """
        if not self.playlist_url:
            raise AuthError("Yandex Music playlist link is required")

        try:
            normalized_input = self._extract_playlist_url_from_embed_code(self.playlist_url)
            self._playlist_ref = self._parse_playlist_url(normalized_input)
            self._playlist_ref = self._resolve_playlist_reference(self._playlist_ref)
            playlist_data = self._load_playlist_data(self._playlist_ref)
            playlist_title = self._extract_playlist_title(playlist_data)
            raw_tracks = self._extract_raw_tracks(playlist_data, self._playlist_ref)
            self._tracks = [self._map_track(track) for track in raw_tracks]
            self._playlist = Playlist(name=playlist_title, tracks=self._tracks)
            logger.info(
                "Loaded Yandex Music playlist '%s' with %s tracks",
                playlist_title,
                len(self._tracks),
            )
        except ServiceError:
            raise
        except Exception as e:
            logger.error("Yandex Music playlist import failed: %s", e)
            raise ServiceError(
                "Failed to load Yandex Music playlist",
                "Could not load the public Yandex Music playlist.",
            ) from e

    def get_playlists(self) -> List[Playlist]:
        """Return the single public playlist configured through the auth form."""
        if not self._playlist:
            raise ServiceError("Not authenticated. Call authenticate() first.")
        return [self._playlist]

    def get_tracks_from_playlist(self, playlist: Playlist) -> List[Track]:
        """Return tracks from the configured public playlist."""
        if not self._playlist:
            raise ServiceError("Not authenticated. Call authenticate() first.")

        if playlist.name != self._playlist.name:
            raise ValueError(f"Playlist '{playlist.name}' not found")

        return list(self._tracks)

    def add_playlist(self, playlist: Playlist) -> None:
        """Creating playlists in Yandex Music is not supported."""
        raise NotImplementedError("YandexMusicService supports only playlist import")

    def add_track_to_playlist(self, playlist: Playlist, track: Track) -> None:
        """Adding tracks to Yandex Music is not supported."""
        raise NotImplementedError("YandexMusicService supports only playlist import")

    def export_playlist(self, source: Playlist, destination: Playlist) -> None:
        """Exporting to Yandex Music is not supported."""
        raise NotImplementedError("YandexMusicService supports only playlist import")

    def get_import_specs(self) -> BaseSpecification:
        """Get import specifications."""
        return YandexImportSpec()

    def get_export_specs(self) -> BaseSpecification:
        """Get export specifications."""
        return YandexExportSpec()

    def get_auth_specs(self) -> BaseSpecification:
        """Get setup form fields."""
        return YandexAuthSpec()

    def set_auth_data(self, playlist_url: str) -> None:
        """Set the public playlist share link."""
        self.playlist_url = playlist_url
        self._playlist_ref = None
        self._playlist = None
        self._tracks = []

    @classmethod
    def _parse_playlist_url(cls, playlist_url: str) -> YandexPlaylistReference:
        parsed = urlparse(playlist_url.strip())

        if parsed.scheme not in {"http", "https"}:
            raise ValueError("Yandex Music playlist link must start with http or https")

        host = parsed.netloc.lower()
        if host not in cls.SUPPORTED_HOSTS:
            raise ValueError("Unsupported Yandex Music host")

        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) == 4 and path_parts[0] == "users" and path_parts[2] == "playlists":
            owner = unquote(path_parts[1]).strip()
            kind = unquote(path_parts[3]).strip()
            if not owner or not kind:
                raise ValueError("Yandex Music playlist owner and id are required")

            return YandexPlaylistReference(
                owner=owner,
                kind=kind,
                host=host,
                original_url=playlist_url.strip(),
            )

        if len(path_parts) == 2 and path_parts[0] == "playlists":
            share_id = unquote(path_parts[1]).strip()
            if not share_id:
                raise ValueError("Yandex Music playlist share id is required")

            return YandexPlaylistReference(
                owner=None,
                kind=None,
                host=host,
                original_url=playlist_url.strip(),
                share_id=share_id,
            )

        if len(path_parts) == 4 and path_parts[0] == "iframe" and path_parts[1] == "playlist":
            owner = unquote(path_parts[2]).strip()
            kind = unquote(path_parts[3]).strip()
            if not owner or not kind:
                raise ValueError("Yandex Music iframe playlist owner and id are required")

            return YandexPlaylistReference(
                owner=owner,
                kind=kind,
                host=host,
                original_url=f"https://{host}/users/{owner}/playlists/{kind}",
            )

        raise ValueError(
            "Expected Yandex Music playlist link format: "
            "https://music.yandex.ru/users/<user>/playlists/<id> "
            "or https://music.yandex.ru/playlists/<share_id> "
            "or iframe embed HTML with https://music.yandex.ru/iframe/playlist/<user>/<id>"
        )

    @classmethod
    def _extract_playlist_url_from_embed_code(cls, raw_input: str) -> str:
        value = raw_input.strip()

        if "<iframe" not in value.lower():
            return value

        match = cls.EMBED_IFRAME_SRC_PATTERN.search(value)
        if match:
            return match.group("quoted") or match.group("plain")

        raise ValueError("Could not extract Yandex Music iframe src from embed HTML")

    def _resolve_playlist_reference(
        self,
        ref: YandexPlaylistReference,
    ) -> YandexPlaylistReference:
        if ref.owner and ref.kind:
            return ref

        if not ref.share_id:
            raise ServiceError(
                "Yandex Music playlist reference is incomplete",
                "Could not resolve the Yandex Music playlist link.",
            )

        page_html = self._get_text(ref.original_url, ref=ref)
        match = self._match_share_playlist_metadata(page_html)

        if not match:
            raise ServiceError(
                "Could not resolve shared Yandex Music playlist link",
                "Could not parse the shared Yandex Music playlist page.",
            )

        owner = match.group("owner").strip()
        kind = match.group("kind").strip()

        if not owner or not kind:
            raise ServiceError(
                "Shared Yandex Music playlist page does not contain owner or playlist id",
                "Could not parse the shared Yandex Music playlist page.",
            )

        logger.info(
            "Resolved Yandex Music share link '%s' to owner='%s', kind='%s'",
            ref.share_id,
            owner,
            kind,
        )

        return YandexPlaylistReference(
            owner=owner,
            kind=kind,
            host=ref.host,
            original_url=ref.original_url,
            share_id=ref.share_id,
        )

    def _match_share_playlist_metadata(self, page_html: str) -> Optional[re.Match]:
        for pattern in self.SHARE_PLAYLIST_PATTERNS:
            match = pattern.search(page_html)
            if match:
                return match
        return None

    def _load_playlist_data(self, ref: YandexPlaylistReference) -> Dict[str, Any]:
        endpoint = f"https://{ref.host}/handlers/playlist.jsx"
        params = {
            "owner": ref.owner,
            "kinds": ref.kind,
            "light": "true",
            "lang": self._language_from_host(ref.host),
            "external-domain": ref.host,
            "overembed": "false",
            "r": str(time.time()),
        }

        data = self._get_json(endpoint, params=params, ref=ref)
        playlist_data = data.get("playlist")

        if not isinstance(playlist_data, dict):
            raise ServiceError(
                "Yandex Music playlist response does not contain playlist data",
                "Could not parse the Yandex Music playlist page.",
            )

        if playlist_data.get("playlistAbsence") or playlist_data.get("error"):
            raise ServiceError(
                "Yandex Music playlist is unavailable or private",
                "The Yandex Music playlist is unavailable or private.",
            )

        return playlist_data

    def _get_json(
        self,
        url: str,
        params: Dict[str, str],
        ref: YandexPlaylistReference,
    ) -> Dict[str, Any]:
        try:
            response = self._session.get(
                url,
                params=params,
                timeout=self.REQUEST_TIMEOUT_SECONDS,
                headers=self._request_headers(ref),
            )
            if "showcaptcha" in response.url:
                raise ServiceError(
                    "Yandex Music requested captcha for playlist API",
                    "Yandex Music requested captcha while loading the playlist.",
                )
            response.raise_for_status()
            return response.json()
        except requests.Timeout as e:
            raise ServiceError(
                "Yandex Music request timed out",
                "Yandex Music did not respond in time.",
            ) from e
        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else None
            if status_code in {403, 404}:
                raise ServiceError(
                    f"Yandex Music playlist is unavailable: HTTP {status_code}",
                    "The Yandex Music playlist is unavailable or private.",
                ) from e
            raise ServiceError(
                f"Yandex Music request failed: HTTP {status_code}",
                "Could not load the Yandex Music playlist.",
            ) from e
        except requests.RequestException as e:
            raise ServiceError(
                f"Yandex Music network error: {e}",
                "Network error while loading the Yandex Music playlist.",
            ) from e
        except ValueError as e:
            raise ServiceError(
                "Yandex Music returned invalid JSON",
                "Could not parse the Yandex Music playlist page.",
            ) from e

    def _get_text(
        self,
        url: str,
        ref: YandexPlaylistReference,
    ) -> str:
        last_captcha_error: Optional[ServiceError] = None

        for attempt in range(1, self.SHARE_PAGE_ATTEMPTS + 1):
            session = self._session if attempt == 1 else requests.Session()
            try:
                response = session.get(
                    url,
                    timeout=self.REQUEST_TIMEOUT_SECONDS,
                    headers=self._request_headers(ref, accept_json=False),
                )
                if "showcaptcha" in response.url:
                    last_captcha_error = ServiceError(
                        "Yandex Music requested captcha for shared playlist page",
                        "Yandex Music requested captcha while opening the shared playlist link.",
                    )
                    logger.warning(
                        "Yandex Music share page returned captcha on attempt %s/%s",
                        attempt,
                        self.SHARE_PAGE_ATTEMPTS,
                    )
                    if attempt < self.SHARE_PAGE_ATTEMPTS:
                        time.sleep(0.4)
                        continue
                    raise last_captcha_error

                response.raise_for_status()
                self._session = session
                return response.text
            except requests.Timeout as e:
                raise ServiceError(
                    "Yandex Music request timed out",
                    "Yandex Music did not respond in time.",
                ) from e
            except requests.HTTPError as e:
                status_code = e.response.status_code if e.response is not None else None
                if status_code in {403, 404}:
                    raise ServiceError(
                        f"Yandex Music playlist is unavailable: HTTP {status_code}",
                        "The Yandex Music playlist is unavailable or private.",
                    ) from e
                raise ServiceError(
                    f"Yandex Music request failed: HTTP {status_code}",
                    "Could not load the Yandex Music playlist.",
                ) from e
            except requests.RequestException as e:
                raise ServiceError(
                    f"Yandex Music network error: {e}",
                    "Network error while loading the Yandex Music playlist.",
                ) from e

        if last_captcha_error:
            raise last_captcha_error

        raise ServiceError(
            "Failed to load Yandex Music shared playlist page",
            "Could not load the shared Yandex Music playlist page.",
        )

    def _request_headers(
        self,
        ref: YandexPlaylistReference,
        accept_json: bool = True,
    ) -> Dict[str, str]:
        if accept_json:
            referer = self._canonical_playlist_url(ref)
            return {
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": referer,
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                ),
                "X-Requested-With": "XMLHttpRequest",
                "X-Retpath-Y": referer,
            }

        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "User-Agent": "Mozilla/5.0",
        }

    def _canonical_playlist_url(self, ref: YandexPlaylistReference) -> str:
        if ref.owner and ref.kind:
            return f"https://{ref.host}/users/{ref.owner}/playlists/{ref.kind}"
        return ref.original_url

    @staticmethod
    def _language_from_host(host: str) -> str:
        return "en" if host.endswith(".com") else "ru"

    @staticmethod
    def _extract_playlist_title(playlist_data: Dict[str, Any]) -> str:
        title = playlist_data.get("title")
        if isinstance(title, str) and title.strip():
            return title.strip()
        return "Yandex Music Playlist"

    def _extract_raw_tracks(
        self,
        playlist_data: Dict[str, Any],
        ref: YandexPlaylistReference,
    ) -> List[Dict[str, Any]]:
        tracks = self._normalize_track_items(playlist_data.get("tracks", []))
        track_entries = self._extract_track_entries(playlist_data)

        if track_entries and len(tracks) < len(track_entries):
            present_ids = {
                str(track.get("id"))
                for track in tracks
                if track.get("id") is not None
            }
            missing_entries = [
                entry
                for entry in track_entries
                if entry.split(":", 1)[0] not in present_ids
            ]
            tracks.extend(self._load_missing_tracks(missing_entries, ref))

        return tracks

    def _load_missing_tracks(
        self,
        track_ids: List[str],
        ref: YandexPlaylistReference,
    ) -> List[Dict[str, Any]]:
        if not track_ids:
            return []

        endpoint = f"https://{ref.host}/handlers/track-entries.jsx"
        tracks: List[Dict[str, Any]] = []

        for batch_start in range(0, len(track_ids), self.TRACK_ENTRIES_BATCH_SIZE):
            batch = track_ids[batch_start:batch_start + self.TRACK_ENTRIES_BATCH_SIZE]
            params = {
                "entries": ",".join(batch),
                "lang": self._language_from_host(ref.host),
                "external-domain": ref.host,
                "overembed": "false",
                "strict": "true",
            }

            data = self._get_json(endpoint, params=params, ref=ref)
            tracks.extend(self._normalize_track_entries_response(data))

        return tracks

    def _normalize_track_entries_response(self, data: Any) -> List[Dict[str, Any]]:
        if isinstance(data, list):
            return self._normalize_track_items(data)

        if isinstance(data, dict):
            for key in ("tracks", "entries", "trackEntries"):
                if isinstance(data.get(key), list):
                    return self._normalize_track_items(data[key])

        logger.warning("Yandex Music missing tracks response has unexpected format")
        return []

    @staticmethod
    def _normalize_track_items(raw_items: Any) -> List[Dict[str, Any]]:
        if not isinstance(raw_items, list):
            return []

        tracks = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            track = item.get("track") if isinstance(item.get("track"), dict) else item
            if track:
                tracks.append(track)
        return tracks

    @staticmethod
    def _extract_track_entries(playlist_data: Dict[str, Any]) -> List[str]:
        raw_ids = playlist_data.get("trackIds") or playlist_data.get("track_ids")
        if not isinstance(raw_ids, list):
            return []

        entries = []
        for raw_id in raw_ids:
            if isinstance(raw_id, dict):
                value = raw_id.get("id") or raw_id.get("trackId")
                album_id = raw_id.get("albumId") or raw_id.get("album_id")
                if value is not None and album_id is not None:
                    value = f"{value}:{album_id}"
            else:
                value = raw_id

            if value is not None:
                entries.append(str(value))

        return entries

    @staticmethod
    def _map_track(raw_track: Dict[str, Any]) -> Track:
        title = raw_track.get("title") or raw_track.get("name") or "Unknown"
        artists = YandexMusicService._extract_artist_names(raw_track)
        albums = raw_track.get("albums") if isinstance(raw_track.get("albums"), list) else []
        album_data = albums[0] if albums and isinstance(albums[0], dict) else {}

        duration_ms = raw_track.get("durationMs") or raw_track.get("duration_ms")
        duration = None
        if duration_ms is not None:
            try:
                duration = float(duration_ms) / 1000
            except (TypeError, ValueError):
                duration = None
        elif raw_track.get("duration") is not None:
            try:
                duration = float(raw_track["duration"])
            except (TypeError, ValueError):
                duration = None

        return Track(
            title=str(title),
            artists=artists,
            album=album_data.get("title") or raw_track.get("album"),
            year=YandexMusicService._extract_year(raw_track, album_data),
            duration=duration,
        )

    @staticmethod
    def _extract_artist_names(raw_track: Dict[str, Any]) -> List[str]:
        raw_artists = raw_track.get("artists")
        if not isinstance(raw_artists, list):
            return []

        artists = []
        for artist in raw_artists:
            if isinstance(artist, dict) and artist.get("name"):
                artists.append(str(artist["name"]))
            elif isinstance(artist, str):
                artists.append(artist)
        return artists

    @staticmethod
    def _extract_year(raw_track: Dict[str, Any], album_data: Dict[str, Any]) -> Optional[int]:
        for value in (
            album_data.get("year"),
            raw_track.get("year"),
            album_data.get("releaseDate"),
            raw_track.get("releaseDate"),
        ):
            year = YandexMusicService._coerce_year(value)
            if year is not None:
                return year
        return None

    @staticmethod
    def _coerce_year(value: Any) -> Optional[int]:
        if value is None:
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, str) and len(value) >= 4:
            try:
                return int(value[:4])
            except ValueError:
                return None

        return None
