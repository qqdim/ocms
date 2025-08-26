import pytest
from django.contrib.auth import get_user_model
from users.services import UserService

User = get_user_model()

@pytest.mark.django_db
def test_create_user_successfully():
    """
    Check  UserService successfully creates the user.
    """
    service = UserService()
    user = service.create_user(
        username="testuser",
        email="test@example.com",
        password="StrongPassword123",
        role=User.Roles.STUDENT
    )

    assert User.objects.count() == 1
    assert user.username == "testuser"
    assert user.role == User.Roles.STUDENT
    assert user.check_password("StrongPassword123")
    assert not user.check_password("WrongPassword")