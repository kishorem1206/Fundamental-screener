"""Thin MinIO (S3-compatible) wrapper — Architecture v2 Stage 7. Durable raw
document storage, closing a real gap: BSE filing PDFs previously only
existed in Redis with a 24h TTL and were gone after that (an extracted
GNPA/NNPA/CAR value couldn't be re-verified against its source PDF past a
day); NSE annual reports were already durable on local disk but only on
this one machine, with no checksum or queryable metadata. Same lazy-
singleton-client pattern as app/infrastructure/redis/client.py.
"""
from __future__ import annotations

import hashlib
import io

from minio import Minio
from minio.error import S3Error

from app.config import config
from app.logger import logger

_client: Minio | None = None
_bucket_ensured = False


def _get_client() -> Minio | None:
    global _client, _bucket_ensured
    if _client is None:
        try:
            _client = Minio(
                config.minio_endpoint,
                access_key=config.minio_access_key,
                secret_key=config.minio_secret_key,
                secure=config.minio_secure,
            )
        except Exception as e:
            logger.warning("MinIO client init failed", error=str(e))
            return None
    if not _bucket_ensured:
        try:
            if not _client.bucket_exists(config.minio_bucket):
                _client.make_bucket(config.minio_bucket)
            _bucket_ensured = True
        except Exception as e:
            logger.warning("MinIO bucket check/create failed", error=str(e))
            return None
    return _client


def put_document(storage_key: str, content: bytes, content_type: str = "application/pdf") -> str | None:
    """Store bytes under `storage_key`, return their sha256 hex digest, or
    None on failure (never raises — matching every ingestion path's
    graceful-degradation contract; a failed MinIO write shouldn't break the
    caller's actual ingestion)."""
    client = _get_client()
    if client is None:
        return None
    sha256 = hashlib.sha256(content).hexdigest()
    try:
        client.put_object(
            config.minio_bucket, storage_key, io.BytesIO(content), length=len(content),
            content_type=content_type,
        )
        return sha256
    except S3Error as e:
        logger.warning("MinIO put_object failed", storage_key=storage_key, error=str(e))
        return None


def get_document(storage_key: str) -> bytes | None:
    """Fetch bytes by storage_key, or None if missing/unreachable."""
    client = _get_client()
    if client is None:
        return None
    try:
        response = client.get_object(config.minio_bucket, storage_key)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()
    except S3Error as e:
        logger.warning("MinIO get_object failed", storage_key=storage_key, error=str(e))
        return None
