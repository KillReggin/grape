import numpy as np
from app.use_cases.process_image import ProcessImageUseCase
from .fakes import FakeDetector, FakeReportGenerator


def test_empty_masks():
    detector = FakeDetector([], [])

    use_case = ProcessImageUseCase(detector, None, 300)

    result = use_case.execute("x")

    assert result.total_weight == 0
    assert result.clusters == []


def test_single_mask():
    detector = FakeDetector([np.ones((10, 10))], [1.0])

    use_case = ProcessImageUseCase(detector, None, 300)

    result = use_case.execute("x")

    assert len(result.clusters) == 1
    assert result.total_weight > 0


def test_multiple_clusters():
    detector = FakeDetector(
        [np.ones((10, 10)), np.ones((8, 8))],
        [1.0, 0.8]
    )

    use_case = ProcessImageUseCase(detector, None, 300)

    result = use_case.execute("x")

    assert len(result.clusters) == 2
    assert result.total_weight > 0


def test_report_called():
    detector = FakeDetector([np.ones((10, 10))], [1.0], image="img")
    report = FakeReportGenerator()

    use_case = ProcessImageUseCase(detector, report, 300)

    use_case.execute("x", results_dir="out")

    assert report.called is True