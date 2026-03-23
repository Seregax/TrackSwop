"""VK Music service factory"""

from typing import Optional
from src.model.services.providers.vk.vk_service import VkService


class VkServiceFactory:
    """Factory for creating VK Music service instances"""

    @staticmethod
    def create(
        token: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> VkService:
        """
        Create a VK Music service instance.

        Args:
            token: VK access token (optional, can be set via authenticate())
            user_id: VK user ID (optional, can be set via authenticate())

        Returns:
            VkService instance
        """
        service = VkService()
        
        if token and user_id:
            service.set_auth_data(token, user_id)
        
        return service
