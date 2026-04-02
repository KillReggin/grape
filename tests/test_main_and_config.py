import importlib


def test_config_reads_environment(monkeypatch):
    monkeypatch.setenv("S3_BUCKET", "bucket-1")
    monkeypatch.setenv("S3_ENDPOINT_URL", "http://minio:9000")
    monkeypatch.setenv("S3_ACCESS_KEY_ID", "ak")
    monkeypatch.setenv("S3_SECRET_ACCESS_KEY", "sk")
    monkeypatch.setenv("INPUT_S3_KEY", "input/grape.jpg")
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@host:5432/db")

    import app.config as config_module

    importlib.reload(config_module)

    assert config_module.Config.S3_BUCKET == "bucket-1"
    assert config_module.Config.INPUT_S3_KEY == "input/grape.jpg"
    assert config_module.Config.DATABASE_URL == "postgresql://u:p@host:5432/db"


def test_main_wires_and_runs(monkeypatch):
    import app.main as main_module

    calls = {}

    class FakeStorage:
        def __init__(self, **kwargs):
            calls["storage_kwargs"] = kwargs

    class FakeImageSource:
        def __init__(self, **kwargs):
            calls["image_source_kwargs"] = kwargs

        def fetch_to_temp(self, object_key):
            calls["fetched_key"] = object_key
            return "/tmp/input.jpg"

        def cleanup(self, temp_path):
            calls["cleanup_path"] = temp_path

    class FakePredictionLog:
        def __init__(self, database_url):
            calls["database_url"] = database_url

    class FakeDetector:
        def __init__(self, model_path):
            calls["model_path"] = model_path

    class FakeReportGenerator:
        def __init__(self, **kwargs):
            calls["report_kwargs"] = kwargs

    class FakeUseCase:
        def __init__(self, **kwargs):
            calls["use_case_kwargs"] = kwargs

    def fake_run(use_case, image_path, image_ref):
        calls["run_args"] = {
            "use_case": use_case,
            "image_path": image_path,
            "image_ref": image_ref,
        }

    monkeypatch.setattr(main_module, "S3Storage", FakeStorage)
    monkeypatch.setattr(main_module, "S3ImageSource", FakeImageSource)
    monkeypatch.setattr(main_module, "PostgresPredictionLog", FakePredictionLog)
    monkeypatch.setattr(main_module, "YOLODetector", FakeDetector)
    monkeypatch.setattr(main_module, "ReportGenerator", FakeReportGenerator)
    monkeypatch.setattr(main_module, "ProcessImageUseCase", FakeUseCase)
    monkeypatch.setattr(main_module, "run", fake_run)

    monkeypatch.setattr(main_module.Config, "S3_BUCKET", "bucket")
    monkeypatch.setattr(main_module.Config, "S3_ENDPOINT_URL", "http://minio:9000")
    monkeypatch.setattr(main_module.Config, "S3_ACCESS_KEY_ID", "key")
    monkeypatch.setattr(main_module.Config, "S3_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setattr(main_module.Config, "INPUT_S3_KEY", "input/a.jpg")
    monkeypatch.setattr(main_module.Config, "DATABASE_URL", "postgresql://db")
    monkeypatch.setattr(main_module.Config, "S3_REGION", "us-east-1")
    monkeypatch.setattr(main_module.Config, "S3_SECURE", False)
    monkeypatch.setattr(main_module.Config, "MODEL_PATH", "model/weights/best.pt")
    monkeypatch.setattr(main_module.Config, "PDF_DPI", 150)
    monkeypatch.setattr(main_module.Config, "PLOT_ELEV", 45)
    monkeypatch.setattr(main_module.Config, "PLOT_AZIM", -60)
    monkeypatch.setattr(main_module.Config, "FIG_SIZE_3D", (12, 10))
    monkeypatch.setattr(main_module.Config, "FIG_SIZE_2D", (8, 5))
    monkeypatch.setattr(main_module.Config, "REF_WEIGHT_GRAMS", 300.0)
    monkeypatch.setattr(main_module.Config, "MIN_CLUSTER_WEIGHT", 50.0)
    monkeypatch.setattr(main_module.Config, "SLICE_RATIO", 0.1)

    main_module.main()

    assert calls["fetched_key"] == "input/a.jpg"
    assert calls["cleanup_path"] == "/tmp/input.jpg"
    assert calls["database_url"] == "postgresql://db"
    assert calls["run_args"]["image_ref"] == "s3://bucket/input/a.jpg"
    assert calls["run_args"]["image_path"] == "/tmp/input.jpg"


def test_require_raises_for_missing_value():
    import app.main as main_module

    try:
        main_module._require("", "S3_BUCKET")
    except ValueError as exc:
        assert "S3_BUCKET" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
