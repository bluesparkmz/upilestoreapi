from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from core.storage import get_storage_provider
from dependencies.auth import get_current_active_user
from models.user import User
from schemas.common import ApiResponse
from schemas.upload import MultiUploadResponse, UploadResponse

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post(
    "/image",
    response_model=ApiResponse[UploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload de uma imagem",
    description="Aceita imagens nos formatos JPG, PNG, WEBP e GIF (máx: 10MB).",
)
async def upload_image(
    file: Annotated[UploadFile, File(description="Ficheiro de imagem a carregar")],
    current_user: Annotated[User, Depends(get_current_active_user)],
    folder: str = Query(default="images", description="Subpasta de destino (ex: images, avatars)"),
) -> ApiResponse[UploadResponse]:
    storage = get_storage_provider()
    url, filename, size = await storage.save_file(file, folder=folder)

    return ApiResponse(
        data=UploadResponse(
            url=url,
            filename=filename,
            content_type=file.content_type or "image/jpeg",
            size=size,
        )
    )


@router.post(
    "/images",
    response_model=ApiResponse[MultiUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload de múltiplas imagens",
    description="Aceita várias imagens de uma só vez.",
)
async def upload_multiple_images(
    files: Annotated[list[UploadFile], File(description="Lista de ficheiros de imagem")],
    current_user: Annotated[User, Depends(get_current_active_user)],
    folder: str = Query(default="images", description="Subpasta de destino"),
) -> ApiResponse[MultiUploadResponse]:
    storage = get_storage_provider()
    results: list[UploadResponse] = []

    for file in files:
        url, filename, size = await storage.save_file(file, folder=folder)
        results.append(
            UploadResponse(
                url=url,
                filename=filename,
                content_type=file.content_type or "image/jpeg",
                size=size,
            )
        )

    return ApiResponse(
        data=MultiUploadResponse(
            files=results,
            total=len(results),
        )
    )
