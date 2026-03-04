from psycopg_pool import AsyncConnectionPool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from . import models  # noqa: F401
from .config import get_settings

database_url = get_settings().database_url

engine = create_async_engine(
    database_url,
    echo=True,
    connect_args={"check_same_thread": False}
    if database_url.startswith("sqlite")
    else {},
)

_langgraph_pool: AsyncConnectionPool | None = None


async def get_session():
    async with AsyncSession(engine) as session:
        yield session


async def init_langgraph_pool() -> AsyncConnectionPool:
    global _langgraph_pool

    db_url = database_url.replace("postgresql+psycopg://", "postgresql://")

    _langgraph_pool = AsyncConnectionPool(
        conninfo=db_url,
        max_size=20,
        kwargs={"autocommit": True},
        open=False,
    )
    await _langgraph_pool.open()
    return _langgraph_pool


async def close_langgraph_pool():
    global _langgraph_pool
    if _langgraph_pool:
        await _langgraph_pool.close()
        _langgraph_pool = None


def get_langgraph_pool() -> AsyncConnectionPool:
    if _langgraph_pool is None:
        raise RuntimeError("LangGraph pool is not initialized. Check lifespan.")
    return _langgraph_pool
