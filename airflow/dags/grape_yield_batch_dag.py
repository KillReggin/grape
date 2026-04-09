import json
from datetime import timedelta

import boto3
import pendulum
import psycopg2
from airflow import DAG
from airflow.hooks.base import BaseHook
from airflow.models import Variable
from airflow.operators.python import PythonOperator, ShortCircuitOperator
from airflow.providers.docker.operators.docker import DockerOperator

DAG_ID = "grape_yield_batch_service"


def _build_s3_endpoint(conn) -> str:
    extra = conn.extra_dejson or {}
    if extra.get("endpoint_url"):
        return extra["endpoint_url"]

    secure = str(extra.get("secure", "false")).lower() in {"true", "1", "yes"}
    scheme = "https" if secure else "http"
    host = conn.host or "localhost"
    port = conn.port or 9000
    return f"{scheme}://{host}:{port}"


def _get_s3_context():
    conn = BaseHook.get_connection("grape_s3")
    endpoint = _build_s3_endpoint(conn)
    bucket = Variable.get("grape_s3_bucket", default_var="grape-artifacts")
    return conn, endpoint, bucket


def _marker_key(ds: str) -> str:
    marker_prefix = Variable.get("grape_marker_prefix", default_var="batch-markers")
    return f"{marker_prefix.rstrip('/')}/dt={ds}/_SUCCESS.json"


def _input_prefix_for_date(ds: str) -> str:
    input_prefix = Variable.get("grape_input_prefix", default_var="raw/grapes").rstrip("/")
    return f"{input_prefix}/dt={ds}/"


def _report_prefix_for_date(ds: str) -> str:
    report_prefix = Variable.get("grape_report_prefix", default_var="reports").rstrip("/")
    return f"{report_prefix}/dt={ds}/"


def _has_inputs_for_date(ds: str, **_):
    conn, endpoint, bucket = _get_s3_context()
    prefix = _input_prefix_for_date(ds)

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=conn.login,
        aws_secret_access_key=conn.password,
        region_name=Variable.get("grape_s3_region", default_var="us-east-1"),
    )

    response = client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1)
    has_input = response.get("KeyCount", 0) > 0
    print(f"Input prefix: s3://{bucket}/{prefix}; has_input={has_input}")
    return has_input


def _validate_outputs(ds: str, **_):
    s3_conn, endpoint, bucket = _get_s3_context()
    report_prefix = _report_prefix_for_date(ds)

    s3_client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=s3_conn.login,
        aws_secret_access_key=s3_conn.password,
        region_name=Variable.get("grape_s3_region", default_var="us-east-1"),
    )

    response = s3_client.list_objects_v2(Bucket=bucket, Prefix=report_prefix, MaxKeys=10)
    report_count = response.get("KeyCount", 0)
    if report_count == 0:
        raise ValueError(f"No report artifacts found under s3://{bucket}/{report_prefix}")

    pg_conn = BaseHook.get_connection("grape_postgres")
    db_port = int(pg_conn.port or 5432)
    db_name = pg_conn.schema or "grape_db"

    with psycopg2.connect(
        host=pg_conn.host,
        port=db_port,
        dbname=db_name,
        user=pg_conn.login,
        password=pg_conn.password,
    ) as db:
        with db.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*)
                FROM prediction_runs
                WHERE image_ref LIKE %s
                """,
                (f"%/dt={ds}/%",),
            )
            (rows_count,) = cur.fetchone()

    if rows_count == 0:
        raise ValueError(f"No DB rows in prediction_runs for dt={ds}")

    print(
        "Validation passed: "
        f"reports_under_prefix={report_count}, prediction_runs_rows_for_dt={rows_count}"
    )


def _write_success_marker(ds: str, run_id: str, **_):
    conn, endpoint, bucket = _get_s3_context()
    marker_key = _marker_key(ds)

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=conn.login,
        aws_secret_access_key=conn.password,
        region_name=Variable.get("grape_s3_region", default_var="us-east-1"),
    )

    payload = {
        "dag_id": DAG_ID,
        "run_id": run_id,
        "ds": ds,
        "status": "success",
    }

    client.put_object(
        Bucket=bucket,
        Key=marker_key,
        Body=json.dumps(payload).encode("utf-8"),
        ContentType="application/json",
    )
    print(f"Wrote idempotency marker: s3://{bucket}/{marker_key}")


default_args = {
    "owner": "ml-platform",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id=DAG_ID,
    description="Batch grape yield inference with DockerOperator",
    start_date=pendulum.datetime(2026, 4, 1, tz="UTC"),
    schedule="@daily",
    catchup=True,
    max_active_runs=1,
    default_args=default_args,
    tags=["batch", "ml", "grape", "docker"],
) as dag:

    run_batch_inference = DockerOperator(
        task_id="run_batch_inference",
        image=Variable.get("grape_batch_image", default_var="grape-yield:1.0.0"),
        command="python -m app.batch_main",
        docker_url=Variable.get("docker_url", default_var="unix://var/run/docker.sock"),
        network_mode=Variable.get("docker_network_mode", default_var="grape_net"),
        auto_remove="success",
        tty=False,
        mount_tmp_dir=False,
        environment={
            "S3_BUCKET": "{{ var.value.grape_s3_bucket }}",
            "S3_ENDPOINT_URL": "{{ var.value.grape_s3_endpoint_url }}",
            "S3_ACCESS_KEY_ID": "{{ conn.grape_s3.login }}",
            "S3_SECRET_ACCESS_KEY": "{{ conn.grape_s3.password }}",
            "S3_REGION": "{{ var.value.grape_s3_region }}",
            "S3_SECURE": "{{ var.value.grape_s3_secure }}",
            "REPORT_S3_PREFIX": "{{ var.value.grape_report_prefix | default('reports', true) }}",
            "DATABASE_URL": "postgresql://{{ conn.grape_postgres.login }}:{{ conn.grape_postgres.password }}@{{ conn.grape_postgres.host }}:{{ conn.grape_postgres.port }}/{{ conn.grape_postgres.schema }}",
            "MODEL_PATH": "{{ var.value.grape_model_path }}",
            "INPUT_S3_PREFIX": "{{ var.value.grape_input_prefix }}",
            "BATCH_DATE": "{{ ds }}",
        },
    )

    check_inputs = ShortCircuitOperator(
        task_id="check_input_images",
        python_callable=_has_inputs_for_date,
        op_kwargs={"ds": "{{ ds }}"},
    )

    validate_outputs = PythonOperator(
        task_id="validate_outputs",
        python_callable=_validate_outputs,
        op_kwargs={"ds": "{{ ds }}"},
    )

    write_success_marker = PythonOperator(
        task_id="write_success_marker",
        python_callable=_write_success_marker,
        op_kwargs={"ds": "{{ ds }}", "run_id": "{{ run_id }}"},
    )

    check_inputs >> run_batch_inference >> validate_outputs >> write_success_marker
