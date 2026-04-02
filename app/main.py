from app.config import Config
from app.frameworks.postgres_prediction_log import PostgresPredictionLog
from app.frameworks.report_generate import ReportGenerator
from app.frameworks.s3_image_source import S3ImageSource
from app.frameworks.s3_storage import S3Storage
from app.frameworks.yolo_model import YOLODetector
from app.interface_adapters.cli import run
from app.use_cases.process_image import ProcessImageUseCase


def _require(value: str, name: str) -> str:
    if not value:
        raise ValueError(f"Environment variable {name} is required")
    return value


def main():
    s3_bucket = _require(Config.S3_BUCKET, "S3_BUCKET")
    s3_endpoint = _require(Config.S3_ENDPOINT_URL, "S3_ENDPOINT_URL")
    s3_key_id = _require(Config.S3_ACCESS_KEY_ID, "S3_ACCESS_KEY_ID")
    s3_secret = _require(Config.S3_SECRET_ACCESS_KEY, "S3_SECRET_ACCESS_KEY")
    input_s3_key = _require(Config.INPUT_S3_KEY, "INPUT_S3_KEY")
    database_url = _require(Config.DATABASE_URL, "DATABASE_URL")

    storage = S3Storage(
        bucket=s3_bucket,
        endpoint_url=s3_endpoint,
        access_key_id=s3_key_id,
        secret_access_key=s3_secret,
        region=Config.S3_REGION,
        secure=Config.S3_SECURE,
    )

    image_source = S3ImageSource(
        bucket=s3_bucket,
        endpoint_url=s3_endpoint,
        access_key_id=s3_key_id,
        secret_access_key=s3_secret,
        region=Config.S3_REGION,
        secure=Config.S3_SECURE,
    )

    prediction_logger = PostgresPredictionLog(database_url=database_url)

    detector = YOLODetector(Config.MODEL_PATH)
    report_generator = ReportGenerator(
        storage=storage,
        pdf_dpi=Config.PDF_DPI,
        plot_elev=Config.PLOT_ELEV,
        plot_azim=Config.PLOT_AZIM,
        fig_size_3d=Config.FIG_SIZE_3D,
        fig_size_2d=Config.FIG_SIZE_2D,
    )

    use_case = ProcessImageUseCase(
        detector=detector,
        report_generator=report_generator,
        ref_weight=Config.REF_WEIGHT_GRAMS,
        min_cluster_weight=Config.MIN_CLUSTER_WEIGHT,
        slice_ratio=Config.SLICE_RATIO,
        prediction_logger=prediction_logger,
    )

    image_path = image_source.fetch_to_temp(input_s3_key)
    try:
        run(use_case, image_path=image_path, image_ref=f"s3://{s3_bucket}/{input_s3_key}")
    finally:
        image_source.cleanup(image_path)


if __name__ == "__main__":
    main()
