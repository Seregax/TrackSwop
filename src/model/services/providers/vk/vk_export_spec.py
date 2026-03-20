from typing import List
from src.model.specifications.base import BaseSpecification, Field, FieldType


class VkExportSpecification(BaseSpecification):
    """Спецификация для экспорта плейлиста во ВКонтакте"""

    def get_fields(self) -> List[Field]:
        return [
            Field(
                name="destination_playlist_id",
                label="ID плейлиста назначения",
                field_type=FieldType.STRING,
                required=True,
                placeholder="67890",
                help_text="ID плейлиста ВКонтакте, куда добавить треки"
            ),
            Field(
                name="create_if_not_exists",
                label="Создать если не существует",
                field_type=FieldType.BOOLEAN,
                required=False,
                default=True,
                help_text="Если True — создать новый плейлист при отсутствии указанного"
            ),
            Field(
                name="playlist_title",
                label="Название плейлиста",
                field_type=FieldType.STRING,
                required=False,
                placeholder="Мой плейлист",
                help_text="Название для нового плейлиста (если создаётся)"
            )
        ]