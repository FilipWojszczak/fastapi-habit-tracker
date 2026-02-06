from fastapi import FastAPI

from .routers import ai, auth, habit_logs, habits

app = FastAPI(title="FastAPI Habit Tracker", version="0.1.0")

app.include_router(ai.router)
app.include_router(auth.router)
app.include_router(habits.router)
app.include_router(habit_logs.router)
