class ViewModel:

    def __init__(self):
        self.values: dict[str, object] = {}

    def set_value(self, key: str, value: object) -> None:
        self.values[key] = value

    def get_value(self, key: str):
        return self.values.get(key)

    def get_all(self) -> dict:
        return self.values