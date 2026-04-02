from abc import ABC, abstractmethod
from typing import Sequence, Optional

from app.entities.grape_cluster import GrapeCluster


class ReportGeneratorPort(ABC):
    @abstractmethod
    def generate(
        self,
        image_rgb,
        clusters: Sequence[GrapeCluster],
        results_dir: Optional[str] = None,
    ) -> Optional[str]:
        raise NotImplementedError
