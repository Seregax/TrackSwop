"""Yandex Music service factory."""

from typing import Optional

from src.model.services.providers.yandex.yandex_service import YandexMusicService


class YandexMusicServiceFactory:
    """Factory for creating Yandex Music service instances."""

    @staticmethod
    def create(playlist_url: Optional[str] = None) -> YandexMusicService:
        """
        Create a Yandex Music service instance.

        Args:
            playlist_url: Public playlist share link.

        Returns:
            YandexMusicService instance.
        """
        return YandexMusicService(playlist_url=playlist_url)
