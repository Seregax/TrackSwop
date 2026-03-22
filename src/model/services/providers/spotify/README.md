# Spotify Integration Guide

## Overview

The Spotify integration allows TrackSwop to authenticate with Spotify using OAuth2 and perform playlist and track operations.

## Setup Instructions

### 1. Create a Spotify App

1. Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Sign in with your Spotify account (create one if needed)
3. Click "Create an App"
4. Accept the terms and create the app
5. You'll get:
   - **Client ID**
   - **Client Secret**

### 2. Set Redirect URI

1. In your app settings, add a Redirect URI:
   - Default: `http://127.0.0.1:8888/callback`
   - Can be customized based on your setup

### 3. Configure Environment Variables (Optional)

Create a `.env` file or set environment variables:

```bash
export SPOTIFY_CLIENT_ID="your_client_id"
export SPOTIFY_CLIENT_SECRET="your_client_secret"
export SPOTIFY_REDIRECT_URI="http://127.0.0.1:8888/callback"
export TRACKSWOP_MASTER_KEY="your_encryption_key"  # For token encryption
```

## Usage

### Basic Authentication

```python
from src.model.services.providers.spotify.factory import SpotifyServiceFactory

# Create service instance
spotify = SpotifyServiceFactory.create(
    client_id="your_client_id",
    client_secret="your_client_secret",
    redirect_uri="http://127.0.0.1:8888/callback"
)

# Authenticate (opens browser for user login)
spotify.authenticate()
```

### List Playlists

```python
playlists = spotify.get_playlists()
for playlist in playlists:
    print(f"- {playlist.name}")
```

### Get Tracks from Playlist

```python
from src.model.entities.playlist import Playlist

playlist = Playlist(name="My Playlist", tracks=None)
tracks = spotify.get_tracks_from_playlist(playlist)

for track in tracks:
    print(f"{track.title} - {', '.join(track.artists)}")
```

### Create New Playlist

```python
from src.model.entities.playlist import Playlist

new_playlist = Playlist(name="TrackSwop Export", tracks=None)
spotify.add_playlist(new_playlist)
```

### Add Track to Playlist

```python
from src.model.entities.playlist import Playlist
from src.model.entities.track import Track

playlist = Playlist(name="My Playlist", tracks=None)
track = Track(
    title="Song Title",
    artists=["Artist Name"],
    album="Album Name",
    year=2024,
    duration=180.0
)

spotify.add_track_to_playlist(playlist, track)
```

## Features

### Authentication Methods

- **OAuth2 Flow**: User-friendly browser-based authentication
- **Token Caching**: First-time auth tokens are cached and reused
- **Token Encryption**: Tokens are encrypted using Fernet encryption
- **Token Validation**: Cached tokens are verified before use

### Playlist Operations

- ✅ Get all user playlists
- ✅ Get tracks from specific playlist
- ✅ Create new playlists
- ✅ Add tracks to playlists
- ✅ Export playlists to other services

### API Scopes

The service uses these OAuth2 scopes:

```python
SCOPES = [
    "playlist-read-private",        # Read private playlists
    "playlist-read-collaborative",  # Read collaborative playlists
    "playlist-modify-public",       # Create and modify public playlists
    "playlist-modify-private",      # Create and modify private playlists
]
```

## Advanced Configuration

### Custom Token Store

```python
from src.model.store.token_store import TokenStore

token_store = TokenStore(
    path="/custom/path/tokens.json",
    master_key=b"your_encryption_key"
)

spotify = SpotifyServiceFactory.create(
    client_id="...",
    client_secret="...",
    token_store=token_store
)
```

### Error Handling

```python
from spotipy.exceptions import SpotifyException

try:
    spotify.authenticate()
    playlists = spotify.get_playlists()
except SpotifyException as e:
    print(f"Spotify API error: {e}")
except Exception as e:
    print(f"Error: {e}")
```

## Authentication Specifications

Get auth form fields dynamically:

```python
auth_spec = spotify.get_auth_specs()

for field in auth_spec.get_fields():
    print(f"{field.label} ({field.field_type.value})")
    if field.required:
        print("  * Required")
    if field.help_text:
        print(f"  Help: {field.help_text}")
```

## Troubleshooting

### "Failed to obtain access token"

- Verify Client ID and Secret are correct
- Check that Redirect URI matches in app settings
- Ensure user approved the OAuth2 scope request

### "Cached token is invalid"

- Token has expired
- User revoked access in Spotify settings
- Token store was corrupted

Solution: Re-authenticate to get a new token

### "Playlist not found"

- Playlist name is case-sensitive in some cases
- Try exact playlist name from Spotify

## Implementation Details

### File Structure

```
src/model/services/providers/spotify/
├── __init__.py
├── spotify_service.py    # Main service implementation
├── factory.py            # Service factory
└── README.md            # This file
```

### Token Storage

Tokens are stored in `tokens.json`:

```json
{
  "spotify": "encrypted_access_token"
}
```

- Encrypted using Fernet (symmetric encryption)
- File location: configurable via TokenStore
- Encryption key: from `TRACKSWOP_MASTER_KEY` environment variable

### Pagination Handling

- All list operations handle Spotify API pagination automatically
- No need to manually request next pages

### Track Searching

When adding tracks, the service:

1. Searches Spotify by track title and artist
2. Returns first matching track
3. Logs warning if track not found

## Security Considerations

1. **Never commit credentials** to version control
2. **Use environment variables** for sensitive data
3. **Tokens are encrypted** at rest in tokens.json
4. **Redirect URI should be HTTPS** in production
5. **Client Secret** should never be exposed in client-side code

## API Limits

Spotify API has rate limits:

- Standard API: 429 rate limit responses
- The `spotipy` library handles automatic retries
- Batch operations recommended for large playlists

## References

- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
- [Spotipy Library](https://spotipy.readthedocs.io/)
- [OAuth2 Flow](https://developer.spotify.com/documentation/general/guides/authorization/)
