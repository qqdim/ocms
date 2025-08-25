import logging
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from typing import List, Optional

from ..exceptions import UserRoleException, ValidationException
from ..models import Course

User = get_user_model()
logger = logging.getLogger(__name__)


class CourseService:
    """Service class for course-related operations."""

    @staticmethod
    def create_course(title: str, description: str, created_by) -> Course:
        """Create a new course and add creator as teacher."""

        logger.info(f"Creating course '{title}' by user {created_by.id}")

        course = Course.objects.create(
            title=title,
            description=description,
            created_by=created_by
        )
        course.teachers.add(created_by)
        logger.info(f"Course {course.id} created successfully")
        return course

    @staticmethod
    def add_student_to_course(course: Course, student_id: int) -> None:
        """Add a student to the course."""

        student = get_object_or_404(User, id=student_id)

        if not student.is_student():
            raise UserRoleException("User is not a student.")

        if course.students.filter(id=student_id).exists():
            raise ValidationException("Student is already enrolled in this course.")

        course.students.add(student)
        logger.info(f"Student {student_id} added to course {course.id}")

    @staticmethod
    def remove_student_from_course(course: Course, student_id: int) -> None:
        """Remove a student from the course."""

        student = get_object_or_404(User, id=student_id)
        course.students.remove(student)
        logger.info(f"Student {student_id} removed from course {course.id}")

    @staticmethod
    def add_teacher_to_course(course: Course, teacher_id: int) -> None:
        """Add a teacher to the course."""

        teacher = get_object_or_404(User, id=teacher_id)
        if not teacher.is_teacher():
            raise UserRoleException("User is not a teacher.")

        if course.teachers.filter(id=teacher_id).exists():
            raise ValidationException("Teacher is already assigned to this course.")

        course.teachers.add(teacher)
        logger.info(f"Teacher {teacher_id} added to course {course.id}")

    @staticmethod
    def get_course_students(course: Course) -> List[User]:
        """Get all students enrolled in the course."""

        return list(course.students.all())

    @staticmethod
    def get_course_teachers(course: Course) -> List[User]:
        """Get all teachers assigned to the course."""

        return list(course.teachers.all())

    @staticmethod
    def is_user_course_teacher(course: Course, user) -> bool:
        """Check if user is a teacher of the course."""

        return course.teachers.filter(id=user.id).exists()

    @staticmethod
    def is_user_course_student(course: Course, user) -> bool:
        """Check if user is a student of the course."""

        return course.students.filter(id=user.id).exists()
