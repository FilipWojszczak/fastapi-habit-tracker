from contextlib import asynccontextmanager
from fastapi import FastAPI

from .db import init_db
from .routers import auth, habits, habit_logs


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)

app.include_router(auth.router)
app.include_router(habits.router)
app.include_router(habit_logs.router)
