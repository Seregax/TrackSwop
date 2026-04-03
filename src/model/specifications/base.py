from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Callable


class FieldType(Enum):
    """Types for fields"""
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
    """Specification field"""
    name: str
    label: str
    field_type: FieldType
    required: bool = False
    default: Any = None
    placeholder: str = ""
    help_text: str = ""
    choices: List[Dict[str, str]] = field(default_factory=list)
    validators: List[Callable] = field(default_factory=list)

    def validate(self, value: Any) -> List[str]:
        """Validates field value"""
        errors = []

        if self.required and (value is None or value == ""):
            errors.append(f"'{self.label}' is required")
            return errors

        if value is None or value == "":
            return errors

        if self.field_type == FieldType.NUMBER:
            try:
                float(value)
            except (ValueError, TypeError) as e:
                errors.append(f"'{self.label}' must be a number")
                logger.exception(f"'{self.label}' must be a number")

        for validator in self.validators:
            try:
                validator(value)
            except ValueError as e:
                errors.append(str(e))
                logger.exception(f"Error adding value: {str(e)}") from e
                
        return errors


@dataclass
class ValidationResult:
    is_valid: bool
    errors: Dict[str, List[str]] = field(default_factory=dict)
    values: Dict[str, Any] = field(default_factory=dict)

    def add_error(self, field_: str, error: str):
        if field_ not in self.errors:
            self.errors[field_] = []
        self.errors[field_].append(error)
        self.is_valid = False


class BaseSpecification(ABC):
    """Base class for all specifications"""

    @abstractmethod
    def get_fields(self) -> List[Field]:
        pass

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        result = ValidationResult(is_valid=True, values=data.copy())

        for elem in self.get_fields():
            value = data.get(elem.name)
            errors = elem.validate(value)

            if errors:
                for error in errors:
                    result.add_error(elem.name, error)

        return result

    def get_defaults(self) -> Dict[str, Any]:
        """Returns default values"""
        return {
            elem.name: elem.default
            for elem in self.get_fields()
            if elem.default is not None
        }
