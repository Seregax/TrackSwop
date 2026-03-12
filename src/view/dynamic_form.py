from service_field import FieldType, ServiceField
from view_model import ViewModel


class DynamicForm:

    def __init__(self, fields: list[ServiceField], view_model: ViewModel):
        self.fields = fields
        self.view_model = view_model

    def render(self) -> None:

        for field in self.fields:

            if field.field_type == FieldType.STRING:
                value = input(f"{field.label}: ")

            elif field.field_type == FieldType.NUMBER:
                value = float(input(f"{field.label}: "))

            elif field.field_type == FieldType.BOOLEAN:
                value = input(f"{field.label} (y/n): ").lower() == "y"

            else:
                raise ValueError("Unknown field type")

            self.view_model.set_value(field.name, value)