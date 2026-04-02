import os
from typing import Optional


class Config:
    MODEL_PATH: str = os.getenv("MODEL_PATH", "model/weights/best.pt")

    REF_WEIGHT_GRAMS: float = float(os.getenv("REF_WEIGHT_GRAMS", "300"))
    MIN_CLUSTER_WEIGHT: float = float(os.getenv("MIN_CLUSTER_WEIGHT", "50"))
    SLICE_RATIO: float = float(os.getenv("SLICE_RATIO", "0.1"))

    S3_BUCKET: Optional[str] = os.getenv("S3_BUCKET")
    S3_ENDPOINT_URL: Optional[str] = os.getenv("S3_ENDPOINT_URL")
    S3_ACCESS_KEY_ID: Optional[str] = os.getenv("S3_ACCESS_KEY_ID")
    S3_SECRET_ACCESS_KEY: Optional[str] = os.getenv("S3_SECRET_ACCESS_KEY")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
    S3_SECURE: bool = os.getenv("S3_SECURE", "False").lower() in ("true", "1", "yes")

    INPUT_S3_KEY: Optional[str] = os.getenv("INPUT_S3_KEY")

    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")

    PDF_DPI: int = int(os.getenv("PDF_DPI", "150"))
    PLOT_ELEV: int = int(os.getenv("PLOT_ELEV", "45"))
    PLOT_AZIM: int = int(os.getenv("PLOT_AZIM", "-60"))
    FIG_SIZE_3D: tuple = tuple(map(int, os.getenv("FIG_SIZE_3D", "12,10").split(",")))
    FIG_SIZE_2D: tuple = tuple(map(int, os.getenv("FIG_SIZE_2D", "8,5").split(",")))
