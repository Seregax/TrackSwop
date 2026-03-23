from typing import List

from src.model.specifications.base import BaseSpecification, Field, FieldType


class LocalExportSpec(BaseSpecification):
    """Local service export specification - not supported"""

    def get_fields(self) -> List[Field]:
        return [
            Field(
                name="not_supported",
                label="Экспорт в локальную директорию не поддерживается",
                field_type=FieldType.TEXT,
                required=False,
                help_text="LocalService поддерживает только импорт из локальных файлов",
            ),
        ]
