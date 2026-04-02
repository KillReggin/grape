from abc import ABC, abstractmethod


class ImageSourcePort(ABC):
    @abstractmethod
    def fetch_to_temp(self, object_key: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def cleanup(self, temp_path: str) -> None:
        raise NotImplementedError
