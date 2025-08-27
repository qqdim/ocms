from django.contrib.auth.models import AbstractUser
from django.db import models
from .querysets import UserQuerySet


class User(AbstractUser):
    """Custom user model with roles for teachers and students."""

    class Roles(models.TextChoices):
        """Enumeration for user roles."""
        TEACHER = "TEACHER", "Teacher"
        STUDENT = "STUDENT", "Student"

    role = models.CharField(max_length=7, choices=Roles.choices)
    objects = UserQuerySet.as_manager()

    def is_teacher(self):
        """Check if the user has the teacher role."""
        return self.role == self.Roles.TEACHER

    def is_student(self):
        """Check if the user has the student role."""
        return self.role == self.Roles.STUDENT
