from typing import List

from src.model.specifications.base import BaseSpecification, Field, FieldType


class LocalImportSpec(BaseSpecification):
    """Local service import specification"""

    def get_fields(self) -> List[Field]:
        return [
            Field(
                name="playlist_name",
                label="Имя плейлиста",
                field_type=FieldType.STRING,
                required=True,
                placeholder="Мой плейлист",
                help_text="Имя для нового плейлиста",
            ),
        ]
