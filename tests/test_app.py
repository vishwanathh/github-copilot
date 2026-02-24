import copy
import pytest
from fastapi.testclient import TestClient

from src import app as app_module
from src.app import app, activities as original_activities


@pytest.fixture(scope="module")
def client():
    """Create a TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """
    Reset the in‑memory `activities` dict before each test.

    This fixture is automatically applied to every test so that tests
    can mutate `app.activities` without affecting others.
    """
    # modify the module-level global, not just an attribute on the FastAPI app
    app_module.activities = copy.deepcopy(original_activities)
    yield


def test_root_redirect(client):
    # Arrange
    # (nothing to arrange)

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 200
    # TestClient follows redirects by default so final URL should be static.
    assert str(response.url).endswith("/static/index.html")


def test_get_activities(client):
    # Arrange
    expected = original_activities

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected


def test_signup_success(client):
    # Arrange
    activity = "Chess Club"
    email = "newstudent@mergington.edu"
    assert email not in app_module.activities[activity]["participants"]

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in app_module.activities[activity]["participants"]


def test_signup_nonexistent_activity(client):
    # Arrange
    activity = "Nonexistent"
    email = "foo@bar.com"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_already_signed(client):
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"
    assert email in app_module.activities[activity]["participants"]

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert f"Student {email} is already signed up for {activity}" in response.json()["detail"]


def test_cancel_success(client):
    # Arrange
    activity = "Programming Class"
    email = "emma@mergington.edu"
    assert email in app_module.activities[activity]["participants"]

    # Act
    response = client.delete(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    assert email not in app_module.activities[activity]["participants"]


def test_cancel_nonexistent_activity(client):
    # Arrange
    activity = "Nothing"
    email = "foo@bar.com"

    # Act
    response = client.delete(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_cancel_not_signed_up(client):
    # Arrange
    activity = "Chess Club"
    email = "nobody@mergington.edu"
    assert email not in app_module.activities[activity]["participants"]

    # Act
    response = client.delete(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert f"Student {email} is not signed up for {activity}" in response.json()["detail"]
