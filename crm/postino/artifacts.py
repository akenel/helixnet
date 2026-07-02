"""Per-lead artifact store — photos, logos, rendered cards, enrichment.json — keyed by the lead's
`artifact_prefix` (e.g. leads/HS-ARTEMIS-COFFEE-0001/photo-1.jpg).

Pluggable backend, same env names as the main app:
  MINIO_ENDPOINT set  → MinIO/S3 object storage (the real thing, when reachable)
  MINIO_ENDPOINT unset → local filesystem (POSTINO_ARTIFACTS_DIR or crm/artifacts/) — works on the
                         laptop today; flip to MinIO later with zero code change, same layout.
Structured, queryable data lives in Postino's DB; blobs + big text live HERE. ext_id is the join.
"""
import io
import os
from pathlib import Path

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "").strip()  # host:port; empty → FS backend
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "postino")
MINIO_SECURE = os.environ.get("MINIO_SECURE", "false").lower() in ("1", "true", "yes")
LOCAL_ROOT = Path(os.environ.get("POSTINO_ARTIFACTS_DIR",
                                 str(Path(__file__).resolve().parent.parent / "artifacts")))

BACKEND = "minio" if MINIO_ENDPOINT else "fs"


def _client():
    from minio import Minio
    c = Minio(MINIO_ENDPOINT, access_key=MINIO_ACCESS_KEY, secret_key=MINIO_SECRET_KEY, secure=MINIO_SECURE)
    if not c.bucket_exists(MINIO_BUCKET):
        c.make_bucket(MINIO_BUCKET)
    return c


def put(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    if BACKEND == "minio":
        _client().put_object(MINIO_BUCKET, key, io.BytesIO(data), length=len(data), content_type=content_type)
    else:
        p = LOCAL_ROOT / key
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return key


def get(key: str) -> bytes | None:
    try:
        if BACKEND == "minio":
            r = _client().get_object(MINIO_BUCKET, key)
            try:
                return r.read()
            finally:
                r.close()
                r.release_conn()
        p = LOCAL_ROOT / key
        return p.read_bytes() if p.exists() else None
    except Exception:
        return None


def list_prefix(prefix: str) -> list[str]:
    """Keys under a lead's prefix (e.g. leads/<ext_id>/)."""
    try:
        if BACKEND == "minio":
            return [o.object_name for o in _client().list_objects(MINIO_BUCKET, prefix=prefix, recursive=True)]
        base = LOCAL_ROOT / prefix
        return [str(p.relative_to(LOCAL_ROOT)) for p in base.rglob("*") if p.is_file()] if base.exists() else []
    except Exception:
        return []


def url(key: str, expires_hours: int = 24) -> str:
    """A link the browser can open: presigned MinIO URL, or a local file path in FS mode."""
    if BACKEND == "minio":
        from datetime import timedelta
        try:
            return _client().presigned_get_object(MINIO_BUCKET, key, expires=timedelta(hours=expires_hours))
        except Exception:
            return ""
    return str(LOCAL_ROOT / key)
