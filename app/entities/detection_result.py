# app/entities/detection_result.py

from dataclasses import dataclass
from typing import List, Any

@dataclass
class DetectionResult:
    masks: List[Any]
    confidences: List[float]
    image: Any