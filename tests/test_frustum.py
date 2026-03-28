from app.use_cases.process_image import ProcessImageUseCase
import numpy as np


def test_frustum_params_basic():
    use_case = ProcessImageUseCase(None, None, 300)

    mask = np.zeros((10, 10))
    mask[2:8, 3:7] = 1

    result = use_case._estimate_frustum_params(mask)

    assert result is not None

    h, R, r, cx, cy = result

    assert h > 0
    assert R >= 0
    assert r >= 0
    assert 0 <= cx <= 10
    assert 0 <= cy <= 10


def test_compute_volume():
    use_case = ProcessImageUseCase(None, None, 300)

    volume = use_case._compute_volume(10, 5, 3)

    assert volume > 0


def test_empty_mask():
    use_case = ProcessImageUseCase(None, None, 300)

    mask = np.zeros((10, 10))

    result = use_case._estimate_frustum_params(mask)

    assert result is None


def test_frustum_invalid_height():
    use_case = ProcessImageUseCase(None, None, 300)

    mask = np.zeros((10, 10))
    mask[5, 5] = 1  

    result = use_case._estimate_frustum_params(mask)

    assert result is None