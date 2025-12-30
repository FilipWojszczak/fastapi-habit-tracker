import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from fastapi_habit_tracker.db import get_session
from fastapi_habit_tracker.main import app
from fastapi_habit_tracker.models import Habit, HabitLog, User  # noqa: F401
from fastapi_habit_tracker.utils.security import hash_password


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="user")
def user_fixture(session: Session):
    email = "john.smith@example.com"
    password = "securepassword"
    hashed_password = hash_password(password)
    user = User(email=email, hashed_password=hashed_password)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
