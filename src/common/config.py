import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration"""
    
    # Application settings
    app_name: str = "TrackSwop"
    version: str = "0.1.0"
    log_level: str = "INFO"
    log_file: str = "app.log"
    
    # Token store settings
    token_store_path: str = "tokens.json"
    master_key: Optional[bytes] = None
    
    def __post_init__(self):
        """Load configuration from environment variables"""
        key = os.environ.get("TRACKSWOP_MASTER_KEY")
        if key:
            self.master_key = key.encode()
