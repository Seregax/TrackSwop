"""Local service factory"""

from typing import Optional
from src.model.services.providers.local.local_service import LocalService


class LocalServiceFactory:
    """Factory for creating Local service instances"""

    @staticmethod
    def create(directory: Optional[str] = None) -> LocalService:
        """
        Create a Local service instance.

        Args:
            directory: Path to music directory (optional, can be set via authenticate())

        Returns:
            LocalService instance
        """
        return LocalService(directory=directory)
