FROM python:3.14
WORKDIR /app
COPY . .
RUN pip install uv
RUN uv sync --frozen
CMD uv run uvicorn --host 0.0.0.0 --port 8000 fastapi_habit_tracker.main:app