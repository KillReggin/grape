set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -f ".env" ]]; then
  echo ".env file not found. Create it from .env.example first." >&2
  exit 1
fi

echo "Loading env..."
set -a
source ".env"
set +a

required_vars=(
  S3_BUCKET
  S3_ACCESS_KEY_ID
  S3_SECRET_ACCESS_KEY
  S3_REGION
  POSTGRES_PASSWORD
  AIRFLOW_DB_USER
  AIRFLOW_DB_PASSWORD
  AIRFLOW_DB_NAME
  AIRFLOW_ADMIN_USERNAME
  AIRFLOW_ADMIN_PASSWORD
  AIRFLOW_ADMIN_FIRSTNAME
  AIRFLOW_ADMIN_LASTNAME
  AIRFLOW_ADMIN_EMAIL
  AIRFLOW_FERNET_KEY
)

for var_name in "${required_vars[@]}"; do
  if [[ -z "${!var_name:-}" ]]; then
    echo "Missing required env var: $var_name" >&2
    echo "Fill it in .env (see .env.example) and run again." >&2
    exit 1
  fi
done

echo "Starting infra (MinIO + Postgres)..."
docker compose --env-file .env -f docker-compose.infra.yml up -d

echo "Starting Airflow (db + init + webserver + scheduler)..."
docker compose --env-file .env -f docker-compose.airflow.yml up -d

echo "Building batch image..."
docker build -t grape-yield:1.0.0 .

echo "Bootstrapping Airflow Connections/Variables..."
bash scripts/bootstrap_airflow.sh

echo
echo "Done."
echo "MinIO Console: http://localhost:9001"
echo "Airflow UI:    http://localhost:8080"
echo
echo "Infra containers:"
docker compose -f docker-compose.infra.yml ps
echo
echo "Airflow containers:"
docker compose -f docker-compose.airflow.yml ps
