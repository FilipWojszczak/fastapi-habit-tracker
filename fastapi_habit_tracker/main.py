from fastapi import FastAPI
from .routers import auth, habits, habit_logs

app = FastAPI()

app.include_router(auth.router)
app.include_router(habits.router)
app.include_router(habit_logs.router)
