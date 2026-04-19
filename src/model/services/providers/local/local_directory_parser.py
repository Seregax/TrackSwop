from pathlib import Path
from typing import List, Optional
from mutagen import File as MutagenFile
import re

from src.common.logger import get_logger
from src.model.entities.track import Track

logger = get_logger(__name__)


class LocalDirectoryParser:

    AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".m4a", ".ogg"}
    SITE_NOISE_DOMAINS = {
        "zaycev.net",
        "muzofond.fm",
        "mp3party.net",
        "hitmo.org",
        "musify.club",
        "muzmo.su",
        "pesni.net",
        "mp3xa.cc",
        "mp3poisk.net",
        "ru-music.com",
        "mp3uks.ru",
        "mp3bob.ru",
        "mp3cc.biz",
        "mp3no.net",
        "hotplayer.ru",
    }
    DASH_PATTERN = re.compile(r"\s+[-–—]\s+")
    DOMAIN_PATTERN_TEXT = (
        r"\b(?:[a-z0-9-]+\.)+(?:ru|su|com|net|org|fm|club|cc|biz|info)\b"
    )
    DOMAIN_PATTERN = re.compile(
        DOMAIN_PATTERN_TEXT,
        re.IGNORECASE,
    )
    LEADING_TRACK_NUMBER_PATTERN = re.compile(
        r"^\s*(?:\d{1,3}[\s._-]+)+(?=\D)"
    )
    EXTRA_SPACES_PATTERN = re.compile(r"\s+")

    def parse_directory(self, directory: Path) -> List[Track]:
        """
        Parse directory for audio files.

        Args:
            directory: Path to directory to parse

        Returns:
            List of Track objects
        """
        directory = Path(directory)
        if not directory.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")

        tracks: List[Track] = []

        try:
            file_paths = sorted(directory.iterdir(), key=lambda path: path.name.lower())
        except OSError as e:
            raise ValueError(f"Cannot read directory: {directory}") from e

        for file_path in file_paths:

            # Skip non-files
            if not file_path.is_file():
                continue

            if file_path.name.startswith("."):
                continue

            # Skip unsupported file formats
            if file_path.suffix.lower() not in self.AUDIO_EXTENSIONS:
                continue

            try:
                if file_path.stat().st_size == 0:
                    logger.debug("Skipping empty audio file: %s", file_path)
                    continue
            except OSError as e:
                logger.warning("Cannot read file metadata for %s: %s", file_path, e)
                continue

            track = self._parse_file(file_path)

            if track:
                tracks.append(track)

        return tracks

    def _parse_file(self, file_path: Path) -> Optional[Track]:

        try:
            audio = MutagenFile(file_path)

            if audio is None:
                logger.debug("Mutagen could not read audio file: %s", file_path)

            tags = audio.tags if audio else None

            duration = getattr(getattr(audio, "info", None), "length", None) if audio else None

            title = self._get_tag(tags, ["TIT2", "title"])
            artists = self._get_artists(tags)
            album = self._get_tag(tags, ["TALB", "album"])
            year = self._get_year(tags)
            filename_title, filename_artists = self._parse_filename(file_path.stem)

            if not title:
                title = filename_title

            if not artists:
                artists = filename_artists

            return Track(
                title=title,
                artists=artists,
                album=album,
                year=year,
                duration=duration,
            )

        except Exception as e:
            logger.warning("Skipping audio file %s: %s", file_path, e)
            return None

    def _get_tag(self, tags, keys: List[str]) -> Optional[str]:

        if not tags:
            return None

        for key in keys:
            if key in tags:
                value = tags[key]

                normalized = self._normalize_tag_value(value)

                if normalized:
                    return normalized

        return None

    def _get_artists(self, tags) -> List[str]:

        artist = self._get_tag(tags, ["TPE1", "artist"])

        if not artist:
            return []

        return self._split_artists(artist)

    def _get_year(self, tags) -> Optional[int]:


        year = self._get_tag(tags, ["TDRC", "date", "year"])

        if not year:
            return None

        try:
            return int(str(year)[:4])
        except ValueError:
            return None

    def _parse_filename(self, stem: str) -> tuple[str, List[str]]:
        cleaned = self._clean_filename_stem(stem)

        if not cleaned:
            return stem.strip(), []

        parts = [part.strip() for part in self.DASH_PATTERN.split(cleaned) if part.strip()]

        if len(parts) >= 2:
            title = parts[-1]
            artist = " - ".join(parts[:-1])
            return title, self._split_artists(artist)

        return cleaned, []

    def _clean_filename_stem(self, stem: str) -> str:
        cleaned = stem.replace("_", " ")
        cleaned = self.LEADING_TRACK_NUMBER_PATTERN.sub("", cleaned)
        cleaned = self._remove_site_noise_in_brackets(cleaned)
        cleaned = self._remove_edge_site_noise(cleaned)
        cleaned = cleaned.strip(" -–—._")
        return self._normalize_spaces(cleaned)

    def _remove_site_noise_in_brackets(self, value: str) -> str:
        def replace_if_site(match: re.Match) -> str:
            content = match.group(1).strip()
            if self._is_site_noise(content):
                return " "
            return match.group(0)

        value = re.sub(r"\(([^()]*)\)", replace_if_site, value)
        return re.sub(r"\[([^\[\]]*)\]", replace_if_site, value)

    def _remove_edge_site_noise(self, value: str) -> str:
        cleaned = value

        while True:
            updated = re.sub(
                r"(?i)^\s*(?:[-–—._\s]*)(?:"
                + self._site_noise_regex()
                + r")\s*[-–—._\s]*",
                "",
                cleaned,
            )
            updated = re.sub(
                r"(?i)\s*[-–—._\s]*(?:"
                + self._site_noise_regex()
                + r")\s*$",
                "",
                updated,
            )

            if updated == cleaned:
                return updated

            cleaned = updated

    def _is_site_noise(self, value: str) -> bool:
        normalized = value.strip().lower()

        if normalized in self.SITE_NOISE_DOMAINS:
            return True

        return bool(self.DOMAIN_PATTERN.fullmatch(normalized))

    def _site_noise_regex(self) -> str:
        domains = [re.escape(domain) for domain in self.SITE_NOISE_DOMAINS]
        domains.append(self.DOMAIN_PATTERN_TEXT)
        return "|".join(domains)

    def _normalize_tag_value(self, value) -> Optional[str]:
        if value is None:
            return None

        if isinstance(value, list):
            values = [
                normalized
                for item in value
                if (normalized := self._normalize_tag_value(item))
            ]
            return ", ".join(values) if values else None

        if hasattr(value, "text"):
            return self._normalize_tag_value(value.text)

        text = str(value).strip()

        if not text or text.lower() == "none":
            return None

        return self._normalize_spaces(text)

    def _split_artists(self, artist: str) -> List[str]:
        normalized = self._normalize_spaces(artist)
        normalized = re.sub(r"(?i)\s+(?:feat\.?|ft\.?)\s+", ",", normalized)
        normalized = re.sub(r"\s*(?:,|;|/|&)\s*", ",", normalized)

        return [
            part.strip()
            for part in normalized.split(",")
            if part.strip()
        ]

    def _normalize_spaces(self, value: str) -> str:
        return self.EXTRA_SPACES_PATTERN.sub(" ", value).strip()
