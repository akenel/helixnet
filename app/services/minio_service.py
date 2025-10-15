import asyncio
import logging
from typing import BinaryIO, Union

# --- MinIO components must be imported from the external 'minio' package
from minio import Minio
from minio.error import S3Error, MinioException 

# Assuming this import path exists for settings
from app.core.config import settings

# Used for type hinting the FastAPI UploadFile object in the async method
from fastapi import UploadFile 

# Initialize the logger
logger = logging.getLogger(__name__)

# --- 🥋 CN MinIO Service: Direct Connection & Artifact Management ---

class MinioService:
    """
    Handles all interactions with the MinIO object storage.
    Uses synchronous client methods, which are wrapped in run_in_executor
    for use in asynchronous contexts (like FastAPI routers).
    """

    def __init__(self):
        # NOTE: Minio client constructor takes 'endpoint' without http:// or https://
        endpoint_no_protocol = f"{settings.MINIO_HOST}:{settings.MINIO_PORT}"
        
        self.client = Minio(
            endpoint=endpoint_no_protocol,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
        self.bucket_name = settings.MINIO_BUCKET
        logger.info("MinioService initialized for bucket: %s", self.bucket_name)
    
    def ensure_bucket_exists(self) -> bool:
        """
        Checks if the configured bucket exists and creates it if it does not.
        This should be called on application startup.
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
        Uploads a file-like object to MinIO (synchronous usage, e.g., in a Celery worker).
        
        NOTE: For large file uploads in the router, use upload_file_stream_async instead.
        """
        try:
            # Go to end, get size, then reset to beginning for reading
            data_size = file_data.seek(0, 2)
            file_data.seek(0)
            
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

            # Return the MinIO object key (path)
            return result.object_name 

        except S3Error as e:
            logger.error("MinIO S3 error during upload: %s", e)
            return None
        except Exception as e:
            logger.error("Unexpected error during MinIO upload: %s", e)
            return None

    def download_artifact(self, object_name: str) -> bytes | None:
        """
        Downloads a file from MinIO using the object name (path in bucket).
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
            
    async def upload_file_stream_async(self, file: UploadFile, object_name: str) -> str | None:
        """
        [NEW ASYNC METHOD] Uploads a file stream directly from a FastAPI UploadFile to MinIO.
        This wraps the synchronous MinIO client in an asyncio executor to prevent blocking
        the main FastAPI event loop, ensuring non-blocking I/O.
        
        Args:
            file: The FastAPI UploadFile object stream.
            object_name: The desired path/name of the file in the bucket.

        Returns:
            The MinIO object key (path) or None on failure.
        """
        try:
            # We use file.file (the SpooledTemporaryFile) as the data source.
            # file.size and file.content_type provide the necessary metadata.
            
            loop = asyncio.get_running_loop()
            
            # Run the synchronous put_object in a separate thread (executor=None)
            result = await loop.run_in_executor(None, self.client.put_object,
                self.bucket_name,
                object_name,
                file.file,          # The file-like object stream
                file.size,          # Required length for streaming
                file.content_type,  # MIME type
            )
            
            minio_key = result.object_name
            logger.info(f"✅ Chuck Norris Upload: Streamed object {minio_key} successfully.")
            return minio_key

        except S3Error as e:
            logger.error(f"MinIO S3 streaming error for {object_name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during MinIO streaming upload for {object_name}: {e}")
            return None


# Instantiate the service singleton
minio_service = MinioService()

# This method should be called early in the application lifecycle (e.g., in main.py)
# to ensure the bucket is ready.
def initialize_minio():
    """Wrapper to call the bucket check/creation method."""
    return minio_service.ensure_bucket_exists()
