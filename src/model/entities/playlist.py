from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from src.model.entities.track import Track


@dataclass
class Playlist:
    name: str
    tracks: Optional[List[Track]] = None
    id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    description: Optional[str] = None
    track_count: Optional[int] = None
