from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Track:
    title: str
    artists: List[str]
    album: Optional[str]
    year: Optional[int]
    duration: Optional[float]
