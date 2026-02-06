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
    assert data["habit_name"] == "Running"
    assert data["value"] == 30
    assert data["note"] == "Training from mock"

    # Ensure that our mock was called exactly once
    mock_ai.assert_called_once()
