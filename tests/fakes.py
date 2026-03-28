

class FakeDetector:
    def __init__(self, masks, confidences, image=None):
        self._masks = masks
        self._confidences = confidences
        self._image = image

    def predict(self, path):
        class Result:
            pass

        r = Result()
        r.masks = self._masks
        r.confidences = self._confidences
        r.image = self._image
        return r


class FakeReportGenerator:
    def __init__(self):
        self.called = False

    def generate(self, image_rgb, clusters, results_dir):
        self.called = True