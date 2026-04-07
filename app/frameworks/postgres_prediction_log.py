from typing import Optional

from app.ports.prediction_log_port import PredictionLogPort


class PostgresPredictionLog(PredictionLogPort):
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._ensure_schema()

    def _connect(self):
        import psycopg2

        return psycopg2.connect(self.database_url)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS prediction_runs (
                        id BIGSERIAL PRIMARY KEY,
                        image_ref TEXT NOT NULL,
                        total_weight DOUBLE PRECISION NOT NULL,
                        clusters_count INTEGER NOT NULL,
                        artifact_uri TEXT,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    """
                )
                # Keep table idempotent by image_ref for batch reruns:
                # deduplicate historical rows and enforce uniqueness.
                cur.execute(
                    """
                    DELETE FROM prediction_runs t
                    USING prediction_runs d
                    WHERE t.image_ref = d.image_ref
                      AND (t.created_at < d.created_at OR (t.created_at = d.created_at AND t.id < d.id));
                    """
                )
                cur.execute(
                    """
                    CREATE UNIQUE INDEX IF NOT EXISTS uq_prediction_runs_image_ref
                    ON prediction_runs (image_ref);
                    """
                )

    def save_prediction(
        self,
        image_ref: str,
        total_weight: float,
        clusters_count: int,
        artifact_uri: Optional[str],
    ) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO prediction_runs (
                        image_ref,
                        total_weight,
                        clusters_count,
                        artifact_uri
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (image_ref)
                    DO UPDATE SET
                        total_weight = EXCLUDED.total_weight,
                        clusters_count = EXCLUDED.clusters_count,
                        artifact_uri = EXCLUDED.artifact_uri,
                        created_at = NOW();
                    """,
                    (image_ref, total_weight, clusters_count, artifact_uri),
                )
