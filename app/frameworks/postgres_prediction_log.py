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
                    VALUES (%s, %s, %s, %s);
                    """,
                    (image_ref, total_weight, clusters_count, artifact_uri),
                )
