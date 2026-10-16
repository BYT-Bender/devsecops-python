"""
Comprehensive Pytest suite for the TaskBoard FastAPI backend.
Covers ≥ 10 test cases across ≥ 5 distinct endpoints:
  /health, /ready, /api/tasks, /api/tasks/{task_id}, /api/tasks/stats
All tests use an isolated SQLite in-memory database via conftest.py fixtures.
"""
import pytest


# ---------------------------------------------------------------------------
# Health & Readiness endpoints
# ---------------------------------------------------------------------------

def test_health_check(client):
    """GET /health → 200 with {'status': 'UP'}"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "UP"}


def test_ready_check(client):
    """GET /ready → 200 with {'status': 'READY'}"""
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "READY"}


# ---------------------------------------------------------------------------
# Task creation  (POST /api/tasks)
# ---------------------------------------------------------------------------

def test_create_task(client):
    """POST /api/tasks with valid payload → 201 and returns created task."""
    payload = {
        "title": "Configure EKS Ingress",
        "description": "Set up NGINX Ingress Controller with NLB annotations",
        "priority": "HIGH",
        "assignee": "DevOps Engineer",
        "status": "TODO",
    }
    response = client.post("/api/tasks", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["priority"] == "HIGH"
    assert data["status"] == "TODO"
    assert "id" in data
    assert "created_at" in data


def test_create_task_invalid_missing_title(client):
    """POST /api/tasks with missing required title → 422 Validation Error."""
    response = client.post("/api/tasks", json={"description": "No title"})
    assert response.status_code == 422


def test_create_task_invalid_bad_priority(client):
    """POST /api/tasks with invalid priority value → 422 Validation Error."""
    response = client.post(
        "/api/tasks",
        json={"title": "Bad task", "priority": "URGENT"},  # not in Literal
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Task listing  (GET /api/tasks)
# ---------------------------------------------------------------------------

def test_list_tasks(client):
    """GET /api/tasks → 200 and returns a list."""
    # Create a task first
    client.post("/api/tasks", json={"title": "List test task", "priority": "LOW"})

    response = client.get("/api/tasks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Verify list item structure
    assert "id" in data[0]
    assert "title" in data[0]
    assert "status" in data[0]


# ---------------------------------------------------------------------------
# Get single task  (GET /api/tasks/{task_id})
# ---------------------------------------------------------------------------

def test_get_task_by_id(client):
    """GET /api/tasks/{task_id} → 200 with exact task data."""
    created = client.post(
        "/api/tasks",
        json={"title": "Get by ID task", "description": "Test retrieval", "priority": "MEDIUM"},
    ).json()
    task_id = created["id"]

    response = client.get(f"/api/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Get by ID task"


def test_get_task_not_found(client):
    """GET /api/tasks/9999 → 404 with detail 'Task not found'."""
    response = client.get("/api/tasks/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# ---------------------------------------------------------------------------
# Update task  (PUT /api/tasks/{task_id})
# ---------------------------------------------------------------------------

def test_update_task_status(client):
    """PUT /api/tasks/{task_id} updating status → 200 with updated task."""
    created = client.post(
        "/api/tasks",
        json={"title": "Update me", "priority": "HIGH"},
    ).json()
    task_id = created["id"]

    response = client.put(f"/api/tasks/{task_id}", json={"status": "IN_PROGRESS"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["id"] == task_id


# ---------------------------------------------------------------------------
# Delete task  (DELETE /api/tasks/{task_id})
# ---------------------------------------------------------------------------

def test_delete_task(client):
    """DELETE /api/tasks/{task_id} → 204; subsequent GET returns 404."""
    created = client.post(
        "/api/tasks",
        json={"title": "Delete me", "priority": "LOW"},
    ).json()
    task_id = created["id"]

    delete_response = client.delete(f"/api/tasks/{task_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/tasks/{task_id}")
    assert get_response.status_code == 404


# ---------------------------------------------------------------------------
# Task statistics  (GET /api/tasks/stats)
# ---------------------------------------------------------------------------

def test_task_stats(client):
    """GET /api/tasks/stats → 200 with aggregated StatsOut."""
    # Create tasks in different states
    client.post("/api/tasks", json={"title": "Stats task TODO", "status": "TODO"})
    client.post("/api/tasks", json={"title": "Stats task IN_PROGRESS", "status": "IN_PROGRESS"})
    client.post("/api/tasks", json={"title": "Stats task DONE", "status": "DONE"})

    response = client.get("/api/tasks/stats")
    assert response.status_code == 200
    data = response.json()

    # Verify all required fields are present
    assert "total" in data
    assert "todo" in data
    assert "inProgress" in data
    assert "done" in data

    # Values should be non-negative integers
    assert data["total"] >= 0
    assert data["todo"] >= 0
    assert data["inProgress"] >= 0
    assert data["done"] >= 0
