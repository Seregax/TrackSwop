
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Track:
    title: str
    artists: List[str]
    album: Optional[str] = None
    year: Optional[int] = None
    duration: Optional[float] = None
    id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
