from ultralytics import YOLO
import numpy as np
from app.entities.detection_result import DetectionResult
from app.ports.detector_port import DetectorPort


class YOLODetector(DetectorPort):

    def __init__(self, model_path):
        self.model = YOLO(model_path)

    def predict(self, image_path) -> DetectionResult:

        results = self.model(image_path)
        result = results[0]

        image = result.orig_img

        if result.masks is None or result.masks.data is None:
            return DetectionResult([], [], image)

        masks = [
            m.cpu().numpy().astype(np.uint8)
            for m in result.masks.data
        ]

        confidences = (
            result.boxes.conf.cpu().numpy().tolist()
            if result.boxes is not None
            else [1.0] * len(masks)
        )

        return DetectionResult(masks, confidences, image)