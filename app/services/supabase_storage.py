from supabase import create_client, Client
from app.config import settings
from typing import BinaryIO, Optional
import uuid

class SupabaseStorageService:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        self.bucket = settings.STORAGE_BUCKET
    
    async def upload_file(
        self, 
        file: BinaryIO, 
        user_id: str, 
        media_type: str,
        file_extension: str
    ) -> str:
        """Upload file to Supabase Storage and return public URL"""
        # Generate unique filename
        file_name = f"{user_id}/{uuid.uuid4()}.{file_extension}"
        
        # Read file content
        file_content = file.read()
        
        # Upload file
        response = self.client.storage.from_(self.bucket).upload(
            file_name,
            file_content,
            file_options={"content-type": media_type}
        )
        
        # Get public URL
        public_url = self.client.storage.from_(self.bucket).get_public_url(file_name)
        return public_url
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Supabase Storage"""
        try:
            # Extract path from URL
            if f"/{self.bucket}/" in file_path:
                path = file_path.split(f"/{self.bucket}/")[-1]
            else:
                # Assume it's already a path
                path = file_path
            self.client.storage.from_(self.bucket).remove([path])
            return True
        except Exception:
            return False
    
    def get_public_url(self, file_path: str) -> str:
        """Generate public URL for a file path"""
        return self.client.storage.from_(self.bucket).get_public_url(file_path)

