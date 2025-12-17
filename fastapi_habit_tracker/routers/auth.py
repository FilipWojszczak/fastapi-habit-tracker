from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import Session, select

from ..db import get_session
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..schemas.user import UserCreate, UserRead
from ..utils.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=UserRead)
async def register_user(
    user_data: UserCreate, session: Annotated[Session, Depends(get_session)]
):
    existing_user = session.exec(
        select(User).where(User.email == user_data.email)
    ).one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=409, detail="User with this email already exists"
        )

    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user


def authenticate_user(email: str, password: str, session: Session) -> User | None:
    user = session.exec(select(User).where(User.email == email)).one_or_none()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)],
):
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token(user.id)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserRead, tags=["auth"])
async def get_my_data(user: Annotated[User, Depends(get_current_user)]):
    return user
