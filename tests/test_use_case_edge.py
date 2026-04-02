import numpy as np
from app.use_cases.process_image import ProcessImageUseCase
from .fakes import FakeDetector, FakePredictionLogger


def test_zero_volume():
    detector = FakeDetector([np.zeros((10, 10))], [1.0])

    use_case = ProcessImageUseCase(detector, None, 300, 50, 0.1)

    result = use_case.execute("x")

    assert result.total_weight == 0


def test_zero_median_volume():
    detector = FakeDetector(
        [np.zeros((10, 10)), np.zeros((10, 10))],
        [1.0, 1.0]
    )

    use_case = ProcessImageUseCase(detector, None, 300, 50, 0.1)

    result = use_case.execute("x")

    assert result.total_weight == 0


def test_confidence_affects_weight():
    detector = FakeDetector([np.ones((10, 10))], [0.5])

    use_case = ProcessImageUseCase(detector, None, 300, 50, 0.1)

    result = use_case.execute("x")

    assert result.total_weight >= 50


def test_missing_confidence():
    detector = FakeDetector([np.ones((10, 10))], [])

    use_case = ProcessImageUseCase(detector, None, 300, 50, 0.1)

    result = use_case.execute("x")

    assert result.total_weight > 0


def test_cluster_has_center():
    detector = FakeDetector([np.ones((10, 10))], [1.0])

    use_case = ProcessImageUseCase(detector, None, 300, 50, 0.1)

    result = use_case.execute("x")

    cluster = result.clusters[0]

    assert cluster.center_x is not None
    assert cluster.center_y is not None


def test_logger_called_for_empty_detection():
    detector = FakeDetector([], [])
    logger = FakePredictionLogger()
    use_case = ProcessImageUseCase(
        detector=detector,
        report_generator=None,
        ref_weight=300,
        min_cluster_weight=50,
        slice_ratio=0.1,
        prediction_logger=logger,
    )

    result = use_case.execute("tmp-file", image_ref="s3://bucket/empty.jpg")

    assert result.total_weight == 0
    assert len(logger.calls) == 1
    assert logger.calls[0]["clusters_count"] == 0
    assert logger.calls[0]["artifact_uri"] is None
