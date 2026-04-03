import json
import os
from pathlib import Path
from typing import Optional, Union

from cryptography.fernet import Fernet

from src.common.logger import get_logger

logger = get_logger(__name__)

class TokenStore:
    def __init__(self, path: Union[str, Path] = "tokens.json", master_key: Optional[bytes] = None):
        self.path = Path(path)
        # master_key можно передавать извне или брать из env
        if master_key is None:
            # В реальном проекте лучше читать из переменной окружения
            key = os.environ.get("TRACKSWOP_MASTER_KEY")
            if not key:
                # Генерируем временный ключ для разработки
                key = Fernet.generate_key().decode()
                logger.info("WARNING: generated temp key, set TRACKSWOP_MASTER_KEY for real usage")
            master_key = key.encode()

        # Приводим к формату, который хочет Fernet: 32 байта base64
        self.cipher = Fernet(master_key)

        # Если файла нет — создаём пустой
        if not self.path.exists():
            self._write_data({})

    def _read_data(self) -> dict:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _write_data(self, data: dict) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def save_token(self, service: str, token: str) -> None:
        data = self._read_data()
        encrypted = self.cipher.encrypt(token.encode()).decode()
        data[service] = encrypted
        self._write_data(data)

    def get_token(self, service: str) -> Optional[str]:
        data = self._read_data()
        encrypted = data.get(service)
        if encrypted is None:
            return None
        try:
            decrypted = self.cipher.decrypt(encrypted.encode()).decode()
            return decrypted
        except Exception:
            logger.exception("Failed to get a token")
            return None

    def delete_token(self, service: str) -> None:
        data = self._read_data()
        if service in data:
            del data[service]
            self._write_data(data)
