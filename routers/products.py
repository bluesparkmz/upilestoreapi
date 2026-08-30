from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from dependencies.auth import get_current_active_user, get_optional_current_user
from models.user import User
from schemas.common import ApiResponse, PaginatedData
from schemas.product import (
    ProductCreate,
    ProductImageCreate,
    ProductImageResponse,
    ProductListItem,
    ProductResponse,
    ProductUpdate,
)
from controllers.product_controller import ProductController

router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "",
    response_model=ApiResponse[ProductResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova obra de arte",
)
def create_product(
    data: ProductCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ProductResponse]:
    service = ProductController(db)
    product = service.create_product(current_user, data)
    return ApiResponse(data=service.build_product_response(product, current_user))


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[ProductListItem]],
    summary="Listar obras com filtros e pesquisa",
)
def list_products(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
    search: str | None = Query(default=None, description="Pesquisar por título, artista ou descrição"),
    category: str | None = Query(default=None),
    product_type: str | None = Query(default=None, alias="type"),
    owner_id: int | None = Query(default=None, description="Filtrar produtos por utilizador (owner_id)"),
    sort_by: str = Query(default="created_at", pattern="^(created_at|price)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[PaginatedData[ProductListItem]]:
    service = ProductController(db)
    items, total = service.list_products(
        search=search,
        category=category,
        product_type=product_type,
        owner_id=owner_id,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
        current_user=current_user,
    )
    pages = (total + page_size - 1) // page_size if total else 0
    return ApiResponse(
        data=PaginatedData(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    )


@router.get(
    "/{product_id}",
    response_model=ApiResponse[ProductResponse],
    summary="Visualizar detalhes de uma obra",
)
def get_product(
    product_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
) -> ApiResponse[ProductResponse]:
    service = ProductController(db)
    product = service.get_product(product_id)
    return ApiResponse(data=service.build_product_response(product, current_user))


@router.put(
    "/{product_id}",
    response_model=ApiResponse[ProductResponse],
    summary="Atualizar obra de arte",
)
def update_product(
    product_id: int,
    data: ProductUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ProductResponse]:
    service = ProductController(db)
    product = service.get_product(product_id)
    updated = service.update_product(product, current_user, data)
    return ApiResponse(data=service.build_product_response(updated, current_user))


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Apagar obra de arte",
)
def delete_product(
    product_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    service = ProductController(db)
    product = service.get_product(product_id)
    service.delete_product(product, current_user)


@router.post(
    "/{product_id}/images",
    response_model=ApiResponse[ProductImageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar imagem à obra",
)
def add_product_image(
    product_id: int,
    data: ProductImageCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ProductImageResponse]:
    service = ProductController(db)
    product = service.get_product(product_id)
    image = service.add_image(product, current_user, data)
    return ApiResponse(data=ProductImageResponse.model_validate(image))


@router.delete(
    "/{product_id}/images/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover imagem da obra",
)
def delete_product_image(
    product_id: int,
    image_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    service = ProductController(db)
    product = service.get_product(product_id)
    service.delete_image(product, image_id, current_user)


@router.put(
    "/{product_id}/images/{image_id}/primary",
    response_model=ApiResponse[ProductImageResponse],
    summary="Definir imagem principal da obra",
)
def set_primary_image(
    product_id: int,
    image_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ProductImageResponse]:
    service = ProductController(db)
    product = service.get_product(product_id)
    image = service.set_primary_image(product, image_id, current_user)
    return ApiResponse(data=ProductImageResponse.model_validate(image))
