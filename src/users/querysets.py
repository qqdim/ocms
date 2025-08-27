from django.db import models


class UserQuerySet(models.QuerySet):
    """Custom QuerySet for the User model."""

    def teachers(self):
        """Returns a QuerySet of users with the 'TEACHER' role."""
        return self.filter(role='TEACHER')

    def students(self):
        """Returns a QuerySet of users with the 'STUDENT' role."""
        return self.filter(role='STUDENT')

    def with_related_courses(self):
        """Prefetches related teaching and enrolled courses for efficiency."""
        return self.prefetch_related('teaching_courses', 'enrolled_courses')