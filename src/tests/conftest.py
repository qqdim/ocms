import pytest
from rest_framework.test import APIClient

from src.courses.tests.factories import StudentFactory, TeacherFactory


@pytest.fixture
def api_client():
    """A fixture to provide an API client for tests."""
    return APIClient()


@pytest.fixture
def teacher():
    """A fixture to create a teacher user."""
    return TeacherFactory()


@pytest.fixture
def student():
    """A fixture to create a student user."""
    return StudentFactory()
