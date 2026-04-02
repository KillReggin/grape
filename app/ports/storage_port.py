from abc import ABC, abstractmethod


class StoragePort(ABC):
    @abstractmethod
    def save(self, data: bytes, filename: str) -> str:
        raise NotImplementedError
