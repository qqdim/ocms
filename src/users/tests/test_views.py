import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_register_endpoint():
    """
    Check the user registration endpoint.
    """
    client = APIClient()
    data = {
        "username": "api_user",
        "email": "api@example.com",
        "password": "ApiPassword123",
        "role": "TEACHER"
    }

    response = client.post("/api/users/register", data=data)

    assert response.status_code == 201
    assert User.objects.filter(username="api_user").exists()