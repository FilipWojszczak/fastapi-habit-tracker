from sqlmodel import SQLModel, create_engine, Session

from . import models

DATABASE_URL = "sqlite:///./habit_tracker.db"

engine = create_engine(DATABASE_URL, echo=True)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
