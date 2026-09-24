from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead
from app.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    return AuthService(db).register(payload)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """form_data.username accepts either a username or an email."""
    service = AuthService(db)
    user = service.authenticate(form_data.username, form_data.password)
    return Token(access_token=service.issue_token(user))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_active_user)):
    return current_user
