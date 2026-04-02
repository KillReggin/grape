import numpy as np
from app.use_cases.process_image import ProcessImageUseCase
from .fakes import FakeDetector, FakePredictionLogger, FakeReportGenerator


def test_empty_masks():
    detector = FakeDetector([], [])

    use_case = ProcessImageUseCase(detector, None, 300, 50, 0.1)

    result = use_case.execute("x")

    assert result.total_weight == 0
    assert result.clusters == []


def test_single_mask():
    detector = FakeDetector([np.ones((10, 10))], [1.0])

    use_case = ProcessImageUseCase(detector, None, 300, 50, 0.1)

    result = use_case.execute("x")

    assert len(result.clusters) == 1
    assert result.total_weight > 0


def test_multiple_clusters():
    detector = FakeDetector(
        [np.ones((10, 10)), np.ones((8, 8))],
        [1.0, 0.8]
    )

    use_case = ProcessImageUseCase(detector, None, 300, 50, 0.1)

    result = use_case.execute("x")

    assert len(result.clusters) == 2
    assert result.total_weight > 0


def test_report_called():
    detector = FakeDetector([np.ones((10, 10))], [1.0], image="img")
    report = FakeReportGenerator()

    use_case = ProcessImageUseCase(detector, report, 300, 50, 0.1)

    use_case.execute("x", results_dir="out")

    assert report.called is True


def test_prediction_logger_called_with_artifact_uri():
    detector = FakeDetector([np.ones((10, 10))], [1.0], image="img")
    report = FakeReportGenerator()
    report.return_uri = "s3://bucket/report.pdf"
    logger = FakePredictionLogger()

    use_case = ProcessImageUseCase(
        detector=detector,
        report_generator=report,
        ref_weight=300,
        min_cluster_weight=50,
        slice_ratio=0.1,
        prediction_logger=logger,
    )

    result = use_case.execute("tmp-file", image_ref="s3://bucket/input.jpg")

    assert result.total_weight > 0
    assert len(logger.calls) == 1
    assert logger.calls[0]["image_ref"] == "s3://bucket/input.jpg"
    assert logger.calls[0]["artifact_uri"] == "s3://bucket/report.pdf"
