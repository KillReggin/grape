# Grape Yield Estimator 

## Назначение
 **прогнозировании урожайности виноградников**


## Предварительные требования
- Python 3.9+
- Docker + Docker Compose
- (опционально) `aws` CLI или `mc`

## Установка
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## ENV-конфигурация
```bash
cp .env.example .env
```

Обязательные поля в `.env`:
- `S3_BUCKET`
- `S3_ENDPOINT_URL`
- `S3_ACCESS_KEY_ID`
- `S3_SECRET_ACCESS_KEY`
- `S3_REGION`
- `S3_SECURE`
- `INPUT_S3_KEY`
- `DATABASE_URL`
- `POSTGRES_PASSWORD`

Загрузить переменные в текущий shell:
```bash
set -a
source .env
set +a
```

## Запуск инфраструктуры
```bash
docker compose --env-file .env -f docker-compose.infra.yml up -d
```

Проверка контейнеров:
```bash
docker compose -f docker-compose.infra.yml ps
```

MinIO Console: `http://localhost:9001`

## Загрузка фото винограда
Вариант `aws`:
```bash
aws --endpoint-url "$S3_ENDPOINT_URL" s3 cp /absolute/path/to/grape.jpg "s3://$S3_BUCKET/$INPUT_S3_KEY"
```

Вариант `mc`:
```bash
mc alias set local "$S3_ENDPOINT_URL" "$S3_ACCESS_KEY_ID" "$S3_SECRET_ACCESS_KEY"
mc cp /absolute/path/to/grape.jpg "local/$S3_BUCKET/$INPUT_S3_KEY"
```

## Запуск приложения
```bash
python -m app.main
```

Ожидаемый stdout:
```text
Total weight: <number> g
```

## Проверка результата

### 1) Проверка PDF в S3/MinIO
```bash
aws --endpoint-url "$S3_ENDPOINT_URL" s3 ls "s3://$S3_BUCKET/"
```
Нужен объект вида `grapes_report_YYYYMMDD_HHMMSS.pdf`.

### 2) Проверка Postgres
Проверять надо SQL-клиентом.

Через docker+psql:
```bash
docker exec -it grape_postgres psql -U grape_user -d grape_db -c "SELECT id, image_ref, total_weight, clusters_count, artifact_uri, created_at FROM prediction_runs ORDER BY id DESC LIMIT 10;"
```

Или внешним клиентом (`DBeaver`, `TablePlus`, `DataGrip`) с параметрами:
- Host: `localhost`
- Port: `5432`
- DB: `grape_db`
- User: `grape_user`
- Password: из `POSTGRES_PASSWORD`

## Тесты
```bash
.venv/bin/pytest -q
.venv/bin/pytest --cov=app --cov-report=term-missing -q
```

## Остановка
```bash
docker compose -f docker-compose.infra.yml down
```

С удалением volume:
```bash
docker compose -f docker-compose.infra.yml down -v
```
