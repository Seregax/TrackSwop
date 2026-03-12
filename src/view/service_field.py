from dataclasses import dataclass
from enum import Enum


class FieldType(Enum):
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"


@dataclass
class ServiceField:
    name: str
    field_type: FieldType
    label: str
