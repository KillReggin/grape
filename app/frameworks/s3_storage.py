from app.ports.storage_port import StoragePort


class S3Storage(StoragePort):

    def __init__(self, bucket: str):
        self.bucket = bucket

    def save(self, data: bytes, filename: str) -> str:
        return f"s3://{self.bucket}/{filename}"