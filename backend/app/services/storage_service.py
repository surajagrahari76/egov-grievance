import secrets
import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from app.core.config import get_settings

settings = get_settings()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}


async def save_validated_upload(file: UploadFile, grievance_ticket: str) -> dict:
    """Validate file extension, MIME type, and size before writing to upload directory."""
    original_name = Path(file.filename or "attachment").name
    ext = Path(original_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    mime_type = (file.content_type or "").lower()
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported MIME type '{mime_type}'. Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}",
        )

    content = await file.read()
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB",
        )

    upload_root = Path(settings.UPLOAD_DIR) / grievance_ticket
    upload_root.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex[:12]}_{secrets.token_hex(4)}{ext}"
    target = upload_root / safe_name
    target.write_bytes(content)

    return {
        "file_path": f"{grievance_ticket}/{safe_name}",
        "original_name": original_name,
        "mime_type": mime_type,
        "size_bytes": len(content),
    }
