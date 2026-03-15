import json
from pathlib import Path

from src.model.store.token_store import TokenStore


def test_save_and_load_token(tmp_path: Path):
    store_path = tmp_path / "tokens.json"
    store = TokenStore(path=store_path)

    store.save_token("spotify", "ABC123")

     # При чтении через TokenStore получаем исходный токен
    assert store.get_token("spotify") == "ABC123"

    # В файле лежит шифрованная строка, не равная исходному токену
    data = json.loads(store_path.read_text(encoding="utf-8"))
    assert data["spotify"] != "ABC123"
    assert isinstance(data["spotify"], str)


def test_load_returns_none_if_not_exists(tmp_path: Path):
    store = TokenStore(path=tmp_path / "tokens.json")

    assert store.get_token("not_exists") is None


def test_delete_token(tmp_path: Path):
    store_path = tmp_path / "tokens.json"
    store = TokenStore(path=store_path)

    store.save_token("spotify", "ABC123")
    store.delete_token("spotify")

    assert store.get_token("spotify") is None
