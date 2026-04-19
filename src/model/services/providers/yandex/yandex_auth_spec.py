from typing import List

from src.model.specifications.base import BaseSpecification, Field, FieldType


class YandexAuthSpec(BaseSpecification):
    """Yandex Music public playlist link specification."""

    def get_fields(self) -> List[Field]:
        return [
            Field(
                name="playlist_url",
                label="Yandex Music playlist link",
                field_type=FieldType.STRING,
                required=True,
                placeholder="https://music.yandex.ru/users/<user>/playlists/<id>",
                help_text="Paste a public Yandex Music playlist share link.",
            ),
        ]
