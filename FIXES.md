# UI Freezing Issue - Fix Summary

## Problem
The UI was freezing while loading playlists after logging in to VK (and other services) because blocking network calls were being made on the main thread.

## Solution
Implemented multi-threaded loading using QThread workers to move heavy I/O operations off the main thread.

## Changes Made

### 1. Created Worker Threads

#### `/src/workers/playlists_loading_worker.py` (NEW)
- `PlaylistsLoadingWorker` class that extends `QThread`
- Loads playlists asynchronously from a service
- Emits `finished(List[Playlist])` signal on success
- Emits `error(str)` signal on failure
- Prevents UI freezing during playlist fetch

#### `/src/workers/tracks_loading_worker.py` (NEW)
- `TracksLoadingWorker` class that extends `QThread`
- Loads tracks from a playlist asynchronously
- Emits `finished(List[Track])` signal on success
- Emits `error(str)` signal on failure
- Prevents UI freezing when selecting and loading tracks

#### `/src/workers/__init__.py` (NEW)
- Module initialization file for the workers package

### 2. Updated Main Window UI

#### `/src/view/main_window.py` (MODIFIED)

**Imports Added:**
- `QProgressBar` for loading indicators
- `PlaylistsLoadingWorker`
- `TracksLoadingWorker`

**MainWindow Class Changes:**

1. **Worker Thread Management:**
   - Added `_playlist_loading_worker` attribute
   - Added `_tracks_loading_worker` attribute
   - Added `_loading_for_panel` to track which panel is loading

2. **Loading Indicators:**
   - Added `_create_loading_indicator()` method to create visual loading indicators
   - Loading indicator shows "⏳ Загрузка плейлистов..." message with animated progress bar
   - Added loading indicators for both source and destination panels

3. **Async Playlist Loading:**
   - Modified `_on_service_selected()` to call `_load_playlists_async()` instead of blocking load
   - Added `_load_playlists_async()` method to manage worker thread
   - Added `_show_loading_indicator()` to provide visual feedback
   - Added `_on_playlists_loaded_async()` to handle successful completion
   - Added `_on_playlists_loading_error()` to handle errors gracefully

4. **Async Tracks Loading:**
   - Modified `_on_playlist_selected()` to call `_load_tracks_async()` instead of blocking load
   - Added `_load_tracks_async()` method to manage worker thread
   - Added `_on_tracks_loaded_async()` to handle successful completion
   - Added `_on_tracks_loading_error()` to handle errors gracefully
   - Shows loading text in track count label while loading

### 3. Tests Added

#### `/tests/test_workers.py` (NEW)
- `TestPlaylistsLoadingWorker` class with tests for:
  - Successful playlist loading
  - Error handling during playlist loading
  
- `TestTracksLoadingWorker` class with tests for:
  - Successful tracks loading
  - Error handling during tracks loading

## Benefits

1. **Non-Blocking UI:** The main thread is never blocked by I/O operations
2. **Better UX:** Users see loading indicators while data is being fetched
3. **Error Handling:** Errors are gracefully handled with user-friendly messages
4. **Responsive Interface:** Users can interact with the UI while loading is in progress
5. **Thread Safety:** Proper use of Qt signals for thread-safe communication

## How It Works

### Playlist Loading Flow:
1. User authenticates with a service
2. `_on_service_selected()` is called
3. Auth succeeds, `_load_playlists_async()` creates a `PlaylistsLoadingWorker`
4. Loading indicator is shown (faded out playlist widget)
5. Worker thread fetches playlists in background
6. Worker emits `finished` signal when done
7. UI is updated with playlists
8. Loading indicator is hidden

### Tracks Loading Flow:
1. User selects a playlist
2. `_on_playlist_selected()` is called
3. `_load_tracks_async()` creates a `TracksLoadingWorker`
4. Track count label shows "⏳ Загрузка треков..."
5. Worker thread fetches tracks in background
6. Worker emits `finished` signal when done
7. Tracks table is populated
8. UI returns to normal state

## Potential Enhancements

1. Cancel loading button for long operations
2. Retry mechanism for failed loads
3. Timeout handling for stuck connections
4. Progress percentage indication for large playlists
5. Caching of loaded playlists to avoid re-fetching

## Testing

Run tests with:
```bash
python -m pytest tests/test_workers.py -v
```

Or with unittest:
```bash
python -m unittest tests.test_workers -v
```
