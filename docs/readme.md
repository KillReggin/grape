# Grape Yield Estimator 

## Назначение
 **прогнозировании урожайности виноградников**

## Структура проекта
```text
app/
  main.py                        # composition root (wiring)
  config.py                      # переменные

  entities/                      # доменные сущности
    detection_result.py
    grape_cluster.py
    prediction_result.py

  use_cases/                     # бизнес-логика
    process_image.py

  ports/                         # абстракции (контракты)
    detector_port.py
    report_port.py
    storage_port.py
    image_source_port.py
    prediction_log_port.py

  interface_adapters/            # адаптеры входа/выхода
    cli.py

  frameworks/                    # реализации портов
    yolo_model.py
    report_generate.py
    s3_storage.py
    s3_image_source.py
    postgres_prediction_log.py

tests/
  fakes.py                      unit-тесты
  test_use_case_basic.py
  test_use_case_edge.py
  test_frustum.py
  test_main_and_config.py

docs/
  readme.md
  clean_architecture_review.md
```


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
