import numpy as np
from app.use_cases.process_image import ProcessImageUseCase
from .fakes import FakeDetector


def test_zero_volume():
    detector = FakeDetector([np.zeros((10, 10))], [1.0])

    use_case = ProcessImageUseCase(detector, None, 300)

    result = use_case.execute("x")

    assert result.total_weight == 0


def test_zero_median_volume():
    detector = FakeDetector(
        [np.zeros((10, 10)), np.zeros((10, 10))],
        [1.0, 1.0]
    )

    use_case = ProcessImageUseCase(detector, None, 300)

    result = use_case.execute("x")

    assert result.total_weight == 0


def test_confidence_affects_weight():
    detector = FakeDetector([np.ones((10, 10))], [0.5])

    use_case = ProcessImageUseCase(detector, None, 300)

    result = use_case.execute("x")

    assert result.total_weight >= 50


def test_missing_confidence():
    detector = FakeDetector([np.ones((10, 10))], [])

    use_case = ProcessImageUseCase(detector, None, 300)

    result = use_case.execute("x")

    assert result.total_weight > 0


def test_cluster_has_center():
    detector = FakeDetector([np.ones((10, 10))], [1.0])

    use_case = ProcessImageUseCase(detector, None, 300)

    result = use_case.execute("x")

    cluster = result.clusters[0]

    assert cluster.center_x is not None
    assert cluster.center_y is not None