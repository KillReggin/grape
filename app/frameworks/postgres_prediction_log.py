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
                # Serialize schema initialization across concurrent workers.
                cur.execute("SELECT pg_advisory_lock(hashtext('prediction_runs_schema_v1'));")
                try:
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

                    # Remove historical duplicates before creating unique index.
                    cur.execute(
                        """
                        WITH ranked AS (
                            SELECT
                                id,
                                ROW_NUMBER() OVER (
                                    PARTITION BY image_ref
                                    ORDER BY created_at DESC, id DESC
                                ) AS rn
                            FROM prediction_runs
                        )
                        DELETE FROM prediction_runs p
                        USING ranked r
                        WHERE p.id = r.id AND r.rn > 1;
                        """
                    )

                    cur.execute(
                        """
                        CREATE UNIQUE INDEX IF NOT EXISTS uq_prediction_runs_image_ref
                        ON prediction_runs (image_ref);
                        """
                    )
                finally:
                    cur.execute("SELECT pg_advisory_unlock(hashtext('prediction_runs_schema_v1'));")

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
