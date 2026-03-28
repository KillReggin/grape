from dataclasses import dataclass
from typing import List
from .grape_cluster import GrapeCluster

@dataclass
class PredictionResult:
    clusters: List[GrapeCluster]
    total_weight: float