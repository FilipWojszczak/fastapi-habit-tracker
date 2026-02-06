from unittest.mock import patch

from fastapi.testclient import TestClient
from tests.conftest import TokenFactory, UserFactory

from fastapi_habit_tracker.ai.extractor import HabitLogData


def test_log_habit_with_ai_mocked(
    client: TestClient, user_factory: UserFactory, token_factory: TokenFactory
):
    # Create a user and obtain a token
    user = user_factory("alice@example.com")
    token = token_factory(user)

    # Create a few habits for the user
    response = client.post(
        "/habits/",
        json={"name": "Running", "description": "Go for a run", "period": "daily"},
        headers={"Authorization": f"Bearer {token}"},
    )
    habit_id = response.json()["id"]
    client.post(
        "/habits/",
        json={"name": "Reading", "description": "Read a book", "period": "daily"},
        headers={"Authorization": f"Bearer {token}"},
    )
    client.post(
        "/habits/",
        json={
            "name": "Meditation",
            "description": "Meditate for 10 minutes",
            "period": "daily",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    # Prepare fake response from AI
    fake_ai_response = HabitLogData(
        habit_name="Running",
        value=30,
        note="Training from mock",
    )

    # Make a patch on the function that calls the AI, so that instead of calling the
    # real AI, it returns our fake response
    with patch("fastapi_habit_tracker.routers.ai.extract_habit_data") as mock_ai:
        mock_ai.return_value = fake_ai_response

        # Call the endpoint
        response = client.post(
            "/ai/log/",
            json={"text": "I ran for 30 minutes."},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["habit_id"] == habit_id
    assert data["value"] == 30
    assert data["note"] == "Training from mock"

    # Ensure that our mock was called exactly once
    mock_ai.assert_called_once()

    # Check that the log was added to db and associated with the correct habit
    response = client.get(
        "/habits/?include_stats=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    habits = response.json()
    assert response.status_code == 200
    habit_list = {habit["id"]: habit for habit in habits}
    assert len(habit_list) == 3
    assert habit_list[habit_id]["stats"]["total_logs"] == 1
