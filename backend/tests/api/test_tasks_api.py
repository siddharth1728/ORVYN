"""Task REST API integration tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["app"] == "ORVYN"


@pytest.mark.asyncio
async def test_agents_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/agents")
        assert response.status_code == 200
        agents = response.json()
        assert len(agents) >= 1
        assert agents[0]["name"] == "ORVYN-Core"


@pytest.mark.asyncio
async def test_task_crud_lifecycle_api():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Create Task
        create_resp = await client.post(
            "/api/tasks",
            json={"title": "Backend Internship Search", "objective": "Find roles in Bangalore"},
        )
        assert create_resp.status_code == 201
        task_data = create_resp.json()
        task_id = task_data["id"]
        assert task_data["status"] == "CREATED"

        # 2. Get Task
        get_resp = await client.get(f"/api/tasks/{task_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == task_id

        # 3. List Tasks
        list_resp = await client.get("/api/tasks")
        assert list_resp.status_code == 200
        assert any(t["id"] == task_id for t in list_resp.json())

        # 4. Run Task (will pause awaiting relocation preference)
        run_resp = await client.post(f"/api/tasks/{task_id}/run")
        assert run_resp.status_code == 200
        run_data = run_resp.json()
        assert run_data["status"] == "AWAITING_RESPONSE"
        assert run_data["checkpoint_token"] is not None

        # 5. Inspect Checkpoints
        chk_resp = await client.get(f"/api/tasks/{task_id}/checkpoints")
        assert chk_resp.status_code == 200
        checkpoints = chk_resp.json()
        assert len(checkpoints) >= 1

        # 6. Resume Task with Human Decision
        resume_resp = await client.post(
            f"/api/tasks/{task_id}/resume",
            json={"decision": {"relocation": True}},
        )
        assert resume_resp.status_code == 200
        resume_data = resume_resp.json()
        assert resume_data["status"] == "COMPLETED"
