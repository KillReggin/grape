import os
from app.ports.storage_port import StoragePort


class LocalStorage(StoragePort):

    def __init__(self, base_path: str):
        self.base_path = base_path

    def save(self, data: bytes, filename: str) -> str:

        os.makedirs(self.base_path, exist_ok=True)

        path = os.path.join(self.base_path, filename)

        with open(path, "wb") as f:
            f.write(data)

        return path