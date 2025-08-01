# import pytest
# from unittest.mock import patch, AsyncMock
# from fastapi.testclient import TestClient
# from httpx import AsyncClient
# from app.main import app

# @pytest.fixture
# async def client():
#     from fastapi import FastAPI
#     from httpx import AsyncClient
#     from app.main import app

#     async with AsyncClient(app=app, base_url="http://testserver") as ac:
#         yield ac

# @patch("app.middlewares.auth.verify_clerk_token", return_value={"sub": "user123"})
# @patch("app.guesses.service.get_similarity_score", return_value=1000)
# @patch("app.shared.http.call_internal_service")
# @patch("app.guesses.model.add_guess", new_callable=AsyncMock)
# @pytest.mark.asyncio
# async def test_guess_song(
#     mock_add_guess,
#     mock_call_internal,
#     mock_similarity,
#     mock_verify_token,
#     client
# ):
#     # Handle all 3 internal service calls
#     def side_effect(service_url, *args, **kwargs):
#         if service_url == "/users":
#             return {
#                 "user_id": "user123",
#                 "is_subscribed": False,
#                 "guesses": {}
#             }
#         elif service_url == "/songs/daily":
#             return {
#                 "id": "song123",
#                 "title": "Bohemian Rhapsody"
#             }
#         elif service_url == "/users" and args[0] == "PUT":
#             return {"status": "ok"}

#     mock_call_internal.side_effect = side_effect

#     response = await client.post(
#         "/guesses",
#         json={ "guess": "Bohemian Rhapsody" },
#         headers={ "authorization": "Bearer fake_token" }
#     )

#     assert response.status_code == 200
#     data = response.json()
#     assert data["is_correct"] is True
#     assert data["score"] == 1000
#     assert data["guesses_left"] == 4


# @patch("app.middlewares.auth.verify_clerk_token", return_value={"sub": "user123"})
# @patch("app.guesses.model.get_guesses", new_callable=AsyncMock)
# @patch("app.shared.http.call_internal_service", return_value={"user_id": "user123"})
# @pytest.mark.asyncio
# async def test_guess_history(mock_user_call, mock_get_guesses, mock_verify_token, client):
#     mock_get_guesses.return_value = [
#         {
#             "guess": "Let it be",
#             "is_correct": False,
#             "score": 700,
#             "guesses_left": 2
#         }
#     ]

#     response = await client.get(
#         "/guesses/history",
#         headers={ "authorization": "Bearer fake_token" }
#     )

#     assert response.status_code == 200
#     assert isinstance(response.json(), list)
#     assert response.json()[0]["guess"] == "Let it be"

