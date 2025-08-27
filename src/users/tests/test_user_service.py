import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from users.services import UserService

User = get_user_model()


@pytest.mark.django_db
class TestUserService:
    def test_create_user_successfully(self):
        """Tests that a user is created correctly with valid data."""
        service = UserService()
        user = service.create_user(
            username="testuser", email="test@example.com", password="StrongPassword123", role=User.Roles.STUDENT
        )

        assert User.objects.count() == 1
        assert user.username == "testuser"
        assert user.role == User.Roles.STUDENT
        assert user.check_password("StrongPassword123")

    def test_create_user_fails_with_weak_password(self):
        """Tests that user creation fails if the password does not meet validation criteria."""
        service = UserService()

        with pytest.raises(ValueError):
            service.create_user(
                username="testuser2", email="test2@example.com", password="123", role=User.Roles.TEACHER
            )

        assert User.objects.count() == 0
