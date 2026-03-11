# FastAPI Habit Tracker

![CI Status](https://github.com/FilipWojszczak/fastapi-habit-tracker/actions/workflows/fastapi-habit-tracker-ci.yml/badge.svg)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)

A comprehensive REST API for tracking habits, built with modern Python tools. This application allows users to create habits, log their progress, view statistics, and interact with intelligent AI agents for seamless habit management.

## Features

* **User Authentication**: Secure registration and login using JWT (JSON Web Tokens).
* **Habit Management**: Create, read, update, and delete habits.
* **Progress Tracking**: Log daily habit completions and filter logs by date.
* **Statistics**:
    * Calculate current and longest streaks.
    * Track total logs and unique days of activity.
* **AI Assistants**: Chat-based interface powered by LLMs for advanced habit management.
* **Smart Logging**: AI agent that analyzes natural language text to match and automatically log habit progress.
* **Interactive Data Retrieval**: Info agent capable of proposing SQL queries to return user statistics directly via chat.
* **Modern Stack**: Built with FastAPI, SQLModel (SQLAlchemy) and Pydantic.
* **Containerized**: Easy setup with Docker and Docker Compose.

## Tech Stack

* **Language**: Python 3.14
* **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
* **Database**: PostgreSQL 17
* **ORM**: SQLModel / SQLAlchemy
* **Migrations**: Alembic
* **AI & LLM Integration**: LangChain, LangGraph
* **Model Providers**: Google GenAI, Ollama
* **AI Persistence**: LangGraph Checkpoint Postgres
* **Dependency Management**: [uv](https://docs.astral.sh/uv/)
* **Testing**: Pytest

## Project Structure

```text
.
├── docker-compose.yml      # Docker services (App & DB)
├── docker-compose.test.yml # Docker services for testing (isolated DB)
├── pyproject.toml          # Dependencies and project metadata
├── alembic/                # Database migrations
├── fastapi_habit_tracker/  # Source code
│   ├── ai/                 # AI agents logic (Logging Agent, Info Agent)
│   ├── main.py             # App entry point
│   ├── dependencies/       # Reusable dependencies (e.g. Auth)
│   ├── models/             # Database models
│   ├── routers/            # API endpoints (Auth, Habits, Logs, AI)
│   ├── schemas/            # Pydantic schemas (Request/Response)
│   └── utils/              # Helper functions (Stats, Security)
└── tests/                  # Test suite
```

## Getting Started

### Prerequisites

* [Docker](https://www.docker.com/) and Docker Compose
* (Optional) Python installed locally if running without Docker

### Installation & Running (Docker)

The easiest way to run the application is using Docker Compose.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/FilipWojszczak/fastapi-habit-tracker.git
    cd fastapi-habit-tracker
    ```

2.  **Environment Configuration:**
    Create a `.env` file based on the example.
    ```bash
    cp .env.example .env
    ```
    *Note: Ensure correct values for variables in `.env`.*

3.  **Build and Run:**
    ```bash
    docker compose up --build
    ```

The API will be available at `http://localhost:8000`.

### Database Migrations

The application uses Alembic for database migrations. When running with Docker, migrations should be applied automatically. In case of some problems, run them manually:

```bash
docker compose exec app uv run alembic upgrade head
```

## API Documentation

Once the application is running, you can access the interactive API documentation provided by FastAPI:

* **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Development

If you want to run the project locally without Docker:

1.  **Install dependencies**:
    This project uses `uv` for fast dependency management.
    ```bash
    uv sync
    ```

2.  **Database Setup**:
    Set up a local PostgreSQL database and update your `.env` file with the correct credentials.

3.  **Run the server**:
    ```bash
    uv run uvicorn fastapi_habit_tracker.main:app --reload
    ```

## Testing

This project uses a dedicated `docker-compose.test.yml` file to run tests in an isolated environment with a separate database.

To run the test suite using Docker:

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

Or locally, with uv (requires local test DB setup):

```bash
uv run pytest
```
