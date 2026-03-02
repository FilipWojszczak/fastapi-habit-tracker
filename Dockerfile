FROM python:3.14-slim AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR /app
COPY pyproject.toml uv.lock ./

FROM base AS local
RUN uv sync --frozen --no-dev
CMD ["uv", "run", "fastapi", "dev", "fastapi_habit_tracker/main.py", "--host", "0.0.0.0", "--port", "8000"]

FROM base as testing
RUN uv sync --frozen
COPY . .
CMD ["uv", "run", "pytest"]

FROM base as prod
RUN uv sync --frozen --no-dev
COPY . .
CMD ["uv", "run", "fastapi", "run", "fastapi_habit_tracker/main.py", "--host", "0.0.0.0", "--port", "8000"]
