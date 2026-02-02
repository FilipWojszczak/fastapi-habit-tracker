from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from tests.conftest import TokenFactory, UserFactory
from tests.utils import dt_with_tzinfo_from_isoformat


def test_habit_crud(
    client: TestClient, user_factory: UserFactory, token_factory: TokenFactory
):
    # Create a user and obtain a token
    user = user_factory("alice@example.com")
    token = token_factory(user)

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


def test_habit_stats(
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
    last_performed_at = dt_with_tzinfo_from_isoformat(stats_data["last_performed_at"])
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
    last_performed_at = dt_with_tzinfo_from_isoformat(stats_data["last_performed_at"])
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
    last_performed_at = dt_with_tzinfo_from_isoformat(stats_data["last_performed_at"])
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
    last_performed_at = dt_with_tzinfo_from_isoformat(stats_data["last_performed_at"])
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
    last_performed_at = dt_with_tzinfo_from_isoformat(stats_data["last_performed_at"])
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
    last_performed_at = dt_with_tzinfo_from_isoformat(stats_data["last_performed_at"])
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
    last_performed_at = dt_with_tzinfo_from_isoformat(stats_data["last_performed_at"])
    assert last_performed_at == today - timedelta(days=7)
    assert stats_data["unique_days"] == 3
    assert stats_data["longest_streak_days"] == 2
    assert (
        stats_data["current_streak_days"]
        == "The provided date range does not include today or yesterday."
    )


def test_habit_list(
    client: TestClient, user_factory: UserFactory, token_factory: TokenFactory
):
    # Create a user and obtain a token
    user = user_factory("alice@example.com")
    token = token_factory(user)

    # Create two habits
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

    response = client.post(
        "/habits/",
        json={
            "name": "Walk",
            "description": "Walk for 1 hour",
            "period": "daily",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    habit2_data = response.json()
    habit2_id = habit2_data["id"]

    # Create new habit logs
    two_days_ago = datetime.now(UTC) - timedelta(days=2)
    yesterday = datetime.now(UTC) - timedelta(days=1)
    today = datetime.now(UTC)

    client.post(
        "/habit-logs/",
        json={"habit_id": habit_id, "performed_at": two_days_ago.isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )

    client.post(
        "/habit-logs/",
        json={"habit_id": habit_id, "performed_at": yesterday.isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )

    client.post(
        "/habit-logs/",
        json={"habit_id": habit_id, "performed_at": yesterday.isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )

    client.post(
        "/habit-logs/",
        json={"habit_id": habit_id, "performed_at": today.isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )

    three_days_ago = datetime.now(UTC) - timedelta(days=3)
    four_days_ago = datetime.now(UTC) - timedelta(days=4)

    client.post(
        "/habit-logs/",
        json={"habit_id": habit2_id, "performed_at": three_days_ago.isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )

    client.post(
        "/habit-logs/",
        json={"habit_id": habit2_id, "performed_at": four_days_ago.isoformat()},
        headers={"Authorization": f"Bearer {token}"},
    )

    # List all habits without stats
    response = client.get(
        "/habits/",
        headers={"Authorization": f"Bearer {token}"},
    )
    habits = response.json()
    assert response.status_code == 200
    habit_list = {habit["id"]: habit for habit in habits}
    assert len(habit_list) == 2
    assert habit_id in habit_list
    assert habit2_id in habit_list
    assert habit_list[habit_id]["stats"] is None
    assert habit_list[habit2_id]["stats"] is None

    # List all habits with stats
    response = client.get(
        "/habits/?include_stats=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    habits = response.json()
    assert response.status_code == 200
    habit_list = {habit["id"]: habit for habit in habits}
    assert len(habit_list) == 2
    assert habit_id in habit_list
    assert habit2_id in habit_list
    assert habit_list[habit_id]["stats"]["total_logs"] == 4
    assert habit_list[habit_id]["stats"]["current_streak_days"] == 3
    assert habit_list[habit2_id]["stats"]["total_logs"] == 2
    assert habit_list[habit2_id]["stats"]["current_streak_days"] == 0


def test_habit_logs(
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
    habit_logs_responses = []
    today = datetime.now(UTC)

    for offset in range(10):
        log_date = today - timedelta(days=offset)

        response = client.post(
            "/habit-logs/",
            json={
                "habit_id": habit_id,
                "performed_at": log_date.isoformat(),
                "note": f"Note {offset}",
                "value": offset * 10,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        habit_logs_responses.append(response.json())

    # List all habit logs
    response = client.get(
        f"/habits/{habit_id}/logs/",
        headers={"Authorization": f"Bearer {token}"},
    )
    logs = response.json()
    assert response.status_code == 200
    assert len(logs) == 10
    for i in range(10):
        assert logs[i]["id"] == habit_logs_responses[i]["id"]
        assert logs[i]["habit_id"] == habit_logs_responses[i]["habit_id"]
        assert logs[i]["note"] == habit_logs_responses[i]["note"]
        assert logs[i]["value"] == habit_logs_responses[i]["value"]
        assert logs[i]["performed_at"] == habit_logs_responses[i]["performed_at"]

    # List habit logs with 'since' filter
    since = (today - timedelta(days=5)).date()
    response = client.get(
        f"/habits/{habit_id}/logs/?since={since}",
        headers={"Authorization": f"Bearer {token}"},
    )
    logs = response.json()
    assert response.status_code == 200
    assert len(logs) == 6
    for i in range(6):
        assert logs[i]["id"] == habit_logs_responses[i]["id"]
        assert logs[i]["habit_id"] == habit_logs_responses[i]["habit_id"]
        assert logs[i]["note"] == habit_logs_responses[i]["note"]
        assert logs[i]["value"] == habit_logs_responses[i]["value"]
        assert logs[i]["performed_at"] == habit_logs_responses[i]["performed_at"]

    # List habit logs with 'to' filter
    to = (today - timedelta(days=7)).date()
    response = client.get(
        f"/habits/{habit_id}/logs/?to={to}",
        headers={"Authorization": f"Bearer {token}"},
    )
    logs = response.json()
    assert response.status_code == 200
    assert len(logs) == 3
    for i, j in zip(range(0, 3), range(7, 10), strict=False):
        assert logs[i]["id"] == habit_logs_responses[j]["id"]
        assert logs[i]["habit_id"] == habit_logs_responses[j]["habit_id"]
        assert logs[i]["note"] == habit_logs_responses[j]["note"]
        assert logs[i]["value"] == habit_logs_responses[j]["value"]
        assert logs[i]["performed_at"] == habit_logs_responses[j]["performed_at"]

    # List habit logs with 'limit' filter
    limit = 4
    response = client.get(
        f"/habits/{habit_id}/logs/?limit={limit}",
        headers={"Authorization": f"Bearer {token}"},
    )
    logs = response.json()
    assert response.status_code == 200
    assert len(logs) == 4
    for i in range(4):
        assert logs[i]["id"] == habit_logs_responses[i]["id"]
        assert logs[i]["habit_id"] == habit_logs_responses[i]["habit_id"]
        assert logs[i]["note"] == habit_logs_responses[i]["note"]
        assert logs[i]["value"] == habit_logs_responses[i]["value"]
        assert logs[i]["performed_at"] == habit_logs_responses[i]["performed_at"]

    # List habit logs with 'since', 'to' and 'limit' filters
    since = (today - timedelta(days=8)).date()
    to = (today - timedelta(days=2)).date()
    limit = 3
    response = client.get(
        f"/habits/{habit_id}/logs/?limit={limit}&since={since}&to={to}",
        headers={"Authorization": f"Bearer {token}"},
    )
    logs = response.json()
    assert response.status_code == 200
    assert len(logs) == 3
    for i, j in zip(range(0, 3), range(2, 5), strict=False):
        assert logs[i]["id"] == habit_logs_responses[j]["id"]
        assert logs[i]["habit_id"] == habit_logs_responses[j]["habit_id"]
        assert logs[i]["note"] == habit_logs_responses[j]["note"]
        assert logs[i]["value"] == habit_logs_responses[j]["value"]
        assert logs[i]["performed_at"] == habit_logs_responses[j]["performed_at"]
