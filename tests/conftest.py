from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine

from fastapi_habit_tracker.config import get_settings
from fastapi_habit_tracker.db import get_session
from fastapi_habit_tracker.main import app
from fastapi_habit_tracker.models import Habit, HabitLog, User  # noqa: F401
from fastapi_habit_tracker.utils.security import create_access_token, hash_password


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session]:
    database_url = get_settings().database_url
    if "postgres" in database_url:
        engine = create_engine(database_url)
    else:
        raise ValueError("database_url must be set to a PostgreSQL database for tests.")
    SQLModel.metadata.create_all(engine)

    connection = engine.connect()
    transaction = connection.begin()

    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient]:
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="user")
def user_fixture(session: Session) -> User:
    email = "john.smith@example.com"
    password = "securepassword"
    hashed_password = hash_password(password)
    user = User(email=email, hashed_password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture(name="token")
def token_fixture(user: User) -> str:
    return create_access_token(user.id)
