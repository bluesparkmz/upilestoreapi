import os
import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from fastapi import UploadFile

from core.config import get_settings
from core.exceptions import BadRequestError

settings = get_settings()

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


class BaseStorageProvider(ABC):
    @abstractmethod
    async def save_file(self, file: UploadFile, folder: str = "images") -> tuple[str, str, int]:
        """
        Salva um arquivo no storage.
        Retorna uma tupla (url, filename, file_size).
        """
        pass

    @abstractmethod
    def delete_file(self, file_path: str) -> bool:
        """Elimina um arquivo do storage."""
        pass


class LocalStorageProvider(BaseStorageProvider):
    def __init__(self, base_dir: str = "uploads") -> None:
        self.base_dir = base_dir

    def _validate_file(self, file: UploadFile) -> str:
        if not file.content_type or file.content_type.lower() not in ALLOWED_IMAGE_TYPES:
            raise BadRequestError(
                f"Formato de imagem não suportado: {file.content_type}. Formatos permitidos: JPG, PNG, WEBP, GIF."
            )
        return ALLOWED_IMAGE_TYPES[file.content_type.lower()]

    async def save_file(self, file: UploadFile, folder: str = "images") -> tuple[str, str, int]:
        ext = self._validate_file(file)

        target_dir = Path(self.base_dir) / folder
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = target_dir / filename

        content = await file.read()
        file_size = len(content)

        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if file_size > max_bytes:
            raise BadRequestError(f"Ficheiro excede o tamanho máximo de {settings.max_upload_size_mb}MB.")

        with open(filepath, "wb") as f:
            f.write(content)

        relative_url = f"/{self.base_dir}/{folder}/{filename}".replace("\\", "/")
        return relative_url, filename, file_size

    def delete_file(self, file_path: str) -> bool:
        clean_path = file_path.lstrip("/")
        filepath = Path(clean_path)
        if filepath.exists() and filepath.is_file():
            filepath.unlink()
            return True
        return False


class CloudflareR2StorageProvider(BaseStorageProvider):
    """
    Provedor para Cloudflare R2 (Compatível com S3).
    Pronto para ser ativado quando as credenciais forem fornecidas no .env.
    """

    def __init__(self) -> None:
        if not settings.r2_account_id or not settings.r2_access_key_id:
            raise NotImplementedError("Credenciais do Cloudflare R2 ainda não configuradas no .env")

    async def save_file(self, file: UploadFile, folder: str = "images") -> tuple[str, str, int]:
        # Implementação futura via boto3 / httpx para Cloudflare R2 API
        raise NotImplementedError("Cloudflare R2 ainda não ativado.")

    def delete_file(self, file_path: str) -> bool:
        raise NotImplementedError("Cloudflare R2 ainda não ativado.")


def get_storage_provider() -> BaseStorageProvider:
    if settings.storage_provider == "cloudflare":
        return CloudflareR2StorageProvider()
    return LocalStorageProvider(base_dir=settings.upload_dir)
