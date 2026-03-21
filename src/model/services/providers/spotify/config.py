"""Spotify service configuration helper"""

import os
from typing import Optional, Tuple
from pathlib import Path
import json


class SpotifyConfig:
    """Helper class for Spotify service configuration"""

    # Environment variable names
    ENV_CLIENT_ID = "SPOTIFY_CLIENT_ID"
    ENV_CLIENT_SECRET = "SPOTIFY_CLIENT_SECRET"
    ENV_REDIRECT_URI = "SPOTIFY_REDIRECT_URI"
    ENV_MASTER_KEY = "TRACKSWOP_MASTER_KEY"

    # Default values
    DEFAULT_REDIRECT_URI = "http://127.0.0.1:8888/callback"
    CONFIG_FILE = ".spotify_config.json"

    @classmethod
    def from_env(cls) -> Optional["SpotifyConfig"]:
        """Load configuration from environment variables"""
        client_id = os.environ.get(cls.ENV_CLIENT_ID)
        client_secret = os.environ.get(cls.ENV_CLIENT_SECRET)

        if not client_id or not client_secret:
            return None

        redirect_uri = os.environ.get(
            cls.ENV_REDIRECT_URI, cls.DEFAULT_REDIRECT_URI
        )

        return cls(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )

    @classmethod
    def from_file(cls, path: str = CONFIG_FILE) -> Optional["SpotifyConfig"]:
        """Load configuration from JSON file"""
        config_path = Path(path)

        if not config_path.exists():
            return None

        try:
            with config_path.open("r") as f:
                data = json.load(f)

            return cls(
                client_id=data.get("client_id"),
                client_secret=data.get("client_secret"),
                redirect_uri=data.get(
                    "redirect_uri", cls.DEFAULT_REDIRECT_URI
                ),
            )
        except Exception as e:
            print(f"Error reading config file: {e}")
            return None

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = DEFAULT_REDIRECT_URI,
    ):
        """Initialize Spotify configuration"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def save_to_file(self, path: str = CONFIG_FILE) -> None:
        """Save configuration to JSON file"""
        config_path = Path(path)

        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        }

        with config_path.open("w") as f:
            json.dump(data, f, indent=2)

        # Set permissions (user read/write only)
        config_path.chmod(0o600)

        print(f"Configuration saved to {path}")
        print("⚠️  Make sure to add this file to .gitignore!")

    def to_env_export(self) -> str:
        """Return shell export commands for environment variables"""
        return f"""
export {self.ENV_CLIENT_ID}="{self.client_id}"
export {self.ENV_CLIENT_SECRET}="{self.client_secret}"
export {self.ENV_REDIRECT_URI}="{self.redirect_uri}"
        """.strip()

    def is_valid(self) -> bool:
        """Check if configuration is valid"""
        return bool(self.client_id and self.client_secret)

    def __str__(self) -> str:
        """String representation"""
        return f"""
Spotify Configuration:
  Client ID: {self.client_id[:10]}...
  Redirect URI: {self.redirect_uri}
  Valid: {self.is_valid()}
        """.strip()


class SpotifySetupWizard:
    """Interactive setup wizard for Spotify configuration"""

    @staticmethod
    def run() -> SpotifyConfig:
        """Run the interactive setup wizard"""
        print("\n╔════════════════════════════════════════╗")
        print("║   Spotify Setup Wizard                 ║")
        print("╚════════════════════════════════════════╝\n")

        print("Before you start, you need to create a Spotify App:")
        print("1. Go to https://developer.spotify.com/dashboard")
        print("2. Log in with your Spotify account (create one if needed)")
        print("3. Create an app and get:")
        print("   - Client ID")
        print("   - Client Secret\n")

        # Get client ID
        print("Enter your Spotify credentials:")
        client_id = input("Client ID: ").strip()

        if not client_id:
            raise ValueError("Client ID is required")

        # Get client secret
        client_secret = input("Client Secret: ").strip()

        if not client_secret:
            raise ValueError("Client Secret is required")

        # Get redirect URI (optional)
        redirect_uri = input(
            f"Redirect URI ({SpotifyConfig.DEFAULT_REDIRECT_URI}): "
        ).strip()

        if not redirect_uri:
            redirect_uri = SpotifyConfig.DEFAULT_REDIRECT_URI

        # Create config
        config = SpotifyConfig(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
        )

        # Save option
        print("\n" + str(config))
        save = input("\nSave to .spotify_config.json? (y/n): ").strip().lower()

        if save == "y":
            config.save_to_file()
            print("\nConfiguration saved successfully!")

        print("\nYou can also set environment variables:")
        print(config.to_env_export())

        return config
