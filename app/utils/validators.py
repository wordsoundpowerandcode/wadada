from fastapi import UploadFile
from app.config import settings

async def validate_media_file(file: UploadFile) -> dict:
    """Validate uploaded media file"""
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset
    
    if file_size > settings.MAX_FILE_SIZE:
        return {
            "valid": False,
            "error": f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE / (1024*1024)}MB"
        }
    
    # Check file type
    mime_type = file.content_type
    allowed_types = settings.allowed_video_types_list + settings.allowed_audio_types_list
    
    if mime_type not in allowed_types:
        return {
            "valid": False,
            "error": f"File type {mime_type} not allowed. Allowed types: {', '.join(allowed_types)}"
        }
    
    return {"valid": True}

