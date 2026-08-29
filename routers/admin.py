from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from controllers.admin_controller import AdminController
from controllers.product_controller import ProductController
from core.database import get_db
from dependencies.auth import get_current_admin
from models.user import User
from schemas.admin import AdminProductUpdate, AdminUserResponse, AdminUserUpdate
from schemas.common import ApiResponse, MessageData, PaginatedData
from schemas.product import ProductResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


# ═══════════════════════════════════════════════════════════════════════════════
# UTILIZADORES
# ═══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/users",
    response_model=ApiResponse[PaginatedData[AdminUserResponse]],
    summary="[Admin] Listar todos os utilizadores",
)
def admin_list_users(
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    search: str | None = Query(default=None, description="Filtrar por nome, username ou email"),
    is_active: bool | None = Query(default=None, description="Filtrar por estado ativo"),
    is_admin: bool | None = Query(default=None, description="Filtrar apenas admins"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[PaginatedData[AdminUserResponse]]:
    controller = AdminController(db)
    users, total = controller.list_users(
        search=search,
        is_active=is_active,
        is_admin=is_admin,
        page=page,
        page_size=page_size,
    )
    pages = (total + page_size - 1) // page_size if total else 0
    return ApiResponse(
        data=PaginatedData(
            items=[AdminUserResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    )


@router.get(
    "/users/{user_id}",
    response_model=ApiResponse[AdminUserResponse],
    summary="[Admin] Ver detalhes de um utilizador",
)
def admin_get_user(
    user_id: int,
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[AdminUserResponse]:
    user = AdminController(db).get_user(user_id)
    return ApiResponse(data=AdminUserResponse.model_validate(user))


@router.put(
    "/users/{user_id}",
    response_model=ApiResponse[AdminUserResponse],
    summary="[Admin] Editar utilizador",
)
def admin_update_user(
    user_id: int,
    data: AdminUserUpdate,
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[AdminUserResponse]:
    user = AdminController(db).update_user(user_id, data)
    return ApiResponse(data=AdminUserResponse.model_validate(user))


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] Eliminar utilizador",
)
def admin_delete_user(
    user_id: int,
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    AdminController(db).delete_user(user_id, current_admin)


@router.patch(
    "/users/{user_id}/toggle-active",
    response_model=ApiResponse[AdminUserResponse],
    summary="[Admin] Ativar / desativar conta de utilizador",
)
def admin_toggle_active(
    user_id: int,
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[AdminUserResponse]:
    user = AdminController(db).toggle_active(user_id, current_admin)
    return ApiResponse(data=AdminUserResponse.model_validate(user))


@router.patch(
    "/users/{user_id}/toggle-verified",
    response_model=ApiResponse[AdminUserResponse],
    summary="[Admin] Verificar / desverificar conta de utilizador",
)
def admin_toggle_verified(
    user_id: int,
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[AdminUserResponse]:
    user = AdminController(db).toggle_verified(user_id)
    return ApiResponse(data=AdminUserResponse.model_validate(user))


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUTOS
# ═══════════════════════════════════════════════════════════════════════════════


@router.get(
    "/products",
    response_model=ApiResponse[PaginatedData[ProductResponse]],
    summary="[Admin] Listar todos os produtos",
)
def admin_list_products(
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
    search: str | None = Query(default=None, description="Filtrar por título, artista ou descrição"),
    owner_id: int | None = Query(default=None, description="Filtrar por dono do produto"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[PaginatedData[ProductResponse]]:
    admin_ctrl = AdminController(db)
    product_ctrl = ProductController(db)

    products, total = admin_ctrl.list_all_products(
        search=search,
        owner_id=owner_id,
        page=page,
        page_size=page_size,
    )
    pages = (total + page_size - 1) // page_size if total else 0
    items = [product_ctrl.build_product_response(p, current_admin) for p in products]

    return ApiResponse(
        data=PaginatedData(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )
    )


@router.put(
    "/products/{product_id}",
    response_model=ApiResponse[ProductResponse],
    summary="[Admin] Editar qualquer produto",
)
def admin_update_product(
    product_id: int,
    data: AdminProductUpdate,
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> ApiResponse[ProductResponse]:
    admin_ctrl = AdminController(db)
    product_ctrl = ProductController(db)

    product = admin_ctrl.admin_update_product(product_id, data)
    return ApiResponse(data=product_ctrl.build_product_response(product, current_admin))


@router.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="[Admin] Eliminar qualquer produto",
)
def admin_delete_product(
    product_id: int,
    current_admin: Annotated[User, Depends(get_current_admin)],
    db: Annotated[Session, Depends(get_db)],
) -> None:
    AdminController(db).admin_delete_product(product_id)
