from dataclasses import dataclass

@dataclass
class GrapeCluster:
    height_px: float
    R_px: float
    r_px: float
    volume_px3: float
    estimated_weight_g: float
    confidence: float
    center_x: float   
    center_y: float  