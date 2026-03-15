from typing import List, Any
from src.model.specifications.base import Field, FieldType
from view_model import ViewModel


class DynamicForm:

    def __init__(self, fields: List[Field], view_model: ViewModel):
        self.fields = fields
        self.view_model = view_model

    def render(self) -> None:
        for field in self.fields:
            value: Any = None

            if field.field_type in [FieldType.STRING, FieldType.TEXT, FieldType.PASSWORD]:
                value = input(f"{field.label}: ") or field.default

            elif field.field_type == FieldType.NUMBER:
                raw = input(f"{field.label}: ") or field.default
                try:
                    value = float(raw) if raw is not None else None
                except ValueError:
                    print(f"'{field.label}' must be a number")
                    continue

            elif field.field_type == FieldType.BOOLEAN:
                raw = input(f"{field.label} (y/n): ").lower() or ""
                value = raw == "y"

            elif field.field_type == FieldType.CHOICE:
                print(f"{field.label}:")
                for idx, choice in enumerate(field.choices):
                    print(f"{idx + 1}. {choice['label']}")
                selected = input("Select option number: ")
                try:
                    index = int(selected) - 1
                    value = field.choices[index]["value"]
                except (ValueError, IndexError):
                    print("Invalid selection")
                    continue

            elif field.field_type == FieldType.MULTI_CHOICE:
                print(f"{field.label} (comma separated numbers):")
                for idx, choice in enumerate(field.choices):
                    print(f"{idx + 1}. {choice['label']}")
                selected = input("Select options: ")
                try:
                    indices = [int(x.strip()) - 1 for x in selected.split(",")]
                    value = [field.choices[i]["value"] for i in indices]
                except (ValueError, IndexError):
                    print("Invalid selection")
                    continue

            errors = field.validate(value)
            if errors:
                for e in errors:
                    print(f"Error: {e}")
                continue

            self.view_model.set_value(field.name, value)