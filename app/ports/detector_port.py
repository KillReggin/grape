from abc import ABC, abstractmethod

from app.entities.detection_result import DetectionResult


class DetectorPort(ABC):
    @abstractmethod
    def predict(self, image_path: str) -> DetectionResult:
        raise NotImplementedError
