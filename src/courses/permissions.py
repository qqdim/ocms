from django.contrib.auth import get_user_model
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Course, Lecture, Submission
from .services import CourseService


def _get_course_from_obj(obj) -> Course | None:
    """Helper to extract course from various objects."""

    if isinstance(obj, Course):
        return obj
    if hasattr(obj, "course"):
        return obj.course
    if hasattr(obj, "lecture"):
        return obj.lecture.course
    if hasattr(obj, "assignment"):
        return obj.assignment.lecture.course
    if hasattr(obj, "submission"):
        return obj.submission.assignment.lecture.course
    return None


class IsTeacher(BasePermission):
    """Permission class to check if the user is a teacher."""

    def has_permission(self, request, view):
        """Check if the user is authenticated and has the teacher role."""
        return request.user.is_authenticated and getattr(request.user, "is_teacher")()


class IsStudent(BasePermission):
    """Permission class to check if the user is a student."""

    def has_permission(self, request, view):
        """Check if the user is authenticated and has the student role."""
        return request.user.is_authenticated and getattr(request.user, "is_student")()


class IsCourseTeacher(BasePermission):
    """Permission class to check if the user is a teacher of the course."""

    def has_object_permission(self, request, view, obj):
        """Check object-level permissions by asking the CourseService."""
        course = _get_course_from_obj(obj)
        if not course:
            return False
        return CourseService.is_user_course_teacher(course=course, user=request.user)


class IsCourseStudentOrTeacherReadOnly(BasePermission):
    """Permission class to allow read-only access for students and teachers."""

    def has_object_permission(self, request, view, obj):
        """Check object-level permissions for read-only access using CourseService."""
        course = _get_course_from_obj(obj)
        if not course:
            return False

        is_teacher = CourseService.is_user_course_teacher(course=course, user=request.user)

        if request.method in SAFE_METHODS:
            is_student = CourseService.is_user_course_student(course=course, user=request.user)
            return is_teacher or is_student

        return is_teacher
