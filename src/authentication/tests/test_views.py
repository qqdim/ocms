import pytest


@pytest.mark.django_db
def test_jwt_create_endpoint_requires_data(api_client):
    """
    Smoke test to ensure the JWT create endpoint is configured and returns 400 for bad requests.
    """
    response = api_client.post("/api/auth/jwt/create/", data={})
    assert response.status_code == 400
