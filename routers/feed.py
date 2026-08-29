from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from controllers.feed_controller import FeedController
from core.database import get_db
from dependencies.auth import get_optional_current_user
from models.user import User
from schemas.common import ApiResponse, PaginatedData
from schemas.feed import FeedItem, FeedSort

router = APIRouter(prefix="/feed", tags=["Feed"])


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[FeedItem]],
    summary="Feed do marketplace — anúncios activos com ordenação inteligente",
    description="""
Retorna anúncios activos com vários modos de ordenação:

- **recent** — mais recentes primeiro (padrão)
- **oldest** — mais antigos primeiro
- **trending** — mais populares (views + likes da última semana)
- **price_asc** — preço crescente
- **price_desc** — preço decrescente
- **for_you** — personalizado pelas preferências do utilizador; requer autenticação (fallback: trending)

Filtros adicionais: `location`, `category`, `type`, `search`.
""",
)
def get_feed(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User | None, Depends(get_optional_current_user)] = None,
    sort: FeedSort = Query(default="recent", description="Modo de ordenação do feed"),
    location: str | None = Query(
        default=None,
        description="Filtrar por cidade/região do vendedor (ex: Maputo, Beira)",
    ),
    category: str | None = Query(default=None, description="Filtrar por categoria"),
    product_type: str | None = Query(default=None, alias="type", description="Filtrar por tipo de arte"),
    search: str | None = Query(default=None, description="Pesquisar por título, artista ou descrição"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse[PaginatedData[FeedItem]]:
    controller = FeedController(db)
    items, total = controller.get_feed(
        sort=sort,
        location=location,
        category=category,
        product_type=product_type,
        search=search,
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
