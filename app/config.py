import os


class Config:

    MODEL_PATH: str = os.getenv(
        "MODEL_PATH",
        "model/weights/best.pt"
    )

    REF_WEIGHT_GRAMS: float = float(
        os.getenv("REF_WEIGHT_GRAMS", "300")
    )

    MIN_CLUSTER_WEIGHT: float = float(
        os.getenv("MIN_CLUSTER_WEIGHT", "50")
    )

    SLICE_RATIO: float = float(
        os.getenv("SLICE_RATIO", "0.1")
    )

    PIXEL_TO_MM: float = float(
        os.getenv("PIXEL_TO_MM", "1.0")
    )

    INPUT_PATH: str = os.getenv(
        "INPUT_PATH",
        "data/input/grape5-2.jpg"
    )

    OUTPUT_PATH: str = os.getenv(
        "OUTPUT_PATH",
        "data/output/"
    )
  
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")  

    S3_BUCKET: str = os.getenv("S3_BUCKET", "my-bucket")

    PDF_DPI: int = int(os.getenv("PDF_DPI", "150"))

    PLOT_ELEV: int = int(os.getenv("PLOT_ELEV", "45"))
    PLOT_AZIM: int = int(os.getenv("PLOT_AZIM", "-60"))

    FIG_SIZE_3D: tuple = tuple(
        map(int, os.getenv("FIG_SIZE_3D", "12,10").split(","))
    )

    FIG_SIZE_2D: tuple = tuple(
        map(int, os.getenv("FIG_SIZE_2D", "8,5").split(","))
    )

    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")