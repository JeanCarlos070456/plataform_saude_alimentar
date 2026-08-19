from __future__ import annotations

import uuid
from pathlib import PurePosixPath

from django.conf import settings
from django.core.exceptions import ValidationError
from supabase import create_client


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def validate_image_upload(uploaded_file) -> str:
    if uploaded_file.size > MAX_IMAGE_BYTES:
        raise ValidationError("A imagem deve ter no máximo 5 MB.")
    content_type = (getattr(uploaded_file, "content_type", "") or "").lower()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValidationError("Formato inválido. Use JPG, PNG ou WEBP.")
    return content_type


def upload_public_image(uploaded_file, folder: str) -> tuple[str, str]:
    content_type = validate_image_upload(uploaded_file)

    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValidationError("Supabase Storage não está configurado no servidor.")
    if not settings.SUPABASE_MEDIA_BUCKET:
        raise ValidationError("SUPABASE_MEDIA_BUCKET não está configurado.")

    suffix = ALLOWED_IMAGE_TYPES[content_type]
    safe_folder = str(PurePosixPath(folder)).strip("/")
    object_path = f"{safe_folder}/{uuid.uuid4().hex}{suffix}"

    uploaded_file.seek(0)
    raw = uploaded_file.read()

    client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    bucket = client.storage.from_(settings.SUPABASE_MEDIA_BUCKET)
    bucket.upload(
        path=object_path,
        file=raw,
        file_options={
            "content-type": content_type,
            "cache-control": "3600",
            "upsert": "false",
        },
    )
    public_url = bucket.get_public_url(object_path)
    return str(public_url), object_path
