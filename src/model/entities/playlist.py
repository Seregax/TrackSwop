from dataclasses import dataclass
from typing import List

from src.model.entities.track import Track


@dataclass
class Playlist:
    name: str
    tracks: List[Track]
