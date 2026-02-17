from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import close_langgraph_pool, init_langgraph_pool
from .routers import ai, auth, habit_logs, habits


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_langgraph_pool()
    yield
    close_langgraph_pool()


app = FastAPI(title="FastAPI Habit Tracker", version="0.1.0", lifespan=lifespan)


app.include_router(ai.router)
app.include_router(auth.router)
app.include_router(habits.router)
app.include_router(habit_logs.router)
