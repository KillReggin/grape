from typing import Optional

import numpy as np

from app.entities.grape_cluster import GrapeCluster
from app.entities.prediction_result import PredictionResult
from app.ports.detector_port import DetectorPort
from app.ports.prediction_log_port import PredictionLogPort
from app.ports.report_port import ReportGeneratorPort


class ProcessImageUseCase:
    def __init__(
        self,
        detector: DetectorPort,
        report_generator: Optional[ReportGeneratorPort],
        ref_weight: float,
        min_cluster_weight: float,
        slice_ratio: float,
        prediction_logger: Optional[PredictionLogPort] = None,
    ):
        self.detector = detector
        self.report_generator = report_generator
        self.ref_weight = ref_weight
        self.min_cluster_weight = min_cluster_weight
        self.slice_ratio = slice_ratio
        self.prediction_logger = prediction_logger

    def _estimate_frustum_params(self, mask: np.ndarray):
        ys, xs = np.where(mask > 0)

        if len(ys) == 0:
            return None

        y_min, y_max = ys.min(), ys.max()
        h = y_max - y_min

        if h <= 0:
            return None

        slice_h = max(1, int(self.slice_ratio * h))

        top_slice = mask[y_min : y_min + slice_h, :]
        bottom_slice = mask[y_max - slice_h : y_max, :]

        def slice_radius(slice_mask):
            xs_slice = np.where(slice_mask > 0)[1]
            if len(xs_slice) == 0:
                return 0
            return (xs_slice.max() - xs_slice.min()) / 2

        upper_radius = slice_radius(top_slice)
        lower_radius = slice_radius(bottom_slice)

        cx = float(xs.mean())
        cy = float(ys.mean())

        return h, upper_radius, lower_radius, cx, cy

    def _compute_volume(self, h, upper_radius, lower_radius):
        return (np.pi * h / 3) * (
            upper_radius**2 + upper_radius * lower_radius + lower_radius**2
        )

    def _save_log(
        self,
        image_ref: str,
        total_weight: float,
        clusters_count: int,
        artifact_uri: Optional[str],
    ) -> None:
        if not self.prediction_logger:
            return

        self.prediction_logger.save_prediction(
            image_ref=image_ref,
            total_weight=total_weight,
            clusters_count=clusters_count,
            artifact_uri=artifact_uri,
        )

    def execute(self, image_path, results_dir=None, image_ref: Optional[str] = None):
        detection = self.detector.predict(image_path)
        prediction_image_ref = image_ref or image_path

        if not detection.masks:
            result = PredictionResult([], 0)
            self._save_log(
                image_ref=prediction_image_ref,
                total_weight=0,
                clusters_count=0,
                artifact_uri=None,
            )
            return result

        clusters = []
        volumes = []
        valid_data = []

        for mask in detection.masks:
            params = self._estimate_frustum_params(mask)

            if params is None:
                continue

            h, upper_radius, lower_radius, cx, cy = params
            volume = self._compute_volume(h, upper_radius, lower_radius)

            volumes.append(volume)
            valid_data.append((h, upper_radius, lower_radius, cx, cy))

        if not volumes:
            result = PredictionResult([], 0)
            self._save_log(
                image_ref=prediction_image_ref,
                total_weight=0,
                clusters_count=0,
                artifact_uri=None,
            )
            return result

        ref_volume = np.median(volumes) or 1e-6

        for i, (h, upper_radius, lower_radius, cx, cy) in enumerate(valid_data):
            volume = self._compute_volume(h, upper_radius, lower_radius)

            confidence = (
                float(detection.confidences[i]) if i < len(detection.confidences) else 1.0
            )

            scale_factor = volume / ref_volume
            weight = max(
                self.ref_weight * scale_factor * confidence,
                self.min_cluster_weight,
            )

            cluster = GrapeCluster(
                height_px=float(h),
                R_px=float(upper_radius),
                r_px=float(lower_radius),
                volume_px3=float(volume),
                estimated_weight_g=float(weight),
                confidence=confidence,
                center_x=float(cx),
                center_y=float(cy),
            )

            clusters.append(cluster)

        total_weight = sum(c.estimated_weight_g for c in clusters)
        result = PredictionResult(clusters, float(total_weight))

        artifact_uri = None
        if self.report_generator:
            artifact_uri = self.report_generator.generate(
                image_rgb=detection.image,
                clusters=clusters,
                results_dir=results_dir,
            )

        self._save_log(
            image_ref=prediction_image_ref,
            total_weight=float(total_weight),
            clusters_count=len(clusters),
            artifact_uri=artifact_uri,
        )

        return result
