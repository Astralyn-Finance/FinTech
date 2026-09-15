from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.security import create_access_token, hash_password, verify_password
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.users = UserRepository(db)

    def register(self, payload: UserCreate) -> User:
        if self.users.get_by_username(payload.username):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Username already registered")
        if self.users.get_by_email(payload.email):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

        user = self.users.create(
            username=payload.username,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role="user",
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def authenticate(self, identifier: str, password: str) -> User:
        """identifier may be a username or an email."""
        user = self.users.get_by_username_or_email(identifier)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                "Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not user.is_active:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Inactive user")
        return user

    def issue_token(self, user: User) -> str:
        return create_access_token(subject=str(user.id), extra_claims={"role": user.role})
