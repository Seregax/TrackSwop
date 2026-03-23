from pathlib import Path
from typing import List, Optional
from mutagen import File as MutagenFile
from dataclasses import dataclass

from src.model.entities.track import Track


class LocalDirectoryParser:

    AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".m4a", ".ogg"}

    def parse_directory(self, directory: Path) -> List[Track]:
        """
        Parse directory for audio files.

        Args:
            directory: Path to directory to parse

        Returns:
            List of Track objects
        """
        tracks: List[Track] = []

        for file_path in directory.glob("*"):

            # Skip non-files
            if not file_path.is_file():
                continue

            # Skip unsupported file formats
            if file_path.suffix.lower() not in self.AUDIO_EXTENSIONS:
                continue

            track = self._parse_file(file_path)

            if track:
                tracks.append(track)

        return tracks

    def _parse_file(self, file_path: Path) -> Optional[Track]:

        try:
            audio = MutagenFile(file_path)

            if audio is None:
                return None

            tags = audio.tags

            duration = getattr(audio.info, "length", None)

            title = self._get_tag(tags, ["TIT2", "title"])
            artists = self._get_artists(tags)
            album = self._get_tag(tags, ["TALB", "album"])
            year = self._get_year(tags)

            # Title is required for Track creation in MVP
            if not title:
                title = file_path.stem

            return Track(
                title=title,
                artists=artists,
                album=album,
                year=year,
                duration=duration,
            )

        except Exception:
            # For MVP we silently ignore corrupted files
            return None

    def _get_tag(self, tags, keys: List[str]) -> Optional[str]:

        if not tags:
            return None

        for key in keys:
            if key in tags:
                value = tags[key]

                if isinstance(value, list):
                    return str(value[0])

                return str(value)

        return None

    def _get_artists(self, tags) -> List[str]:

        artist = self._get_tag(tags, ["TPE1", "artist"])

        if not artist:
            return []

        # Artists may be separated by commas
        return [a.strip() for a in artist.split(",")]

    def _get_year(self, tags) -> Optional[int]:


        year = self._get_tag(tags, ["TDRC", "date", "year"])

        if not year:
            return None

        try:
            return int(str(year)[:4])
        except ValueError:
            return None