from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Callable


class FieldType(Enum):
    STRING = "string"
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    FOLDER = "folder"
    FILE = "file"
    CHOICE = "choice"
    MULTI_CHOICE = "multi_choice"
    PASSWORD = "password"


@dataclass
class Field:
    name: str
    label: str
    field_type: FieldType
    required: bool = False
    default: Any = None
    placeholder: str = ""
    help_text: str = ""
    choices: List[Dict[str, str]] = field(default_factory=list)
    validators: List[Callable[[Any], None]] = field(default_factory=list)

    def validate(self, value: Any) -> List[str]:
        errors = []

        if self.required and (value is None or value == ""):
            errors.append(f"'{self.label}' is required")
            return errors

        if value is None or value == "":
            return errors

        if self.field_type == FieldType.NUMBER:
            try:
                float(value)
            except (ValueError, TypeError):
                errors.append(f"'{self.label}' must be a number")

        for validator in self.validators:
            try:
                validator(value)
            except ValueError as e:
                errors.append(str(e))

        return errors