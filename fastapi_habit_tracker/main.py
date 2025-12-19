from contextlib import asynccontextmanager

from fastapi import FastAPI

from .db import init_db
from .routers import auth, habit_logs, habits


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="FastAPI Habit Tracker", version="0.1.0", lifespan=lifespan)

app.include_router(auth.router)
app.include_router(habits.router)
app.include_router(habit_logs.router)
