# TrackSwop

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

TrackSwop is an extensible application for importing, exporting, and managing music playlists across multiple streaming platforms (e.g., Spotify, VK, etc.). It provides a unified abstraction layer over different music service APIs and a modular provider-based architecture.

---

## Table of Contents

* [Description](#description)
* [Target Users](#target-users)
* [Goals](#goals)
* [Key Features](#key-features)
* [Installation](#installation)
* [Usage](#usage)
* [Tech Stack](#tech-stack)
* [Architecture Overview](#architecture-overview)
* [Project Structure](#project-structure)
* [Infrastructure](#infrastructure)
* [Configuration](#configuration)
* [Logging](#logging)
* [Tests](#tests)
* [Development Guide](#development-guide)
* [Project Status](#project-status)
* [License](#license)
* [Author](#author)
* [Contributing](#contributing)
* [Feedback](#feedback)

---

## Description

TrackSwop simplifies playlist migration and synchronization between music streaming platforms. It abstracts provider-specific API logic behind a consistent interface and allows new services to be integrated without modifying core application logic.

---

## Target Users

* Developers building integrations with music streaming services
* Users migrating playlists between platforms (e.g., Spotify ↔ VK)
* Desktop applications requiring unified music service abstraction
* Projects that need a plugin-based provider architecture

---

## Goals

* Provide a unified interface for multiple music services
* Enable reliable playlist import and export across platforms
* Ensure secure storage and handling of authentication tokens
* Support extensible provider-based architecture
* Maintain testable, modular, and maintainable codebase

---

## Key Features

* Dynamic form generation from provider specifications
* Secure token storage with encryption (Fernet)
* Plugin-based provider architecture
* Cross-platform playlist import/export
* Track parsing and metadata normalization
* Progress tracking and basic statistics

---

## Installation

### Requirements

* Python 3.9 or higher

### Setup

```bash id="q8v2wm"
git clone https://github.com/Seregax/TrackSwop.git
cd TrackSwop

python -m venv venv
source venv/bin/activate  # Linux / macOS
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### Development dependencies (optional)

```bash id="k3n9fp"
pip install -r requirements.dev.txt
```

---

## Usage

Run the application:

```bash id="z1m7qv"
python src/main.py
```

---

## Tech Stack

* Python 3.x
* PySide6 (UI framework)
* Spotipy (Spotify API client)
* vk_api (VK API integration)
* Redis (optional infrastructure layer)
* Requests (HTTP client)
* Cryptography (secure token storage)
* Mutagen (audio metadata processing)

---

## Architecture Overview

TrackSwop is built using a modular layered architecture:

* **Presentation Layer**: UI components and ViewModels (MVVM pattern)
* **Domain Layer**: Core entities (Playlist, Track)
* **Service Layer**: Music service providers (Spotify, VK, etc.)
* **Infrastructure Layer**: Token storage, configuration, logging

### Core design principles

* Provider-based architecture for extensibility
* Separation of concerns across layers
* Dependency injection for testability
* Specification-driven UI generation

---

## Project Structure

```text id="r2t6kd"
src/
 ├── view/                     # UI layer (PySide6)
 ├── view_models/              # MVVM presentation logic
 ├── model/
 │   ├── entities/             # Domain models (Playlist, Track)
 │   ├── services/
 │   │   └── providers/        # Music service implementations
 │   ├── specifications/       # Auth / Import / Export specs
 │   └── store/                # Token storage (TokenStore)
 ├── common/
 │   └── config.py             # Application configuration
tests/
```

---

## Infrastructure

### TokenStore

Responsible for secure storage of authentication tokens:

* Tokens are encrypted before saving to disk
* Uses symmetric encryption (Fernet)
* Stored locally in `tokens.json`

### DynamicForm

Generates UI forms dynamically based on provider specifications:

* Reduces UI coupling with service logic
* Allows adding new providers without UI changes
* Driven by AuthSpec definitions

---

## Configuration

### Environment Variables

| Variable             | Description                      |
| -------------------- | -------------------------------- |
| TRACKSWOP_MASTER_KEY | Encryption key for token storage |

### Example configuration

```python id="p4x8ab"
Config(
    app_name="TrackSwop",
    version="0.1.0",
    log_level="INFO",
    token_store_path="tokens.json"
)
```

---

## Logging

Application logs are written to:

```text id="l0v9sd"
app.log
```

Log level can be configured via `Config.log_level`.

---

## Tests

The project includes unit tests for core components:

* Spotify service (authentication, playlist retrieval, track parsing)
* TokenStore (save, load, delete operations)

### Run tests

```bash id="t7c2mv"
pytest
```

or

```bash id="w9p1qn"
python -m unittest
```

---

## Development Guide

### Principles

* Modular and extensible architecture
* Provider-based integration system
* Strict separation between domain, service, and UI layers
* Test-driven development encouraged

### Adding a new provider

Each provider must implement:

* `get_service_info()`
* `authenticate()`
* `get_auth_specs()`
* `get_import_specs()`
* `get_export_specs()`

### Example

```python id="v3n8kp"
class MyMusicProvider:
    def get_service_info(self):
        ...

    def authenticate(self):
        ...

    def get_auth_specs(self):
        ...

    def get_import_specs(self):
        ...

    def get_export_specs(self):
        ...
```

---

## Project Status

Active development

* Core architecture implemented
* Spotify integration completed
* Token storage system implemented
* Unit tests for core services
* Additional providers and UI improvements in progress

---

## License

MIT License

Copyright (c) 2026 Seregax

Permission is hereby granted, free of charge, to use, copy, modify, and distribute this software under the terms of the license.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.

---

## Author

Seregax — main developer

---

## Contributing

Contributions are welcome.

For major changes, please open an issue first to discuss what you would like to change.

---

## Feedback

If you have suggestions or ideas, please open an issue:

https://github.com/Seregax/TrackSwop/issues
