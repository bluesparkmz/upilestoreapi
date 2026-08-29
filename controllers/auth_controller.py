from sqlalchemy import select
from sqlalchemy.orm import Session

from core.exceptions import ConflictError, NotFoundError, UnauthorizedError
from core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    get_token_subject,
    verify_password,
)
from models.user import User
from schemas.user import TokenData, UserLogin, UserRegister, UserUpdate


class AuthController:
    def __init__(self, db: Session) -> None:
        self.db = db

    def register(self, data: UserRegister) -> User:
        if self.db.scalar(select(User).where(User.email == data.email)):
            raise ConflictError("Email já registado")

        if self.db.scalar(select(User).where(User.username == data.username)):
            raise ConflictError("Username já registado")

        user = User(
            name=data.name,
            username=data.username,
            email=data.email,
            password_hash=get_password_hash(data.password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, data: UserLogin) -> TokenData:
        user = self.db.scalar(select(User).where(User.email == data.email))
        if user is None or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Email ou password incorretos")

        if not user.is_active:
            raise UnauthorizedError("Conta de usuário inativa")

        return TokenData(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    def refresh_tokens(self, refresh_token: str) -> TokenData:
        try:
            user_id = get_token_subject(refresh_token, expected_type="refresh")
        except Exception as exc:
            raise UnauthorizedError("Refresh token inválido") from exc

        user = self.db.get(User, user_id)
        if user is None or not user.is_active:
            raise UnauthorizedError("Usuário inválido ou inativo")

        return TokenData(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )

    def get_user_by_id(self, user_id: int) -> User:
        user = self.db.get(User, user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        return user

    def update_user(self, user: User, data: UserUpdate) -> User:
        update_data = data.model_dump(exclude_unset=True)

        if "username" in update_data and update_data["username"] != user.username:
            existing = self.db.scalar(select(User).where(User.username == update_data["username"]))
            if existing:
                raise ConflictError("Username já registado")

        for field, value in update_data.items():
            setattr(user, field, value)

        self.db.commit()
        self.db.refresh(user)
        return user
