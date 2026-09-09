from typing import List

from src.model.specifications.base import BaseSpecification, Field


class YandexImportSpec(BaseSpecification):
    """Yandex Music import specification.

    The playlist share link is requested in the auth form.
    """

    def get_fields(self) -> List[Field]:
        return []
