from fastapi.testclient import TestClient

from fastapi_habit_tracker.models import User
from fastapi_habit_tracker.utils.security import create_access_token


def test_habit_crud(client: TestClient, user: User):
    # Create a new habit
    response = client.post(
        "/habits/",
        json={
            "name": "Exercise",
            "description": "Daily morning exercise",
            "period": "daily",
        },
        headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
    )
    data = response.json()
    assert response.status_code == 201
    assert data["name"] == "Exercise"
    assert data["description"] == "Daily morning exercise"
    assert data["period"] == "daily"
    habit_id = data["id"]

    # Retrieve the created habit
    response = client.get(
        f"/habits/{habit_id}",
        headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
    )
    data = response.json()
    assert response.status_code == 200
    assert data["id"] == habit_id
    assert data["name"] == "Exercise"
    assert data["description"] == "Daily morning exercise"
    assert data["period"] == "daily"
    assert "created_at" in data
    assert "updated_at" in data

    # List all habits
    response = client.get(
        "/habits/",
        headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
    )
    data = response.json()
    assert response.status_code == 200
    assert any(habit["id"] == habit_id for habit in data)

    # Update the habit
    response = client.put(
        f"/habits/{habit_id}",
        json={"name": "Exercise Updated", "description": "Updated description"},
        headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
    )
    data = response.json()
    assert response.status_code == 200
    assert data["name"] == "Exercise Updated"
    assert data["description"] == "Updated description"
    assert data["created_at"] != data["updated_at"]

    # Delete the habit
    response = client.delete(
        f"/habits/{habit_id}",
        headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
    )
    assert response.status_code == 204
