#!/usr/bin/env python3
"""
Interactive Spotify API Test Script

This script allows you to test Spotify API functionality interactively:
- Authenticate with your Spotify account (opens browser)
- List your playlists
- View tracks in a playlist
- Create new playlists
- Add tracks to playlists

Run: python3 test_spotify_interactive.py
"""

import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from src.model.services.providers.spotify.factory import SpotifyServiceFactory
from src.model.services.providers.spotify.config import SpotifyConfig, SpotifySetupWizard
from src.model.entities.playlist import Playlist
from src.model.entities.track import Track


class SpotifyTestInteractive:
    """Interactive Spotify API test interface"""

    def __init__(self):
        """Initialize the test interface"""
        self.spotify = None
        self.current_playlist_name = None

    def print_header(self, text):
        """Print a formatted header"""
        print("\n" + "=" * 60)
        print(f"  {text}")
        print("=" * 60 + "\n")

    def print_menu(self, options):
        """Print a menu of options"""
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        print(f"  0. Exit\n")

    def get_choice(self, prompt="Choose option: "):
        """Get user choice"""
        while True:
            try:
                choice = input(prompt).strip()
                return int(choice)
            except ValueError:
                print("Invalid input. Please enter a number.\n")

    def setup_spotify(self):
        """Setup Spotify service with credentials"""
        self.print_header("SPOTIFY SETUP")

        print("Before you start, make sure you have:")
        print("  1. Spotify app credentials from https://developer.spotify.com/dashboard")
        print("  2. Spotify Developer Dashboard: Set Redirect URI to:")
        print("     https://localhost:8888/callback\n")

        print("Would you like to:")
        print("  1. Use environment variables (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)")
        print("  2. Use config file (.spotify_config.json)")
        print("  3. Interactive setup wizard")
        print()

        choice = self.get_choice("Choose setup method: ")

        try:
            if choice == 1:
                # Load from environment
                client_id = os.environ.get("SPOTIFY_CLIENT_ID")
                client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

                if not client_id or not client_secret:
                    print("❌ Environment variables not set!")
                    print("\nSet them with:")
                    print("  export SPOTIFY_CLIENT_ID='your_client_id'")
                    print("  export SPOTIFY_CLIENT_SECRET='your_client_secret'")
                    return False

                self.spotify = SpotifyServiceFactory.create(
                    client_id=client_id,
                    client_secret=client_secret,
                )
                print("✓ Loaded from environment variables")
                return True

            elif choice == 2:
                # Load from config file
                config = SpotifyConfig.from_file()
                if not config:
                    print("❌ .spotify_config.json not found!")
                    return False

                if not config.is_valid():
                    print("❌ Invalid configuration!")
                    return False

                self.spotify = SpotifyServiceFactory.create(
                    client_id=config.client_id,
                    client_secret=config.client_secret,
                    redirect_uri=config.redirect_uri,
                )
                print("✓ Loaded from .spotify_config.json")
                return True

            elif choice == 3:
                # Interactive setup
                config = SpotifySetupWizard.run()
                self.spotify = SpotifyServiceFactory.create(
                    client_id=config.client_id,
                    client_secret=config.client_secret,
                    redirect_uri=config.redirect_uri,
                )
                print("✓ Configuration complete")
                return True

            else:
                print("Invalid choice")
                return False

        except Exception as e:
            print(f"❌ Error: {e}")
            return False

    def authenticate(self):
        """Authenticate with Spotify"""
        if not self.spotify:
            print("❌ Spotify service not initialized")
            return False

        self.print_header("SPOTIFY AUTHENTICATION")
        print("🔓 Opening browser for authentication...")
        print("Please log in with your Spotify account\n")

        try:
            self.spotify.authenticate()
            print("✓ Successfully authenticated!")
            return True
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            print("\nTroubleshooting:")
            print("  1. Make sure your Client ID and Secret are correct")
            print("  2. Check that the Redirect URI matches in Spotify Dashboard")
            print("  3. Try again with correct credentials")
            return False

    def list_playlists(self):
        """List all playlists"""
        if not self.spotify:
            print("❌ Not connected")
            return

        self.print_header("YOUR PLAYLISTS")

        try:
            playlists = self.spotify.get_playlists()

            if not playlists:
                print("No playlists found")
                return

            print(f"Found {len(playlists)} playlists:\n")

            for i, playlist in enumerate(playlists, 1):
                print(f"  {i:2}. {playlist.name}")

            print()

        except Exception as e:
            print(f"❌ Error: {e}")

    def view_playlist_tracks(self):
        """View tracks in a playlist"""
        if not self.spotify:
            print("❌ Not connected")
            return

        self.print_header("VIEW PLAYLIST TRACKS")

        # Get playlist name
        playlist_name = input("Enter playlist name (or leave blank for last used): ").strip()

        if not playlist_name:
            if self.current_playlist_name:
                playlist_name = self.current_playlist_name
            else:
                print("No playlist name provided")
                return

        self.current_playlist_name = playlist_name

        try:
            playlist = Playlist(name=playlist_name, tracks=None)
            tracks = self.spotify.get_tracks_from_playlist(playlist)

            if not tracks:
                print(f"No tracks found in '{playlist_name}'")
                return

            print(f"Tracks in '{playlist_name}' ({len(tracks)} total):\n")

            # Show first 20
            for i, track in enumerate(tracks[:20], 1):
                artists = ", ".join(track.artists) if track.artists else "Unknown"
                duration = f"{int(track.duration) // 60}:{int(track.duration) % 60:02d}" if track.duration else "?"
                print(f"  {i:2}. {track.title}")
                print(f"      {artists} • {duration}")

            if len(tracks) > 20:
                print(f"\n  ... and {len(tracks) - 20} more")

            print()

        except ValueError as e:
            # Playlist not found - show available playlists
            print(f"❌ {str(e)}")
            print("\nAvailable playlists:")
            try:
                playlists = self.spotify.get_playlists()
                for i, playlist in enumerate(playlists[:10], 1):
                    print(f"  {i:2}. {playlist.name}")
                if len(playlists) > 10:
                    print(f"  ... and {len(playlists) - 10} more")
            except Exception:
                pass
            print()
        except Exception as e:
            print(f"❌ Error: {e}")

    def create_playlist(self):
        """Create a new playlist"""
        if not self.spotify:
            print("❌ Not connected")
            return

        self.print_header("CREATE PLAYLIST")

        playlist_name = input("Enter new playlist name: ").strip()

        if not playlist_name:
            print("Playlist name cannot be empty")
            return

        try:
            playlist = Playlist(name=playlist_name, tracks=None)
            self.spotify.add_playlist(playlist)
            print(f"✓ Playlist '{playlist_name}' created successfully!")
            print()

        except Exception as e:
            print(f"❌ Error: {e}")

    def add_track_to_playlist(self):
        """Add a track to a playlist"""
        if not self.spotify:
            print("❌ Not connected")
            return

        self.print_header("ADD TRACK TO PLAYLIST")

        # Get playlist name
        playlist_name = input("Enter playlist name: ").strip()
        if not playlist_name:
            print("Playlist name cannot be empty")
            return

        # Get track info
        print("\nEnter track information:")
        title = input("Track title: ").strip()
        if not title:
            print("Track title cannot be empty")
            return

        artist = input("Artist: ").strip() or "Unknown"
        album = input("Album (optional): ").strip() or None

        try:
            track = Track(
                title=title,
                artists=[artist],
                album=album,
                year=None,
                duration=None,
            )

            playlist = Playlist(name=playlist_name, tracks=None)
            self.spotify.add_track_to_playlist(playlist, track)
            print(f"\n✓ Track '{title}' added to '{playlist_name}'!")
            print()

        except Exception as e:
            print(f"❌ Error: {e}")

    def show_service_info(self):
        """Show Spotify service info"""
        if not self.spotify:
            print("❌ Not connected")
            return

        self.print_header("SERVICE INFORMATION")

        info = self.spotify.get_service_info()
        print(f"Service: {info.name}")
        print(f"Icon: {info.icon_path}")
        print()

    def main_menu(self):
        """Main menu loop"""
        while True:
            self.print_header("SPOTIFY API INTERACTIVE TEST")

            if not self.spotify:
                print("⚠️  Not yet connected\n")
                options = [
                    "Setup Spotify Service",
                ]
            else:
                print("✓ Connected to Spotify\n")
                options = [
                    "Authenticate",
                    "List Playlists",
                    "View Playlist Tracks",
                    "Create Playlist",
                    "Add Track to Playlist",
                    "Show Service Info",
                ]

            self.print_menu(options)
            choice = self.get_choice("Choose option: ")

            if choice == 0:
                print("Goodbye! 👋\n")
                break

            if not self.spotify:
                if choice == 1:
                    success = self.setup_spotify()
                    if not success:
                        print("\nTry again with correct credentials.\n")
            else:
                if choice == 1:
                    self.authenticate()
                elif choice == 2:
                    self.list_playlists()
                elif choice == 3:
                    self.view_playlist_tracks()
                elif choice == 4:
                    self.create_playlist()
                elif choice == 5:
                    self.add_track_to_playlist()
                elif choice == 6:
                    self.show_service_info()
                else:
                    print("Invalid choice\n")

            if choice != 0:
                input("Press Enter to continue...")


def main():
    """Main entry point"""
    print("\n╔════════════════════════════════════════╗")
    print("║   Spotify API Interactive Test        ║")
    print("╚════════════════════════════════════════╝")

    tester = SpotifyTestInteractive()

    try:
        tester.main_menu()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye! 👋\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
