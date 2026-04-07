import os
from typing import List

import boto3

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


def _build_s3_client(endpoint_url: str, access_key_id: str, secret_access_key: str, region: str):
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region,
    )


def _list_input_keys(client, bucket: str, prefix: str) -> List[str]:
    keys: List[str] = []
    continuation_token = None

    while True:
        params = {"Bucket": bucket, "Prefix": prefix}
        if continuation_token:
            params["ContinuationToken"] = continuation_token

        response = client.list_objects_v2(**params)

        for obj in response.get("Contents", []):
            key = obj["Key"]
            if key.endswith("/"):
                continue
            keys.append(key)

        if not response.get("IsTruncated"):
            break

        continuation_token = response.get("NextContinuationToken")

    return sorted(keys)


def main() -> None:
    s3_bucket = _require(Config.S3_BUCKET, "S3_BUCKET")
    s3_endpoint = _require(Config.S3_ENDPOINT_URL, "S3_ENDPOINT_URL")
    s3_key_id = _require(Config.S3_ACCESS_KEY_ID, "S3_ACCESS_KEY_ID")
    s3_secret = _require(Config.S3_SECRET_ACCESS_KEY, "S3_SECRET_ACCESS_KEY")
    database_url = _require(Config.DATABASE_URL, "DATABASE_URL")

    input_prefix = _require(os.getenv("INPUT_S3_PREFIX"), "INPUT_S3_PREFIX")
    batch_date = _require(os.getenv("BATCH_DATE"), "BATCH_DATE")
    report_prefix = os.getenv("REPORT_S3_PREFIX", "reports").strip("/")

    date_partition_prefix = f"{input_prefix.rstrip('/')}/dt={batch_date}/"

    s3_client = _build_s3_client(
        endpoint_url=s3_endpoint,
        access_key_id=s3_key_id,
        secret_access_key=s3_secret,
        region=Config.S3_REGION,
    )

    image_keys = _list_input_keys(s3_client, s3_bucket, date_partition_prefix)

    if not image_keys:
        print(f"No images found for prefix: {date_partition_prefix}")
        return

    storage = S3Storage(
        bucket=s3_bucket,
        endpoint_url=s3_endpoint,
        access_key_id=s3_key_id,
        secret_access_key=s3_secret,
        region=Config.S3_REGION,
        secure=Config.S3_SECURE,
        key_prefix=f"{report_prefix}/dt={batch_date}",
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

    print(f"Batch date: {batch_date}")
    print(f"Found {len(image_keys)} image(s)")

    for key in image_keys:
        image_path = image_source.fetch_to_temp(key)
        try:
            run(use_case, image_path=image_path, image_ref=f"s3://{s3_bucket}/{key}")
        finally:
            image_source.cleanup(image_path)


if __name__ == "__main__":
    main()
