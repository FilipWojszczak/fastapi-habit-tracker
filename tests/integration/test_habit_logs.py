from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from tests.conftest import TokenFactory, UserFactory
from tests.utils import dt_with_tzinfo_from_isoformat


def test_habit_logs_crud(
    client: TestClient, user_factory: UserFactory, token_factory: TokenFactory
):
    # Create a user and obtain a token
    user = user_factory("alice@example.com")
    token = token_factory(user)

    # Create a new habit
    response = client.post(
        "/habits/",
        json={
            "name": "Read Books",
            "description": "Read for 30 minutes",
            "period": "daily",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    habit_data = response.json()
    habit_id = habit_data["id"]

    # Create new habit logs
    yesterday = datetime.now(UTC) - timedelta(days=1)

    response = client.post(
        "/habit-logs/",
        json={"habit_id": habit_id, "performed_at": yesterday.isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )
    log_data = response.json()
    assert response.status_code == 201
    assert log_data["habit_id"] == habit_id
    assert log_data["note"] is None
    assert log_data["value"] is None
    response_date = dt_with_tzinfo_from_isoformat(log_data["performed_at"])
    assert response_date == yesterday

    response = client.post(
        "/habit-logs/",
        json={"habit_id": habit_id, "note": "Example note", "value": 30},
        headers={"Authorization": f"Bearer {token}"},
    )
    log2_data = response.json()
    assert response.status_code == 201
    assert log2_data["habit_id"] == habit_id
    assert log2_data["note"] == "Example note"
    assert log2_data["value"] == 30
    assert "performed_at" in log2_data

    # List all habit logs
    response = client.get(
        f"/habits/{habit_id}/logs/",
        headers={"Authorization": f"Bearer {token}"},
    )
    logs = response.json()
    assert response.status_code == 200
    assert len(logs) == 2
    assert logs[0]["id"] == log2_data["id"]
    assert logs[0]["habit_id"] == log2_data["habit_id"]
    assert logs[0]["note"] == log2_data["note"]
    assert logs[0]["value"] == log2_data["value"]
    assert logs[0]["performed_at"] == log2_data["performed_at"]

    assert logs[1]["id"] == log_data["id"]
    assert logs[1]["habit_id"] == log_data["habit_id"]
    assert logs[1]["note"] == log_data["note"]
    assert logs[1]["value"] == log_data["value"]
    assert logs[1]["performed_at"] == log_data["performed_at"]

    # Update the habit log
    response = client.put(
        f"/habit-logs/{log_data['id']}",
        json={"note": "Updated note", "value": 15},
        headers={"Authorization": f"Bearer {token}"},
    )
    updated_log_data = response.json()
    assert response.status_code == 200
    assert updated_log_data["id"] == log_data["id"]
    assert updated_log_data["habit_id"] == habit_id
    assert updated_log_data["note"] == "Updated note"
    assert updated_log_data["value"] == 15
    assert updated_log_data["performed_at"] == log_data["performed_at"]

    # List habit logs after updating one of them with all possible params
    first_log_date = datetime.fromisoformat(log_data["performed_at"]).date()

    limit = 1
    since = first_log_date
    to = first_log_date

    response = client.get(
        f"/habits/{habit_id}/logs/?limit={limit}&since={since}&to={to}",
        headers={"Authorization": f"Bearer {token}"},
    )
    logs = response.json()
    assert response.status_code == 200
    assert len(logs) == 1

    assert logs[0]["id"] == updated_log_data["id"]
    assert logs[0]["habit_id"] == updated_log_data["habit_id"]
    assert logs[0]["note"] == updated_log_data["note"]
    assert logs[0]["value"] == updated_log_data["value"]
    assert logs[0]["performed_at"] == updated_log_data["performed_at"]

    # Delete updated habit log
    response = client.delete(
        f"/habit-logs/{updated_log_data['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204

    # List all habit logs after deletion
    response = client.get(
        f"/habits/{habit_id}/logs/",
        headers={"Authorization": f"Bearer {token}"},
    )
    logs = response.json()
    assert response.status_code == 200
    assert len(logs) == 1
    assert logs[0]["id"] == log2_data["id"]
    assert logs[0]["habit_id"] == log2_data["habit_id"]
    assert logs[0]["note"] == log2_data["note"]
    assert logs[0]["value"] == log2_data["value"]
    assert logs[0]["performed_at"] == log2_data["performed_at"]


def test_habit_logs_crud_as_not_authenticated(
    client: TestClient, user_factory: UserFactory, token_factory: TokenFactory
):
    # Create a user and obtain a token
    user = user_factory("alice@example.com")
    token = token_factory(user)

    # Create a new habit to have a valid habit_id
    response = client.post(
        "/habits/",
        json={
            "name": "Exercise",
            "description": "Workout for 1 hour",
            "period": "daily",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    habit_data = response.json()
    habit_id = habit_data["id"]

    # Create a new habit log without authentication
    response = client.post(
        "/habit-logs/",
        json={"habit_id": habit_id},
    )
    assert response.status_code == 401

    # Create a new habit log with authentication
    response = client.post(
        "/habit-logs/",
        json={"habit_id": habit_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    log_data = response.json()
    habit_log_id = log_data["id"]

    # Update a habit log without authentication
    response = client.put(
        f"/habit-logs/{habit_log_id}",
        json={"note": "Updated note"},
    )
    assert response.status_code == 401

    # Delete a habit log without authentication
    response = client.delete(f"/habit-logs/{habit_log_id}")
    assert response.status_code == 401


def test_create_habit_log_with_invalid_habit_id(
    client: TestClient, user_factory: UserFactory, token_factory: TokenFactory
):
    # Create a user and obtain a token
    user = user_factory("alice@example.com")
    token = token_factory(user)

    invalid_habit_id = 9999

    response = client.post(
        "/habit-logs/",
        json={"habit_id": invalid_habit_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Habit not found"


def test_not_existing_habit_log(
    client: TestClient, user_factory: UserFactory, token_factory: TokenFactory
):
    # Create a user and obtain a token
    user = user_factory("alice@example.com")
    token = token_factory(user)

    non_existent_habit_log_id = 9999

    # Attempt to update a non-existing habit log
    response = client.put(
        f"/habit-logs/{non_existent_habit_log_id}",
        json={"note": "Updated note"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Habit log not found"

    # Attempt to delete a non-existing habit log
    response = client.delete(
        f"/habit-logs/{non_existent_habit_log_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Habit log not found"


def test_habit_log_access_by_different_user(
    client: TestClient, user_factory: UserFactory, token_factory: TokenFactory
):
    # Create two users and obtain tokens
    user_1 = user_factory("alice@example.com")
    token_1 = token_factory(user_1)
    user_2 = user_factory("bob@example.com")
    token_2 = token_factory(user_2)

    # Create a new habit with the first user
    response = client.post(
        "/habits/",
        json={
            "name": "Meditate",
            "description": "Meditate for 15 minutes",
            "period": "daily",
        },
        headers={"Authorization": f"Bearer {token_1}"},
    )
    habit_data = response.json()
    habit_id = habit_data["id"]

    # Create a new habit log with the first user
    response = client.post(
        "/habit-logs/",
        json={"habit_id": habit_id},
        headers={"Authorization": f"Bearer {token_1}"},
    )
    log_data = response.json()
    habit_log_id = log_data["id"]

    # Attempt to update the habit log created by the first user with the second user's
    # token
    response = client.put(
        f"/habit-logs/{habit_log_id}",
        json={"note": "Trying to update"},
        headers={"Authorization": f"Bearer {token_2}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Habit log not found"

    # Attempt to delete the habit log created by the first user with the second user's
    # token
    response = client.delete(
        f"/habit-logs/{habit_log_id}",
        headers={"Authorization": f"Bearer {token_2}"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Habit log not found"
