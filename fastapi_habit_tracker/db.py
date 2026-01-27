from sqlmodel import Session, create_engine

from . import models  # noqa: F401
from .config import get_settings

database_url = get_settings().database_url

engine = create_engine(
    database_url,
    echo=True,
    connect_args={"check_same_thread": False}
    if database_url.startswith("sqlite")
    else {},
)


def get_session():
    with Session(engine) as session:
        yield session
