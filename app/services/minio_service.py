import logging
from typing import BinaryIO

# --- CRITICAL FIX: Ensure MinIO components are imported from the external 'minio' package, 
# --- NOT from app.services.minio_service (which causes a circular import).
from minio import Minio
from minio.error import S3Error, MinioException # FIX: Importing both exceptions from minio.error

from app.core.config import settings

# Initialize the logger
logger = logging.getLogger(__name__)

# --- 🥋 CN MinIO Service: Direct Connection & Artifact Management ---

class MinioService:
    """
    Handles all interactions with the MinIO object storage.
    Uses synchronous client methods, primarily intended for use
    within synchronous contexts like Celery tasks.
    """

    def __init__(self):
        # NOTE: Minio client constructor takes 'endpoint' without http:// or https://
        endpoint_no_protocol = f"{settings.MINIO_HOST}:{settings.MINIO_PORT}"
        
        self.client = Minio(
            endpoint=endpoint_no_protocol,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
            # For debugging connection issues:
            # http_client=requests.Session() 
        )
        self.bucket_name = settings.MINIO_BUCKET
        logger.info("MinioService initialized for bucket: %s", self.bucket_name)
    
    def ensure_bucket_exists(self) -> bool:
        """
        Checks if the configured bucket exists and creates it if it does not.
        This should be called on application startup or before the first upload.
        """
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info("✅ MinIO bucket '%s' created successfully.", self.bucket_name)
            else:
                logger.info("MinIO bucket '%s' already exists.", self.bucket_name)
            return True
        except S3Error as e:
            logger.error("MinIO S3 error during bucket check/creation: %s", e)
            return False
        except MinioException as e:
            logger.error("MinIO client error (check connectivity/credentials): %s", e)
            return False
        except Exception as e:
            logger.critical("Unexpected error in MinIO setup: %s", e)
            return False

    def upload_artifact(self, file_data: BinaryIO, object_name: str, content_type: str) -> str | None:
        """
        Uploads a file-like object to MinIO and returns its public URL path.

        Args:
            file_data: A file-like object containing the data to upload.
            object_name: The desired path/name of the file in the bucket (e.g., 'jobs/uuid/result.json').
            content_type: The MIME type of the data (e.g., 'application/json').

        Returns:
            The public URL to the stored artifact, or None on failure.
        """
        try:
            # file_data.seek(0) # Ensure the file pointer is at the start if needed
            data_size = file_data.seek(0, 2)  # Go to end, get size
            file_data.seek(0) # Reset to beginning for reading
            
            result = self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=file_data,
                length=data_size,
                content_type=content_type,
            )
            
            logger.info(
                "Uploaded object: %s/%s. ETag: %s", 
                result.bucket_name, result.object_name, result.etag
            )

            # Construct the external URL (this assumes MinIO is accessible externally 
            # via a host/port, which is true in a Docker/local setup)
            artifact_url = f"{settings.MINIO_ENDPOINT_URL}/{self.bucket_name}/{object_name}"
            return artifact_url

        except S3Error as e:
            logger.error("MinIO S3 error during upload: %s", e)
            return None
        except Exception as e:
            logger.error("Unexpected error during MinIO upload: %s", e)
            return None

    def download_artifact(self, object_name: str) -> bytes | None:
        """
        Downloads a file from MinIO using the object name (path in bucket).

        Args:
            object_name: The desired path/name of the file in the bucket (e.g., 'jobs/uuid/result.json').

        Returns:
            The file content as bytes, or None on failure.
        """
        try:
            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
            )
            # Read all data from the response stream
            file_content = response.read() 
            response.close()
            response.release_conn() # Release the connection pool resource
            
            logger.info("Downloaded object: %s/%s", self.bucket_name, object_name)
            return file_content

        except S3Error as e:
            logger.error("MinIO S3 error during download: %s", e)
            return None
        except Exception as e:
            logger.error("Unexpected error during MinIO download: %s", e)
            return None


# Instantiate the service singleton
minio_service = MinioService()

# This method should be called early in the application lifecycle (e.g., in main.py)
# to ensure the bucket is ready.
def initialize_minio():
    """Wrapper to call the bucket check/creation method."""
    return minio_service.ensure_bucket_exists()
