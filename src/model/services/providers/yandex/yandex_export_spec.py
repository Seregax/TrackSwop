from typing import List

from src.model.specifications.base import BaseSpecification, Field, FieldType


class YandexExportSpec(BaseSpecification):
    """Yandex Music export specification - not supported."""

    def get_fields(self) -> List[Field]:
        return [
            Field(
                name="not_supported",
                label="Export to Yandex Music is not supported",
                field_type=FieldType.TEXT,
                required=False,
                help_text="YandexMusicService supports only public playlist import.",
            ),
        ]
