import os
import tempfile

from app.ports.image_source_port import ImageSourcePort


class S3ImageSource(ImageSourcePort):
    def __init__(
        self,
        bucket: str,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        region: str = "us-east-1",
        secure: bool = False,
    ):
        import boto3

        resolved_endpoint = endpoint_url
        if secure and endpoint_url.startswith("http://"):
            resolved_endpoint = endpoint_url.replace("http://", "https://", 1)

        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=resolved_endpoint,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region,
        )

    def fetch_to_temp(self, object_key: str) -> str:
        suffix = os.path.splitext(object_key)[1] or ".jpg"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
            self.client.download_fileobj(self.bucket, object_key, temp_file)
            return temp_file.name

    def cleanup(self, temp_path: str) -> None:
        if os.path.exists(temp_path):
            os.remove(temp_path)
