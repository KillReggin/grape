import numpy as np
from app.entities.grape_cluster import GrapeCluster
from app.entities.prediction_result import PredictionResult
from app.config import Config


class ProcessImageUseCase:

    def __init__(self, detector, report_generator, ref_weight):
        self.detector = detector
        self.report_generator = report_generator
        self.ref_weight = ref_weight

    def _estimate_frustum_params(self, mask: np.ndarray):
        ys, xs = np.where(mask > 0)

        if len(ys) == 0:
            return None

        y_min, y_max = ys.min(), ys.max()
        h = y_max - y_min

        if h <= 0:
            return None

        slice_h = max(1, int(Config.SLICE_RATIO * h))

        top_slice = mask[y_min:y_min + slice_h, :]
        bottom_slice = mask[y_max - slice_h:y_max, :]

        def slice_radius(slice_mask):
            xs = np.where(slice_mask > 0)[1]
            if len(xs) == 0:
                return 0
            return (xs.max() - xs.min()) / 2

        R = slice_radius(top_slice)
        r = slice_radius(bottom_slice)

        cx = float(xs.mean())
        cy = float(ys.mean())

        return h, R, r, cx, cy

    def _compute_volume(self, h, R, r):
        return (np.pi * h / 3) * (R**2 + R*r + r**2)

    def execute(self, image_path, results_dir=None):

        detection = self.detector.predict(image_path)

        if not detection.masks:
            return PredictionResult([], 0)

        masks = detection.masks
        confidences = detection.confidences
        image = detection.image

        clusters = []
        volumes = []
        valid_data = []

        for mask in masks:
            params = self._estimate_frustum_params(mask)

            if params is None:
                continue

            h, R, r, cx, cy = params
            volume = self._compute_volume(h, R, r)

            volumes.append(volume)
            valid_data.append((h, R, r, cx, cy))

        if not volumes:
            return PredictionResult([], 0)

        ref_volume = np.median(volumes) or 1e-6

        for i, (h, R, r, cx, cy) in enumerate(valid_data):

            volume = self._compute_volume(h, R, r)

            confidence = (
                float(confidences[i])
                if i < len(confidences)
                else 1.0
            )

            scale_factor = volume / ref_volume

            weight = max(
                self.ref_weight * scale_factor * confidence,
                Config.MIN_CLUSTER_WEIGHT
            )

            cluster = GrapeCluster(
                height_px=float(h),
                R_px=float(R),
                r_px=float(r),
                volume_px3=float(volume),
                estimated_weight_g=float(weight),
                confidence=confidence,
                center_x=float(cx),
                center_y=float(cy)
            )

            clusters.append(cluster)

        total_weight = sum(c.estimated_weight_g for c in clusters)

        result = PredictionResult(clusters, float(total_weight))

        if self.report_generator:
            self.report_generator.generate(
                image_rgb=image,
                clusters=clusters,
                results_dir=results_dir
            )

        return result