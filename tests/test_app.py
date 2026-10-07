"""
Unit and Integration Tests for ACEest Fitness & Gym Flask Application.
Validates service health, authentication, client CRUD, workout logging,
progress tracking, and AI routine recommendation logic.
"""

import os
import tempfile
import pytest
from app import create_app, init_db


@pytest.fixture
def app_instance():
    """Create a temporary SQLite database and test Flask application instance."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    app = create_app({
        "TESTING": True,
        "DATABASE": db_path,
        "SECRET_KEY": "test-secret-key"
    })

    with app.app_context():
        init_db(db_path)

    yield app

    os.close(db_fd)
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def client(app_instance):
    """Test client fixture."""
    return app_instance.test_client()


def test_index_endpoint(client):
    """Test root landing endpoint returns 200 and API service information."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.get_json()
    assert data["service"] == "ACEest Fitness & Gym Web Application"
    assert data["status"] == "operational"
    assert "endpoints" in data


def test_health_check(client):
    """Test health check probe endpoint returns UP status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "UP"
    assert "timestamp" in data


def test_login_success(client):
    """Test login authentication with valid admin credentials."""
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin"
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["username"] == "admin"
    assert data["role"] == "Admin"


def test_login_invalid_credentials(client):
    """Test login authentication with invalid password returns 401."""
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    data = response.get_json()
    assert data["status"] == "error"
    assert "Invalid credentials" in data["message"]


def test_login_missing_fields(client):
    """Test login endpoint with missing username/password returns 400."""
    response = client.post("/api/auth/login", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_client_crud_lifecycle(client):
    """Test adding, retrieving, and listing client profiles."""
    # List clients initially empty
    response = client.get("/api/clients")
    assert response.status_code == 200
    assert response.get_json() == []

    # Add a new client
    new_client = {
        "name": "Sarah Connor",
        "age": 29,
        "height": 168.0,
        "weight": 62.5,
        "program": "Fat Loss",
        "calories": 2100,
        "target_weight": 58.0,
        "target_adherence": 90,
        "membership_status": "Active",
        "membership_end": "2026-12-31"
    }
    post_res = client.post("/api/clients", json=new_client)
    assert post_res.status_code == 201
    assert "saved successfully" in post_res.get_json()["message"]

    # Retrieve specific client
    get_res = client.get("/api/clients/Sarah Connor")
    assert get_res.status_code == 200
    client_data = get_res.get_json()
    assert client_data["name"] == "Sarah Connor"
    assert client_data["calories"] == 2100
    assert client_data["membership_status"] == "Active"

    # List all clients
    list_res = client.get("/api/clients")
    assert list_res.status_code == 200
    assert len(list_res.get_json()) == 1


def test_add_client_validation(client):
    """Test adding client without name returns 400."""
    response = client.post("/api/clients", json={})
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_add_duplicate_client(client):
    """Test adding duplicate client returns 409 Conflict."""
    payload = {"name": "Arnold S."}
    res1 = client.post("/api/clients", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/clients", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.get_json()["error"]


def test_client_not_found(client):
    """Test retrieving non-existent client returns 404."""
    response = client.get("/api/clients/NonExistentPerson")
    assert response.status_code == 404
    assert "error" in response.get_json()


def test_generate_program_endpoint(client):
    """Test AI-style training program generator assigns valid workout routine."""
    client.post("/api/clients", json={"name": "Bruce Wayne"})
    response = client.post("/api/clients/Bruce Wayne/generate-program")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "success"
    assert data["client"] == "Bruce Wayne"
    assert "category" in data
    assert "program" in data

    # Verify updated client record
    client_record = client.get("/api/clients/Bruce Wayne").get_json()
    assert client_record["program"] == data["program"]


def test_membership_verification(client):
    """Test membership verification endpoint returns status and expiry."""
    client.post("/api/clients", json={
        "name": "Clark Kent",
        "membership_status": "Active",
        "membership_end": "2026-10-31"
    })
    response = client.get("/api/clients/Clark Kent/membership")
    assert response.status_code == 200
    data = response.get_json()
    assert data["membership_status"] == "Active"
    assert data["membership_end"] == "2026-10-31"


def test_workout_logging(client):
    """Test logging workouts and querying client workout history."""
    workout_data = {
        "client_name": "Diana Prince",
        "date": "2026-10-07",
        "workout_type": "Hypertrophy",
        "duration_min": 75,
        "notes": "Legs and Core focus"
    }
    post_res = client.post("/api/workouts", json=workout_data)
    assert post_res.status_code == 201
    workout_id = post_res.get_json()["id"]

    # Query workouts for client
    get_res = client.get("/api/workouts?client_name=Diana Prince")
    assert get_res.status_code == 200
    workouts = get_res.get_json()
    assert len(workouts) == 1
    assert workouts[0]["id"] == workout_id
    assert workouts[0]["workout_type"] == "Hypertrophy"


def test_exercise_logging(client):
    """Test adding exercises to a workout and querying them."""
    ex_data = {
        "workout_id": 1,
        "name": "Barbell Squat",
        "sets": 4,
        "reps": 8,
        "weight": 100.0
    }
    post_res = client.post("/api/exercises", json=ex_data)
    assert post_res.status_code == 201

    get_res = client.get("/api/exercises?workout_id=1")
    assert get_res.status_code == 200
    exercises = get_res.get_json()
    assert len(exercises) == 1
    assert exercises[0]["name"] == "Barbell Squat"


def test_progress_tracking(client):
    """Test weekly adherence logging and tracking."""
    progress_data = {
        "client_name": "Diana Prince",
        "week": "Week 1",
        "adherence": 95
    }
    post_res = client.post("/api/progress", json=progress_data)
    assert post_res.status_code == 201

    get_res = client.get("/api/progress?client_name=Diana Prince")
    assert get_res.status_code == 200
    records = get_res.get_json()
    assert len(records) == 1
    assert records[0]["adherence"] == 95


def test_metrics_tracking(client):
    """Test logging biometric weight and bodyfat records."""
    metrics_data = {
        "client_name": "Diana Prince",
        "date": "2026-10-07",
        "weight": 65.0,
        "waist": 28.0,
        "bodyfat": 18.5
    }
    post_res = client.post("/api/metrics", json=metrics_data)
    assert post_res.status_code == 201

    get_res = client.get("/api/metrics?client_name=Diana Prince")
    assert get_res.status_code == 200
    records = get_res.get_json()
    assert len(records) == 1
    assert records[0]["weight"] == 65.0
