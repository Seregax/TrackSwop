from typing import Any, Dict

class ViewModel:
    def __init__(self):
        self.values: Dict[str, Any] = {}

    def set_value(self, key: str, value: Any) -> None:
        self.values[key] = value

    def get_value(self, key: str) -> Any:
        return self.values.get(key)

    def get_all(self) -> Dict[str, Any]:
        return self.values