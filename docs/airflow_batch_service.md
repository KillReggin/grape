# Airflow Batch Service

## Что это
`grape_yield_batch_service` — ежедневный batch-конвейер для обработки фото винограда.

За дату `{{ ds }}` пайплайн:
1. Берет входные фото из S3: `raw/grapes/dt={{ ds }}/`.
2. Запускает инференс в контейнере (`DockerOperator`, `python -m app.batch_main`).
3. Сохраняет отчеты в S3: `reports/dt={{ ds }}/...`.
4. Сохраняет метаданные в Postgres (`prediction_runs`).
5. Пишет success marker: `batch-markers/dt={{ ds }}/_SUCCESS.json`.

## Основные файлы
- `airflow/dags/grape_yield_batch_dag.py` — оркестрация DAG.
- `app/batch_main.py` — batch entrypoint контейнера приложения.
- `Dockerfile` — образ `grape-yield`.
- `docker-compose.airflow.yml` — Airflow (webserver/scheduler/db/init).


## Конфигурация DAG
- `schedule="@daily"`
- `start_date=2026-04-01 UTC`
- `catchup=True`
- `max_active_runs=1`
- `retries=2`, `retry_delay=5m`

## Секреты и конфиг
Секреты не хранятся в коде DAG.

Используется:
- Airflow Connections: `grape_s3`, `grape_postgres`
- Airflow Variables: `grape_*`, `docker_*`

Настраивается автоматически скриптом:
```bash
bash scripts/bootstrap_airflow.sh
```

## Запуск
Полный запуск одним скриптом:
```bash
bash scripts/start_all.sh
```

Скрипт:
1. Проверяет обязательные env.
2. Поднимает infra (`docker-compose.infra.yml`).
3. Поднимает Airflow (`docker-compose.airflow.yml`).
4. Собирает образ `grape-yield:1.0.0`.
5. Прописывает Airflow Connections/Variables.

## Проверка, что сервис готов
```bash
docker compose -f docker-compose.infra.yml ps
docker compose -f docker-compose.airflow.yml ps
docker exec airflow_webserver airflow dags list | rg grape_yield_batch_service
```
