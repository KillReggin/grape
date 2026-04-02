from app.use_cases.process_image import ProcessImageUseCase


def run(use_case: ProcessImageUseCase, image_path: str, image_ref: str):
    result = use_case.execute(image_path=image_path, image_ref=image_ref)
    print(f"Total weight: {round(result.total_weight, 2)} g")
    return result
