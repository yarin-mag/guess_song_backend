# tests/songs/test_routes.py

import pytest
from httpx import AsyncClient
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        yield ac

@pytest.mark.asyncio
async def test_get_daily_song(client):
    response = await client.get("/songs/daily")
    assert response.status_code == 200
    assert "id" in response.json()
    assert "title" in response.json()
