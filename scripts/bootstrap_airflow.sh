set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ -f ".env" ]]; then
  set -a
  source ".env"
  set +a
fi

required_vars=(
  S3_BUCKET
  S3_ACCESS_KEY_ID
  S3_SECRET_ACCESS_KEY
  S3_REGION
  POSTGRES_PASSWORD
)

for var_name in "${required_vars[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    echo "Missing required env var: $var_name" >&2
    exit 1
  fi
done

AIRFLOW_CONTAINER="${AIRFLOW_CONTAINER:-airflow_webserver}"
GRAPE_BATCH_IMAGE="${GRAPE_BATCH_IMAGE:-grape-yield:1.0.0}"
S3_ENDPOINT_AIRFLOW="${S3_ENDPOINT_AIRFLOW:-http://host.docker.internal:9000}"
POSTGRES_HOST_AIRFLOW="${POSTGRES_HOST_AIRFLOW:-host.docker.internal}"
POSTGRES_PORT_AIRFLOW="${POSTGRES_PORT_AIRFLOW:-5432}"
POSTGRES_DB_AIRFLOW="${POSTGRES_DB_AIRFLOW:-grape_db}"
POSTGRES_USER_AIRFLOW="${POSTGRES_USER_AIRFLOW:-grape_user}"

echo "Waiting for Airflow container '$AIRFLOW_CONTAINER'..."
for _ in {1..60}; do
  if docker exec "$AIRFLOW_CONTAINER" airflow version >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! docker exec "$AIRFLOW_CONTAINER" airflow version >/dev/null 2>&1; then
  echo "Airflow container is not ready: $AIRFLOW_CONTAINER" >&2
  exit 1
fi

echo "Configuring Airflow Connections..."
docker exec "$AIRFLOW_CONTAINER" airflow connections delete grape_s3 >/dev/null 2>&1 || true
docker exec "$AIRFLOW_CONTAINER" airflow connections add grape_s3 \
  --conn-type aws \
  --conn-login "$S3_ACCESS_KEY_ID" \
  --conn-password "$S3_SECRET_ACCESS_KEY" \
  --conn-extra "{\"endpoint_url\":\"$S3_ENDPOINT_AIRFLOW\",\"region_name\":\"$S3_REGION\",\"secure\":false}" >/dev/null

docker exec "$AIRFLOW_CONTAINER" airflow connections delete grape_postgres >/dev/null 2>&1 || true
docker exec "$AIRFLOW_CONTAINER" airflow connections add grape_postgres \
  --conn-type postgres \
  --conn-host "$POSTGRES_HOST_AIRFLOW" \
  --conn-port "$POSTGRES_PORT_AIRFLOW" \
  --conn-schema "$POSTGRES_DB_AIRFLOW" \
  --conn-login "$POSTGRES_USER_AIRFLOW" \
  --conn-password "$POSTGRES_PASSWORD" >/dev/null

echo "Configuring Airflow Variables..."
docker exec "$AIRFLOW_CONTAINER" airflow variables set grape_s3_bucket "$S3_BUCKET" >/dev/null
docker exec "$AIRFLOW_CONTAINER" airflow variables set grape_s3_endpoint_url "$S3_ENDPOINT_AIRFLOW" >/dev/null
docker exec "$AIRFLOW_CONTAINER" airflow variables set grape_s3_region "$S3_REGION" >/dev/null
docker exec "$AIRFLOW_CONTAINER" airflow variables set grape_s3_secure "False" >/dev/null
docker exec "$AIRFLOW_CONTAINER" airflow variables set grape_input_prefix "raw/grapes" >/dev/null
docker exec "$AIRFLOW_CONTAINER" airflow variables set grape_report_prefix "reports" >/dev/null
docker exec "$AIRFLOW_CONTAINER" airflow variables set grape_model_path "model/weights/best.pt" >/dev/null
docker exec "$AIRFLOW_CONTAINER" airflow variables set grape_batch_image "$GRAPE_BATCH_IMAGE" >/dev/null
docker exec "$AIRFLOW_CONTAINER" airflow variables set docker_url "unix://var/run/docker.sock" >/dev/null
docker exec "$AIRFLOW_CONTAINER" airflow variables set docker_network_mode "bridge" >/dev/null

echo "Airflow bootstrap completed."
echo "Connections: grape_s3, grape_postgres"
echo "Variables: grape_* and docker_*"
