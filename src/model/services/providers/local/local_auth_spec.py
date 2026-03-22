from typing import List
from pathlib import Path

from src.model.specifications.base import BaseSpecification, Field, FieldType


class LocalAuthSpec(BaseSpecification):
    """Local service authentication specification"""

    def get_fields(self) -> List[Field]:
        return [
            Field(
                name="directory",
                label="Директория с музыкой",
                field_type=FieldType.FOLDER,
                required=True,
                placeholder="Выберите директорию",
                help_text="Директория, в которой хранятся ваши аудиофайлы",
            ),
        ]
