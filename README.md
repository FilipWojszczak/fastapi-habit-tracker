# FastAPI Habit Tracker

A comprehensive REST API for tracking habits, built with modern Python tools. This application allows users to create habits, log their progress, and view statistics such as current and longest streaks.

## Features

* **User Authentication**: Secure registration and login using JWT (JSON Web Tokens).
* **Habit Management**: Create, read, update, and delete habits.
* **Progress Tracking**: Log daily habit completions and filter logs by date.
* **Statistics**:
    * Calculate current and longest streaks.
    * Track total logs and unique days of activity.
* **Modern Stack**: Built with FastAPI, SQLModel (SQLAlchemy) and Pydantic.
* **Containerized**: Easy setup with Docker and Docker Compose.

## Tech Stack

* **Language**: Python 3.14+
* **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
* **Database**: PostgreSQL 17
* **ORM**: SQLModel / SQLAlchemy
* **Migrations**: Alembic
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
│   ├── main.py             # App entry point
│   ├── models/             # Database models
│   ├── routers/            # API endpoints (Auth, Habits, Logs)
│   ├── schemas/            # Pydantic schemas (Request/Response)
│   └── utils/              # Helper functions (Stats, Security)
└── tests/                  # Test suite
```

## Getting Started
