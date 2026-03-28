from app.use_cases.process_image import ProcessImageUseCase
from app.frameworks.yolo_model import YOLODetector
from app.frameworks.report_generate import ReportGenerator
from app.frameworks.local_storage import LocalStorage
from app.frameworks.s3_storage import S3Storage
from app.config import Config


def main():

    if Config.STORAGE_TYPE == "s3":
        storage = S3Storage(Config.S3_BUCKET)
    else:
        storage = LocalStorage(Config.OUTPUT_PATH)

    detector = YOLODetector(Config.MODEL_PATH)
    report_generator = ReportGenerator(storage)

    use_case = ProcessImageUseCase(
        detector=detector,
        report_generator=report_generator,
        ref_weight=Config.REF_WEIGHT_GRAMS
    )

    result = use_case.execute(
        image_path=Config.INPUT_PATH
    )

    print(f"Total weight: {round(result.total_weight, 2)} g")


if __name__ == "__main__":
    main()