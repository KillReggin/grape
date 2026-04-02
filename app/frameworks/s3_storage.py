from typing import Optional

from app.ports.storage_port import StoragePort


class S3Storage(StoragePort):
    def __init__(
        self,
        bucket: str,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        region: str = "us-east-1",
        secure: bool = False,
        key_prefix: Optional[str] = None,
    ):
        import boto3
        from botocore.exceptions import ClientError

        if not bucket:
            raise ValueError("S3 bucket must be provided")

        self.bucket = bucket
        self.key_prefix = key_prefix.strip("/") if key_prefix else None

        resolved_endpoint = endpoint_url
        if secure and endpoint_url.startswith("http://"):
            resolved_endpoint = endpoint_url.replace("http://", "https://", 1)

        self.client = boto3.client(
            "s3",
            endpoint_url=resolved_endpoint,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
        )
        self._client_error = ClientError
        self._ensure_bucket_exists(region)

    def _ensure_bucket_exists(self, region: str) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
            return
        except self._client_error as exc:
            code = exc.response.get("Error", {}).get("Code")
            if code not in {"404", "NoSuchBucket"}:
                raise

        if region == "us-east-1":
            self.client.create_bucket(Bucket=self.bucket)
            return

        self.client.create_bucket(
            Bucket=self.bucket,
            CreateBucketConfiguration={"LocationConstraint": region},
        )

    def _build_key(self, filename: str) -> str:
        clean_name = filename.lstrip("/")
        if self.key_prefix:
            return f"{self.key_prefix}/{clean_name}"
        return clean_name

    def save(self, data: bytes, filename: str) -> str:
        key = self._build_key(filename)
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType="application/pdf",
        )
        return f"s3://{self.bucket}/{key}"
