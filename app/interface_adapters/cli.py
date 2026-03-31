from app.use_cases.process_image import ProcessImageUseCase
from app.config import Config


def run(use_case: ProcessImageUseCase):
    result = use_case.execute(
        image_path=Config.INPUT_PATH
    )

    print(f"Total weight: {round(result.total_weight, 2)} g")