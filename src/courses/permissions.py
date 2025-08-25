from django.contrib.auth import get_user_model
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import Course, Grade, HomeworkAssignment, Lecture, Submission

User = get_user_model()


class IsTeacher(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "is_teacher")()


class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "is_student")()


class IsCourseTeacher(BasePermission):
    def _is_teacher_of(self, user, course: Course):
        return course.teachers.filter(id=user.id).exists()

    def has_object_permission(self, request, view, obj):
        user = request.user
        if isinstance(obj, Course):
            return self._is_teacher_of(user, obj)
        if isinstance(obj, Lecture):
            return self._is_teacher_of(user, obj.course)
        if isinstance(obj, HomeworkAssignment):
            return self._is_teacher_of(user, obj.lecture.course)
        if isinstance(obj, Submission):
            return self._is_teacher_of(user, obj.assignment.lecture.course)
        if isinstance(obj, Grade):
            return self._is_teacher_of(user, obj.submission.assignment.lecture.course)
        return False


class IsCourseStudentOrTeacherReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        def is_teacher(course: Course):
            return course.teachers.filter(id=request.user.id).exists()

        def is_student(course: Course):
            return course.students.filter(id=request.user.id).exists()

        if isinstance(obj, Course):
            course = obj
        elif hasattr(obj, "course"):
            course = obj.course
        elif hasattr(obj, "lecture"):
            course = obj.lecture.course
        elif hasattr(obj, "assignment"):
            course = obj.assignment.lecture.course
        elif hasattr(obj, "submission"):
            course = obj.submission.assignment.lecture.course
        else:
            return False
        if request.method in SAFE_METHODS:
            return is_teacher(course) or is_student(course)
        return is_teacher(course)
