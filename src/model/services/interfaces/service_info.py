from dataclasses import dataclass
from typing import Optional


@dataclass
class ServiceInfo:
    name: str
    icon_path: Optional[str]
