from dataclasses import dataclass
from typing import List, Optional

from src.model.entities.track import Track


@dataclass
class Playlist:
    name: str
    tracks: Optional[List[Track]]
