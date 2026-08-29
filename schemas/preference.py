from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PreferenceUpdate(BaseModel):
    """Payload para actualizar as preferências do utilizador."""

    categories: list[str] = Field(
        default_factory=list,
        description="Categorias de arte preferidas (ex: pintura, escultura)",
    )
    types: list[str] = Field(
        default_factory=list,
        description="Tipos de produto preferidos (ex: original, impressão)",
    )
    preferred_location: str | None = Field(
        default=None,
        max_length=255,
        description="Localização preferida para filtrar o feed",
    )


class PreferenceResponse(BaseModel):
    """Resposta com as preferências guardadas."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    categories: list[str]
    types: list[str]
    preferred_location: str | None
    created_at: datetime
    updated_at: datetime
