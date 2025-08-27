import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()
logger = logging.getLogger(__name__)


class UserService:
    """Service class for user-related operations."""

    @staticmethod
    def create_user(username, email, password, role) -> User:
        """Validates password and creates a new user."""

        logger.info(f"Attempting to create user with username: {username}")
        try:
            validate_password(password)
        except ValidationError as e:
            raise ValueError(e)

        user = User.objects.create(username=username, email=email, role=role)
        user.set_password(password)
        user.save()
        logger.info(f"User {user.id} ({username}) created successfully")
        return user
