"""Example usage of Spotify service"""

from src.model.services.providers.spotify.factory import SpotifyServiceFactory
from src.model.entities.playlist import Playlist
from src.model.entities.track import Track


def example_basic_auth():
    """Example: Basic authentication"""
    print("=== Basic Authentication ===\n")

    # Create Spotify service
    spotify = SpotifyServiceFactory.create(
        client_id="your_client_id",
        client_secret="your_client_secret",
    )

    # Authenticate (will open browser)
    print("Authenticating with Spotify...")
    try:
        spotify.authenticate()
        print("✓ Successfully authenticated!\n")
    except Exception as e:
        print(f"✗ Authentication failed: {e}\n")
        return


def example_list_playlists(spotify):
    """Example: List all user playlists"""
    print("=== List Playlists ===\n")

    try:
        playlists = spotify.get_playlists()
        print(f"Found {len(playlists)} playlists:\n")

        for i, playlist in enumerate(playlists[:5], 1):  # Show first 5
            print(f"{i}. {playlist.name}")

        if len(playlists) > 5:
            print(f"... and {len(playlists) - 5} more")

        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")


def example_get_playlist_tracks(spotify):
    """Example: Get tracks from a playlist"""
    print("=== Get Playlist Tracks ===\n")

    try:
        # First, get playlist name from user or use default
        playlist_name = "Liked Songs"

        playlist = Playlist(name=playlist_name, tracks=None)
        tracks = spotify.get_tracks_from_playlist(playlist)

        print(f"Tracks in '{playlist_name}':\n")

        for i, track in enumerate(tracks[:5], 1):  # Show first 5
            artists = ", ".join(track.artists) if track.artists else "Unknown"
            print(f"{i}. {track.title}")
            print(f"   Artist: {artists}")
            if track.album:
                print(f"   Album: {track.album}")
            print()

        if len(tracks) > 5:
            print(f"... and {len(tracks) - 5} more tracks")

        print()
    except Exception as e:
        print(f"✗ Error: {e}\n")


def example_create_playlist(spotify):
    """Example: Create a new playlist"""
    print("=== Create Playlist ===\n")

    try:
        playlist_name = "TrackSwop Export"
        playlist = Playlist(name=playlist_name, tracks=None)

        print(f"Creating playlist '{playlist_name}'...")
        spotify.add_playlist(playlist)
        print(f"✓ Playlist created successfully!\n")

    except Exception as e:
        print(f"✗ Error: {e}\n")


def example_add_track_to_playlist(spotify):
    """Example: Add a track to a playlist"""
    print("=== Add Track to Playlist ===\n")

    try:
        # Create a track
        track = Track(
            title="Bohemian Rhapsody",
            artists=["Queen"],
            album="A Night at the Opera",
            year=1975,
            duration=354.0,
        )

        playlist = Playlist(name="My Favorite Songs", tracks=None)

        print(f"Adding '{track.title}' by {track.artists[0]}...")
        print(f"to playlist '{playlist.name}'...\n")

        spotify.add_track_to_playlist(playlist, track)
        print("✓ Track added successfully!\n")

    except Exception as e:
        print(f"✗ Error: {e}\n")


def example_auth_specs(spotify):
    """Example: Get authentication specifications"""
    print("=== Authentication Specifications ===\n")

    specs = spotify.get_auth_specs()

    print("Required credentials:\n")
    for field in specs.get_fields():
        required_text = " *" if field.required else ""
        print(f"• {field.label}{required_text}")
        print(f"  Type: {field.field_type.value}")

        if field.help_text:
            print(f"  Help: {field.help_text}")

        if field.default:
            print(f"  Default: {field.default}")

        print()


def example_complete_workflow(client_id: str, client_secret: str):
    """Example: Complete workflow"""
    print("╔════════════════════════════════════════╗")
    print("║   Spotify Integration - Full Example   ║")
    print("╚════════════════════════════════════════╝\n")

    # Create service
    spotify = SpotifyServiceFactory.create(
        client_id=client_id,
        client_secret=client_secret,
    )

    # Authenticate
    print("Step 1: Authentication")
    print("-" * 40)
    try:
        spotify.authenticate()
        print("✓ Authenticated successfully\n")
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        print("Get credentials from https://developer.spotify.com/dashboard\n")
        return

    # List playlists
    print("Step 2: List Playlists")
    print("-" * 40)
    example_list_playlists(spotify)

    # Get tracks from a playlist
    print("Step 3: Get Playlist Tracks")
    print("-" * 40)
    example_get_playlist_tracks(spotify)

    # Show auth specs
    print("Step 4: Authentication Specifications")
    print("-" * 40)
    example_auth_specs(spotify)

    print("╔════════════════════════════════════════╗")
    print("║          Example Complete!            ║")
    print("╚════════════════════════════════════════╝")


if __name__ == "__main__":
    # Replace with your actual credentials
    CLIENT_ID = "your_spotify_client_id"
    CLIENT_SECRET = "your_spotify_client_secret"

    if CLIENT_ID == "your_spotify_client_id":
        print("⚠️  Please set your Spotify credentials in this file")
        print("\nGet credentials from: https://developer.spotify.com/dashboard\n")
    else:
        example_complete_workflow(CLIENT_ID, CLIENT_SECRET)
