from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlmodel import Session, select

from ..db import get_session
from ..dependencies.auth import get_current_user
from ..models.user import User
from ..schemas.user import UserCreate, UserRead
from ..utils.security import authenticate_user, create_access_token, hash_password

router = APIRouter(prefix="/auth", tags=["auth"])


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post(
    "/register",
    response_model=UserRead,
    summary="Register a new user account",
    description=(
        "Creates a new user account using email and password.  \n"
        "Validates that the email is unique and stores the password using a secure "
        "hash.\n\n"
        "This endpoint is publicly accessible and does not require authentication."
    ),
)
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


@router.post(
    "/token",
    summary="Log in and obtain an access token",
    description=(
        "Authenticates the user using email and password. "
        "Returns a JWT access token that must be included in the `Authorization: "
        "Bearer <token>` header for all protected endpoints.\n\n"
        "This endpoint follows the OAuth2 Password Flow used by FastAPI's built-in "
        "`OAuth2PasswordRequestForm`. Note that `username` in the form corresponds to "
        "the user's email."
    ),
)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)],
):
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    access_token = create_access_token(user.id)
    return Token(access_token=access_token)


@router.get(
    "/me",
    response_model=UserRead,
    summary="Retrieve data about authenticated user",
    description=(
        "Return `id`, `email` and activity state (flag which shows if account "
        "is active)."
    ),
)
async def get_my_data(user: Annotated[User, Depends(get_current_user)]):
    return user
