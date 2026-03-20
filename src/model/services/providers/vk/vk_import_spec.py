from typing import List
from src.model.specifications.base import BaseSpecification, Field, FieldType


class VkImportSpecification(BaseSpecification):
    """Спецификация для импорта плейлиста из ВКонтакте"""

    def get_fields(self) -> List[Field]:
        return [
            Field(
                name="playlist_id",
                label="ID плейлиста",
                field_type=FieldType.STRING,
                required=True,
                placeholder="12345",
                help_text="Цифровой ID плейлиста ВКонтакте"
            ),
            Field(
                name="owner_id",
                label="Owner ID",
                field_type=FieldType.NUMBER,
                required=False,
                placeholder="123456789",
                help_text="ID владельца плейлиста (по умолчанию = авторизованный пользователь)"
            )
        ]