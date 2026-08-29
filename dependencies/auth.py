from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from core.database import get_db
from core.exceptions import ForbiddenError, UnauthorizedError
from core.security import TokenValidationError, get_token_subject
from models.user import User

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Token de autenticação ausente")

    try:
        user_id = get_token_subject(credentials.credentials, expected_type="access")
    except TokenValidationError as exc:
        raise UnauthorizedError(str(exc)) from exc

    user = db.get(User, user_id)
    if user is None:
        raise UnauthorizedError("Usuário não encontrado")

    return user


def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise ForbiddenError("Conta de usuário inativa")
    return current_user


def get_current_admin(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if not current_user.is_admin:
        raise ForbiddenError("Acesso restrito a administradores")
    return current_user


def get_optional_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | None:
    if credentials is None or not credentials.credentials:
        return None

    try:
        user_id = get_token_subject(credentials.credentials, expected_type="access")
    except TokenValidationError:
        return None

    return db.get(User, user_id)


def get_user_from_token(token: str, db: Session) -> User | None:
    """Helper para autenticar token JWT (usado em WebSockets)."""
    if not token:
        return None
    try:
        user_id = get_token_subject(token, expected_type="access")
    except TokenValidationError:
        return None

    user = db.get(User, user_id)
    if user and user.is_active:
        return user
    return None
