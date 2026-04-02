
from app.entities.detection_result import DetectionResult
from app.ports.detector_port import DetectorPort
from app.ports.report_port import ReportGeneratorPort


class FakeDetector(DetectorPort):
    def __init__(self, masks, confidences, image=None):
        self._masks = masks
        self._confidences = confidences
        self._image = image

    def predict(self, path):
        return DetectionResult(
            masks=self._masks,
            confidences=self._confidences,
            image=self._image,
        )


class FakeReportGenerator(ReportGeneratorPort):
    def __init__(self):
        self.called = False
        self.return_uri = None

    def generate(self, image_rgb, clusters, results_dir=None):
        self.called = True
        return self.return_uri


class FakePredictionLogger:
    def __init__(self):
        self.calls = []

    def save_prediction(self, image_ref, total_weight, clusters_count, artifact_uri):
        self.calls.append(
            {
                "image_ref": image_ref,
                "total_weight": total_weight,
                "clusters_count": clusters_count,
                "artifact_uri": artifact_uri,
            }
        )
