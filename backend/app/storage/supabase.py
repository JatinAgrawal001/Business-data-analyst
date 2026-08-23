from typing import Optional, Dict, Any
from app.core.config import settings
from app.services.supabase_client import supabase_manager
from app.utils.sanitization import sanitize_path_component, generate_secure_filename
from app.core.logging import get_logger

logger = get_logger("app.storage.supabase")

class SupabaseStorageService:
    """
    Handles secure, multi-tenant isolated file storage in Supabase Storage buckets.
    Path structure: {user_id}/{project_id}/{secure_filename}
    """

    def __init__(self):
        self.bucket = settings.DATASET_STORAGE_BUCKET

    def build_storage_path(self, user_id: str, project_id: str, original_filename: str) -> Dict[str, str]:
        """
        Builds a sanitized, collision-resistant path within the tenant storage space.
        """
        clean_uid = sanitize_path_component(user_id)
        clean_pid = sanitize_path_component(project_id)
        secure_filename = generate_secure_filename(original_filename)
        path = f"{clean_uid}/{clean_pid}/{secure_filename}"

        return {
            "bucket": self.bucket,
            "path": path,
            "filename": secure_filename
        }

    async def upload_file(
        self,
        file_bytes: bytes,
        original_filename: str,
        user_id: str,
        project_id: str,
        content_type: str = "text/csv",
        user_jwt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Uploads dataset bytes to Supabase Storage.
        """
        path_info = self.build_storage_path(user_id, project_id, original_filename)
        client = supabase_manager.get_user_scoped_client(user_jwt) or supabase_manager.get_anon_client()

        if client:
            try:
                client.storage.from_(self.bucket).upload(
                    path=path_info["path"],
                    file=file_bytes,
                    file_options={
                        "content-type": content_type,
                        "upsert": "true"
                    }
                )
                logger.info(f"File uploaded to Supabase Storage: {path_info['path']}")
            except Exception as e:
                logger.warning(f"Supabase storage upload note: {e}")

        return {
            "storageBucket": self.bucket,
            "storagePath": path_info["path"],
            "fileName": path_info["filename"],
            "sizeBytes": len(file_bytes),
            "userId": user_id,
            "projectId": project_id
        }

    async def download_file(self, storage_path: str, user_jwt: Optional[str] = None) -> Optional[bytes]:
        """
        Downloads dataset bytes from Supabase Storage.
        """
        client = supabase_manager.get_user_scoped_client(user_jwt) or supabase_manager.get_anon_client()
        if not client:
            return None

        try:
            data = client.storage.from_(self.bucket).download(storage_path)
            return data
        except Exception as e:
            logger.warning(f"Error downloading file from storage ({storage_path}): {e}")
            return None

    async def delete_file(self, storage_path: str, user_jwt: Optional[str] = None) -> bool:
        """
        Deletes a dataset file from Supabase Storage.
        """
        client = supabase_manager.get_user_scoped_client(user_jwt) or supabase_manager.get_anon_client()
        if not client:
            return True

        try:
            client.storage.from_(self.bucket).remove([storage_path])
            return True
        except Exception as e:
            logger.warning(f"Error deleting file from storage ({storage_path}): {e}")
            return False

storage_service = SupabaseStorageService()
