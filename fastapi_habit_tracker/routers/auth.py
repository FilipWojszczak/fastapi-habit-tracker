from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..db import get_session
from ..models.user import User
from ..schemas.user import UserCreate, UserRead
from ..utils.security import hash_password

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UserRead)
async def register_user(user_data: UserCreate, session: Session = Depends(get_session)):
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


@router.post("/login")
async def login_user():
    pass
