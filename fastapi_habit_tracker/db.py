from sqlmodel import Session, create_engine

from . import models  # noqa: F401
from .config import get_settings

settings = get_settings()
DATABASE_URL = settings.database_url

engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False}
    if DATABASE_URL.startswith("sqlite")
    else {},
)


def get_session():
    with Session(engine) as session:
        yield session
