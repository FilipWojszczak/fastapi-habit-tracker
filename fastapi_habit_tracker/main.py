from fastapi import FastAPI

app = FastAPI(title="Habit & Workout Tracker API")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
