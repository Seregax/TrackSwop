"""
Service Registry Module

Provides centralized registry for all streaming service factories.
"""

from typing import Dict, Type, Optional, Any

from src.model.services.interfaces.istreaming_service import IStreamingService
from src.model.store.token_store import TokenStore

from src.common.logger import get_logger

logger = get_logger(__name__)

class ServiceRegistry:
    """
    Central registry for streaming service factories.
    
    Usage:
        registry = ServiceRegistry(token_store)
        service = registry.get_service("vk", auth_data)
    """
    
    def __init__(self, token_store: Optional[TokenStore] = None):
        """
        Initialize the service registry.
        
        Args:
            token_store: TokenStore instance for managing service tokens
        """
        self._factories: Dict[str, Type] = {}
        self._token_store = token_store
        self._service_instances: Dict[str, IStreamingService] = {}
        
        # Register built-in factories
        self._register_builtin_factories()
    
    def _register_builtin_factories(self):
        """Register all built-in service factories"""
        try:
            from src.model.services.providers.spotify.factory import SpotifyServiceFactory
            self._factories["spotify"] = SpotifyServiceFactory
        except ImportError as e:
            logger.warning(f"Could not register Spotify factory: {e}")

        try:
            from src.model.services.providers.vk.factory import VkServiceFactory
            self._factories["vk"] = VkServiceFactory
        except ImportError as e:
            logger.warning(f"Could not register VK factory: {e}")

        try:
            from src.model.services.providers.local.factory import LocalServiceFactory
            self._factories["local"] = LocalServiceFactory
        except ImportError as e:
            print(f"Warning: Could not register Local factory: {e}")
        try:
            from src.model.services.providers.yandex.factory import YandexMusicServiceFactory
            self._factories["yandex"] = YandexMusicServiceFactory
        except ImportError as e:
            print(f"Warning: Could not register Yandex Music factory: {e}")

    
    def register_factory(self, service_name: str, factory_class: Type):
        """
        Register a service factory.
        
        Args:
            service_name: Unique service identifier (e.g., "vk", "spotify")
            factory_class: Factory class with create() static method
        """
        self._factories[service_name] = factory_class
    
    def get_service(self, service_name: str, auth_data: Optional[Dict[str, Any]] = None) -> IStreamingService:
        """
        Get or create a service instance.

        Args:
            service_name: Service identifier (e.g., "vk", "spotify", "local")
            auth_data: Authentication data for the service (optional)

        Returns:
            IStreamingService instance

        Raises:
            ValueError: If service is not registered
        """
        if service_name not in self._factories:
            raise ValueError(f"Service '{service_name}' is not registered")

        factory_class = self._factories[service_name]

        # Create service instance based on factory type
        return self._create_service_from_factory(factory_class, service_name, auth_data)
    
    def _create_service_from_factory(
        self, 
        factory_class: Type, 
        service_name: str, 
        auth_data: Optional[Dict[str, Any]] = None
    ) -> IStreamingService:
        """
        Create service instance from factory.
        
        Args:
            factory_class: Factory class
            service_name: Service identifier
            auth_data: Authentication data
            
        Returns:
            IStreamingService instance
        """
        # For factories that accept token_store
        if service_name == "spotify":
            return factory_class.create(
                client_id=auth_data.get("client_id") if auth_data else "",
                client_secret=auth_data.get("client_secret") if auth_data else "",
                redirect_uri=auth_data.get("redirect_uri", "http://127.0.0.1:8888/callback") if auth_data else "http://127.0.0.1:8888/callback",
                token_store=self._token_store,
            )
        
        # For VK factory
        elif service_name == "vk":
            if auth_data:
                return factory_class.create(
                    token=auth_data.get("token"),
                    user_id=auth_data.get("user_id"),
                )
            return factory_class.create()
        
        # For Local factory
        elif service_name == "local":
            if auth_data and "directory" in auth_data:
                return factory_class.create(directory=auth_data.get("directory"))
            return factory_class.create()

        # For Yandex Music factory
        elif service_name == "yandex":
            if auth_data and "playlist_url" in auth_data:
                return factory_class.create(playlist_url=auth_data.get("playlist_url"))
            return factory_class.create()
        
        # Generic fallback
        return factory_class.create()
    
    def clear_cache(self, service_name: Optional[str] = None):
        """
        Clear cached service instances.
        
        Args:
            service_name: Specific service to clear, or None to clear all
        """
        if service_name:
            self._service_instances.pop(service_name, None)
        else:
            self._service_instances.clear()
    
    def get_available_services(self) -> list:
        """
        Get list of available service names.

        Returns:
            List of registered service names
        """
        return list(self._factories.keys())
    
    def is_service_available(self, service_name: str) -> bool:
        """
        Check if a service is registered.
        
        Args:
            service_name: Service identifier
            
        Returns:
            True if service is available
        """
        return service_name in self._factories
