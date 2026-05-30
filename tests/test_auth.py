import pytest
from app import create_app, db


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


class TestRegister:
    def test_register_page_loads(self, client):
        r = client.get("/auth/register")
        assert r.status_code == 200

    def test_register_valid_user(self, client):
        r = client.post("/auth/register", data={
            "name": "Test User", "email": "test@example.com",
            "password": "Test@1234", "confirm_password": "Test@1234",
        }, follow_redirects=True)
        assert r.status_code == 200

    def test_register_duplicate_email(self, client):
        data = {"name": "A", "email": "dup@ex.com", "password": "Test@1234", "confirm_password": "Test@1234"}
        client.post("/auth/register", data=data)
        r = client.post("/auth/register", data=data, follow_redirects=True)
        assert b"already exists" in r.data

    def test_register_weak_password(self, client):
        r = client.post("/auth/register", data={
            "name": "A", "email": "weak@ex.com",
            "password": "abc", "confirm_password": "abc",
        }, follow_redirects=True)
        assert b"least" in r.data or b"uppercase" in r.data or b"number" in r.data

    def test_register_mismatched_passwords(self, client):
        r = client.post("/auth/register", data={
            "name": "A", "email": "mm@ex.com",
            "password": "Test@1234", "confirm_password": "Test@9999",
        }, follow_redirects=True)
        assert b"do not match" in r.data


class TestLogin:
    def test_login_page_loads(self, client):
        assert client.get("/auth/login").status_code == 200

    def test_login_invalid_credentials(self, client):
        r = client.post("/auth/login", data={
            "email": "nope@ex.com", "password": "wrong"
        }, follow_redirects=True)
        assert b"Invalid" in r.data

    def test_health_endpoint(self, client):
        r = client.get("/health")
        assert r.status_code in (200, 503)
        data = r.get_json()
        assert "status" in data
