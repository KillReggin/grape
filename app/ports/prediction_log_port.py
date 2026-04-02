from abc import ABC, abstractmethod
from typing import Optional


class PredictionLogPort(ABC):
    @abstractmethod
    def save_prediction(
        self,
        image_ref: str,
        total_weight: float,
        clusters_count: int,
        artifact_uri: Optional[str],
    ) -> None:
        raise NotImplementedError
