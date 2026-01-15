import os

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine, select, text

from fastapi_habit_tracker.models import Habit, HabitLog, User

# Load variables from .env
load_dotenv()

POSTGRES_URL = os.getenv("DATABASE_URL")
SQLITE_URL = "sqlite:///./habit_tracker.db"


def migrate():
    if not POSTGRES_URL or "postgresql" not in POSTGRES_URL:
        print(
            "Error: DATABASE_URL in .env is not configured correctly with PostgreSQL!"
        )
        return

    print(f"--- Migration to db: {POSTGRES_URL.split('@')[-1]} ---")

    sqlite_engine = create_engine(SQLITE_URL)
    pg_engine = create_engine(POSTGRES_URL)

    # Creating tables
    print("Creating tables in PostgreSQL...")
    SQLModel.metadata.create_all(pg_engine)

    with Session(sqlite_engine) as src_session, Session(pg_engine) as dst_session:
        # Migration of User model
        users = src_session.exec(select(User)).all()
        for user in users:
            dst_session.add(User(**user.model_dump()))
        print(f"{len(users)} Users were migrated.")

        # Migration of Habit model
        habits = src_session.exec(select(Habit)).all()
        for habit in habits:
            dst_session.add(Habit(**habit.model_dump()))
        print(f"{len(habits)} Habits were migrated.")

        # Migration of HabitLog model
        logs = src_session.exec(select(HabitLog)).all()
        for log in logs:
            dst_session.add(HabitLog(**log.model_dump()))
        print(f"{len(logs)} HabitLogs were migrated.")

        dst_session.commit()

        # Fix of ID sequence for PostgreSQL
        models = [User, Habit, HabitLog]
        for model in models:
            table_name = model.__tablename__
            print(f"Fixing counter for table: {table_name}")

            try:
                query = (
                    f"SELECT setval(pg_get_serial_sequence('\"{table_name}\"', 'id'), "
                    f'coalesce(max(id), 0) + 1, false) FROM "{table_name}";'
                )
                dst_session.exec(text(query))
            except Exception as e:
                print(f"Error during processing table: {table_name}: {e}")
        dst_session.commit()

    print("--- Success! ---")


if __name__ == "__main__":
    migrate()
