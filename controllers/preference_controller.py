from sqlalchemy import select
from sqlalchemy.orm import Session

from models.user import User
from models.user_preference import UserPreference
from schemas.preference import PreferenceResponse, PreferenceUpdate


class PreferenceController:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create(self, user: User) -> UserPreference:
        """Retorna as preferências do utilizador, criando um registo vazio se não existir."""
        pref = self.db.scalar(
            select(UserPreference).where(UserPreference.user_id == user.id)
        )
        if pref is None:
            pref = UserPreference(user_id=user.id, categories=[], types=[])
            self.db.add(pref)
            self.db.commit()
            self.db.refresh(pref)
        return pref

    def update(self, user: User, data: PreferenceUpdate) -> PreferenceResponse:
        """Cria ou actualiza as preferências do utilizador."""
        pref = self.get_or_create(user)

        pref.categories = data.categories
        pref.types = data.types
        pref.preferred_location = data.preferred_location

        self.db.commit()
        self.db.refresh(pref)
        return PreferenceResponse.model_validate(pref)

    def to_response(self, pref: UserPreference) -> PreferenceResponse:
        return PreferenceResponse.model_validate(pref)
