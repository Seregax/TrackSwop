"""
Main Window ViewModel

Central coordinator for all ViewModels and services.
"""

from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal

from src.model.store.token_store import TokenStore
from src.model.services.registry.service_registry import ServiceRegistry
from src.model.services.interfaces.istreaming_service import IStreamingService
from src.view.view_models.playlist_vm import PlaylistViewModel
from src.view.view_models.transfer_vm import TransferViewModel


class MainWindowViewModel(QObject):
    """
    Main ViewModel for MainWindow.
    
    Central coordinator that manages:
    - ServiceRegistry (single instance)
    - TokenStore
    - Child ViewModels
    - Authentication flow
    """
    
    # Signals
    source_service_changed = Signal(str)
    destination_service_changed = Signal(str)
    transfer_requested = Signal()
    authentication_started = Signal(str)  # service_name
    authentication_completed = Signal(str, bool)  # service_name, success
    
    def __init__(
        self,
        token_store: Optional[TokenStore] = None,
        parent=None
    ):
        super().__init__(parent)
        
        self._token_store = token_store
        self._service_registry = ServiceRegistry(token_store)
        
        # Auth state
        self._auth_services: Dict[str, IStreamingService] = {}  # service_name -> authenticated service
        
        # Create ViewModels (share the same service_registry)
        self._source_vm = PlaylistViewModel(service_name="source", parent=self)
        self._dest_vm = PlaylistViewModel(service_name="dest", parent=self)
        self._transfer_vm = TransferViewModel()
        
        # Connect signals
        self._source_vm.service_selected.connect(self._on_source_service_selected)
        self._dest_vm.service_selected.connect(self._on_destination_service_selected)
        
        # Track selected services
        self._source_service_name: str = ""
        self._dest_service_name: str = ""
    
    @property
    def source_vm(self) -> PlaylistViewModel:
        """Get source PlaylistViewModel"""
        return self._source_vm
    
    @property
    def dest_vm(self) -> PlaylistViewModel:
        """Get destination PlaylistViewModel"""
        return self._dest_vm
    
    @property
    def transfer_vm(self) -> TransferViewModel:
        """Get TransferViewModel"""
        return self._transfer_vm
    
    @property
    def service_registry(self) -> ServiceRegistry:
        """Get ServiceRegistry"""
        return self._service_registry
    
    @property
    def token_store(self) -> Optional[TokenStore]:
        """Get TokenStore"""
        return self._token_store
    
    def _on_source_service_selected(self, service: str):
        """Handle source service selection"""
        self._source_service_name = service
        self.source_service_changed.emit(service)
    
    def _on_destination_service_selected(self, service: str):
        """Handle destination service selection"""
        self._dest_service_name = service
        self.destination_service_changed.emit(service)
    
    def authenticate_service(self, service_name: str, auth_data: Dict[str, Any]) -> bool:
        """
        Authenticate a service.
        
        Args:
            service_name: Service name (e.g., "vk", "local")
            auth_data: Authentication data from form
            
        Returns:
            True if authentication successful
        """
        try:
            # Get service with auth data
            service = self._service_registry.get_service(service_name, auth_data)
            
            # Call authenticate (skip for local - already configured via directory)
            if service_name != "local":
                service.authenticate()
            
            # Save token if available
            if self._token_store and "token" in auth_data:
                self._token_store.save_token(service_name, auth_data["token"])
            
            # Cache authenticated service
            self._auth_services[service_name] = service
            
            self.authentication_completed.emit(service_name, True)
            return True
            
        except Exception as e:
            print(f"Authentication error for {service_name}: {e}")
            self.authentication_completed.emit(service_name, False)
            return False
    
    def get_authenticated_service(self, service_name: str) -> Optional[IStreamingService]:
        """
        Get authenticated service instance.
        
        Args:
            service_name: Service name
            
        Returns:
            Service instance or None
        """
        # Return cached authenticated service
        if service_name in self._auth_services:
            return self._auth_services[service_name]
        
        # Try to create with stored token
        token = self._token_store.get_token(service_name) if self._token_store else None
        if token:
            try:
                service = self._service_registry.get_service(
                    service_name,
                    {"token": token}
                )
                service.authenticate()
                self._auth_services[service_name] = service
                return service
            except Exception:
                pass
        
        return None
    
    def start_transfer(self):
        """
        Start transfer from source to destination.
        """
        # Get service names from ViewModels
        source_name = self._source_vm.selected_service
        dest_name = self._dest_vm.selected_service
        
        if not source_name or not dest_name:
            print("Error: Services not selected")
            return
        
        # Get authenticated services
        source_service = self.get_authenticated_service(source_name)
        dest_service = self.get_authenticated_service(dest_name)
        
        if not source_service or not dest_service:
            print("Error: Services not authenticated")
            return
        
        # Get playlist objects from ViewModels
        source_playlist = self._source_vm.current_playlist_object
        dest_playlist = self._dest_vm.current_playlist_object
        
        if not all([source_playlist, dest_playlist]):
            print("Error: Playlists not selected")
            return
        
        # Configure transfer VM
        self._transfer_vm.source_service = source_name
        self._transfer_vm.destination_service = dest_name
        self._transfer_vm.source_playlist = self._source_vm.current_playlist or ""
        self._transfer_vm.destination_playlist = self._dest_vm.current_playlist or ""
        
        self._transfer_vm.set_service_instances(
            source_service,
            dest_service,
            source_playlist,
            dest_playlist,
        )
        
        # Start transfer
        self._transfer_vm.start_transfer()
        self.transfer_requested.emit()
    
    def can_transfer(self) -> bool:
        """
        Check if transfer can be started.
        """
        return (
            self._source_vm.has_playlist_selected and
            self._dest_vm.has_playlist_selected and
            self.get_authenticated_service(self._source_vm.selected_service) is not None and
            self.get_authenticated_service(self._dest_vm.selected_service) is not None
        )
