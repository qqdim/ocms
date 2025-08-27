import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestUserViews:
    def test_register_endpoint(self, api_client):
        """Tests the user registration API endpoint."""
        data = {"username": "api_user", "email": "api@example.com", "password": "ApiPassword123", "role": "TEACHER"}

        response = api_client.post("/api/users/register/", data=data)

        assert response.status_code == 201
        assert User.objects.filter(username="api_user").exists()

    def test_me_endpoint_unauthenticated(self, api_client):
        """Tests that the /me endpoint requires authentication."""
        response = api_client.get("/api/users/me/")
        assert response.status_code == 401

    def test_me_endpoint_authenticated(self, api_client, student):
        """Tests that the /me endpoint returns the correct user data when authenticated."""
        api_client.force_authenticate(user=student)

        response = api_client.get("/api/users/me/")

        assert response.status_code == 200
        assert response.data["username"] == student.username
        assert response.data["role"] == "STUDENT"
