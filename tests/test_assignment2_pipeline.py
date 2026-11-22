"""
Assignment 2 Unit and Integration Tests
Validates Caloric Calculator, BMI Calculator, Program Catalog, Version Headers,
and Container Health Probes for Continuous Integration Pipelines.
"""

import os
import tempfile
import pytest
from app import create_app, init_db, calculate_calories, calculate_bmi
from ACEest_Fitness import app as entrypoint_app


@pytest.fixture
def client():
    """Create test client with isolated SQLite database."""
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    app = create_app({
        "TESTING": True,
        "DATABASE": db_path,
        "SECRET_KEY": "test-key-wilp-2026"
    })
    with app.app_context():
        init_db(db_path)

    yield app.test_client()

    os.close(db_fd)
    if os.path.exists(db_path):
        os.remove(db_path)


def test_version_endpoint(client):
    """Test /api/version returns version information."""
    res = client.get("/api/version")
    assert res.status_code == 200
    data = res.get_json()
    assert "version" in data
    assert data["student_id"] == "2025TM93130"


def test_programs_catalog(client):
    """Test /api/programs returns complete program definitions."""
    res = client.get("/api/programs")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["count"] == 3
    assert "Fat Loss (FL)" in data["programs"]
    assert "Muscle Gain (MG)" in data["programs"]
    assert "Beginner (BG)" in data["programs"]


def test_calculate_calories_engine():
    """Verify caloric multiplier formulas."""
    assert calculate_calories(70, "Fat Loss (FL)") == 1540
    assert calculate_calories(80, "Muscle Gain (MG)") == 2800
    assert calculate_calories(65, "Beginner (BG)") == 1690

    with pytest.raises(ValueError):
        calculate_calories(0, "Fat Loss")


def test_calculate_bmi_engine():
    """Verify BMI formula and categorization."""
    bmi, cat = calculate_bmi(70, 175)
    assert bmi == 22.86
    assert cat == "Normal Weight"

    with pytest.raises(ValueError):
        calculate_bmi(70, 0)


def test_api_calculate_calories_endpoint(client):
    """Test POST /api/calculate-calories."""
    payload = {"weight": 80.0, "program": "Muscle Gain (MG)"}
    res = client.post("/api/calculate-calories", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["target_calories"] == 2800


def test_api_calculate_bmi_endpoint(client):
    """Test POST /api/calculate-bmi."""
    payload = {"weight": 85.0, "height": 175.0}
    res = client.post("/api/calculate-bmi", json=payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["bmi"] == 27.76
    assert data["category"] == "Overweight"


def test_client_auto_calorie_assignment(client):
    """Test that client registration automatically calculates calories if omitted."""
    payload = {
        "name": "Auto Calorie Athlete",
        "age": 27,
        "height": 180.0,
        "weight": 70.0,
        "program": "Fat Loss (FL)"
    }
    res = client.post("/api/clients", json=payload)
    assert res.status_code == 201

    get_res = client.get("/api/clients/Auto Calorie Athlete")
    assert get_res.status_code == 200
    client_data = get_res.get_json()
    # 70 * 22 = 1540
    assert client_data["calories"] == 1540


def test_entrypoint_app_instance():
    """Verify that ACEest_Fitness entrypoint exports a valid Flask application."""
    assert entrypoint_app is not None
    assert entrypoint_app.name == "app"
