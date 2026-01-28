from fastapi.testclient import TestClient

from fastapi_habit_tracker.models import User
from fastapi_habit_tracker.utils.security import create_access_token


def test_habit_logs_create_list(client: TestClient, user: User):
    # Create a new habit first
    response = client.post(
        "/habits/",
        json={
            "name": "Read Books",
            "description": "Read for 30 minutes",
            "period": "daily",
        },
        headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
    )
    habit_data = response.json()
    habit_id = habit_data["id"]

    # Create new habit logs
    response = client.post(
        "/habit-logs/",
        json={"habit_id": habit_id},
        headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
    )
    log_data = response.json()
    assert response.status_code == 201
    assert log_data["habit_id"] == habit_id
    assert log_data["note"] is None
    assert log_data["value"] is None
    assert "performed_at" in log_data

    response = client.post(
        "/habit-logs/",
        json={"habit_id": habit_id, "note": "Example note", "value": 30},
        headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
    )
    log2_data = response.json()
    assert response.status_code == 201
    assert log2_data["habit_id"] == habit_id
    assert log2_data["note"] == "Example note"
    assert log2_data["value"] == 30
    assert "performed_at" in log2_data

    # List habit logs
    response = client.get(
        f"/habits/{habit_id}/logs/?limit=1",
        headers={"Authorization": f"Bearer {create_access_token(user.id)}"},
    )
    logs = response.json()
    assert response.status_code == 200
    assert len(logs) == 1
    assert logs[0]["id"] == log2_data["id"]
    assert logs[0]["habit_id"] == log2_data["habit_id"]
    assert logs[0]["note"] == log2_data["note"]
    assert logs[0]["value"] == log2_data["value"]
    assert logs[0]["performed_at"] == log2_data["performed_at"]
