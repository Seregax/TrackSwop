from typing import List
from src.model.specifications.base import BaseSpecification, Field, FieldType


class VkAuthSpecification(BaseSpecification):
    """Спецификация для авторизации в ВКонтакте"""

    def get_fields(self) -> List[Field]:
        return [
            Field(
                name="token",
                label="Access Token",
                field_type=FieldType.PASSWORD,
                required=True,
                placeholder="vk1.a.AbCdEfGhIjKlMnOpQrStUvWxYz...",
                help_text="Получите токен."
            ),
            Field(
                name="user_id",
                label="User ID",
                field_type=FieldType.NUMBER,
                required=True,
                placeholder="123456789",
                help_text="Ваш VK user_id (можно узнать через метод users.get)"
            )
        ]