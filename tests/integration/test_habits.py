from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient


def test_habit_crud(client: TestClient, token: str):
    # Create a new habit
    response = client.post(
        "/habits/",
        json={
            "name": "Exercise",
            "description": "Daily morning exercise",
            "period": "daily",
        },
        headers={"Authorization": f"Bearer {token}"},
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
        headers={"Authorization": f"Bearer {token}"},
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
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    assert response.status_code == 200
    assert any(habit["id"] == habit_id for habit in data)

    # Update the habit
    response = client.put(
        f"/habits/{habit_id}",
        json={"name": "Exercise Updated", "description": "Updated description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    data = response.json()
    assert response.status_code == 200
    assert data["name"] == "Exercise Updated"
    assert data["description"] == "Updated description"
    assert data["created_at"] != data["updated_at"]

    # Delete the habit
    response = client.delete(
        f"/habits/{habit_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


def test_habit_stats(client: TestClient, token: str):
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

    # Create habit log in the past (not yesterday)
    past_date = datetime.now(UTC) - timedelta(days=5)
    response = client.post(
        "/habit-logs/",
        json={"habit_id": habit_id, "performed_at": past_date.isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    # Retrieve habit's stats
    response = client.get(
        f"/habits/{habit_id}/stats/",
        headers={"Authorization": f"Bearer {token}"},
    )
    stats_data = response.json()
    assert response.status_code == 200
    assert stats_data["total_logs"] == 1
    last_performed_at = datetime.fromisoformat(stats_data["last_performed_at"])
    if last_performed_at.tzinfo is None:
        last_performed_at = last_performed_at.replace(tzinfo=UTC)
    assert last_performed_at == past_date
    assert stats_data["unique_days"] == 1
    assert stats_data["longest_streak_days"] == 1
    assert stats_data["current_streak_days"] == 0

    # Create habit log with performed_at as yesterday
    yesterday = datetime.now(UTC) - timedelta(days=1)
    response = client.post(
        "/habit-logs/",
        json={"habit_id": habit_id, "performed_at": yesterday.isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    # Retrieve habit's stats
    response = client.get(
        f"/habits/{habit_id}/stats/",
        headers={"Authorization": f"Bearer {token}"},
    )
    stats_data = response.json()
    assert response.status_code == 200
    assert stats_data["total_logs"] == 2
    last_performed_at = datetime.fromisoformat(stats_data["last_performed_at"])
    if last_performed_at.tzinfo is None:
        last_performed_at = last_performed_at.replace(tzinfo=UTC)
    assert last_performed_at == yesterday
    assert stats_data["unique_days"] == 2
    assert stats_data["longest_streak_days"] == 1
    assert stats_data["current_streak_days"] == 1

    # Create more habit logs (1 today and a few in the past, but not yesterday)
    today = datetime.now(UTC)
    response = client.post(
        "/habit-logs/",
        json={"habit_id": habit_id, "performed_at": today.isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    days_offsets = [4, 6, 7, 10, 11]
    for offset in days_offsets:
        log_date = today - timedelta(days=offset)

        response = client.post(
            "/habit-logs/",
            json={"habit_id": habit_id, "performed_at": log_date.isoformat()},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201

    # Retrieve habit's stats
    response = client.get(
        f"/habits/{habit_id}/stats/",
        headers={"Authorization": f"Bearer {token}"},
    )
    stats_data = response.json()
    assert response.status_code == 200
    assert stats_data["total_logs"] == 8
    last_performed_at = datetime.fromisoformat(stats_data["last_performed_at"])
    if last_performed_at.tzinfo is None:
        last_performed_at = last_performed_at.replace(tzinfo=UTC)
    assert last_performed_at == today
    assert stats_data["unique_days"] == 8
    assert stats_data["longest_streak_days"] == 4
    assert stats_data["current_streak_days"] == 2

    # Create habit logs in a days that already has a log (today and day in the past, but
    # not yesterday)
    duplicate_log_date = datetime.now(UTC) - timedelta(days=4)
    response = client.post(
        "/habit-logs/",
        json={"habit_id": habit_id, "performed_at": duplicate_log_date.isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    newer_today = datetime.now(UTC)
    response = client.post(
        "/habit-logs/",
        json={"habit_id": habit_id, "performed_at": newer_today.isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    # Retrieve habit's stats
    response = client.get(
        f"/habits/{habit_id}/stats/",
        headers={"Authorization": f"Bearer {token}"},
    )
    stats_data = response.json()
    assert response.status_code == 200
    assert stats_data["total_logs"] == 10
    last_performed_at = datetime.fromisoformat(stats_data["last_performed_at"])
    if last_performed_at.tzinfo is None:
        last_performed_at = last_performed_at.replace(tzinfo=UTC)
    assert last_performed_at == newer_today
    assert stats_data["unique_days"] == 8
    assert stats_data["longest_streak_days"] == 4
    assert stats_data["current_streak_days"] == 2

    # Retrieve habit's stats with 'since' and 'to' filters
    since_date = (datetime.now(UTC) - timedelta(days=6)).date()
    to_date = (datetime.now(UTC) - timedelta(days=1)).date()
    response = client.get(
        f"/habits/{habit_id}/stats/?since={since_date.isoformat()}&to={to_date.isoformat()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    stats_data = response.json()
    assert response.status_code == 200
    assert stats_data["total_logs"] == 5
    last_performed_at = datetime.fromisoformat(stats_data["last_performed_at"])
    if last_performed_at.tzinfo is None:
        last_performed_at = last_performed_at.replace(tzinfo=UTC)
    assert last_performed_at == yesterday
    assert stats_data["unique_days"] == 4
    assert stats_data["longest_streak_days"] == 3
    assert stats_data["current_streak_days"] == 1

    # Retrieve habit's stats with only 'since' filter
    since_date = (datetime.now(UTC) - timedelta(days=4)).date()
    response = client.get(
        f"/habits/{habit_id}/stats/?since={since_date.isoformat()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    stats_data = response.json()
    assert response.status_code == 200
    assert stats_data["total_logs"] == 5
    last_performed_at = datetime.fromisoformat(stats_data["last_performed_at"])
    if last_performed_at.tzinfo is None:
        last_performed_at = last_performed_at.replace(tzinfo=UTC)
    assert last_performed_at == newer_today
    assert stats_data["unique_days"] == 3
    assert stats_data["longest_streak_days"] == 2
    assert stats_data["current_streak_days"] == 2

    # Retrieve habit's stats with only 'to' filter
    to_date = (datetime.now(UTC) - timedelta(days=7)).date()
    response = client.get(
        f"/habits/{habit_id}/stats/?to={to_date.isoformat()}",
        headers={"Authorization": f"Bearer {token}"},
    )
    stats_data = response.json()
    assert response.status_code == 200
    assert stats_data["total_logs"] == 3
    last_performed_at = datetime.fromisoformat(stats_data["last_performed_at"])
    if last_performed_at.tzinfo is None:
        last_performed_at = last_performed_at.replace(tzinfo=UTC)
    assert last_performed_at == today - timedelta(days=7)
    assert stats_data["unique_days"] == 3
    assert stats_data["longest_streak_days"] == 2
    assert (
        stats_data["current_streak_days"]
        == "The provided date range does not include today or yesterday."
    )
