from django.contrib.auth import get_user_model

from .exceptions import (
    AlreadyGradedException,
    NotEnrolledException,
    PermissionDeniedException,
    UserRoleException,
    ValidationException,
)
from .models import Course, Grade, Submission

User = get_user_model()


class CourseValidator:
    """Contains validation logic related to rates."""

    @staticmethod
    def validate_user_is_student(user: User):
        """Checks that the user has the student role."""
        if not user.is_student():
            raise UserRoleException("User is not a student.")

    @staticmethod
    def validate_student_not_enrolled(course: Course, student: User):
        """Checks that the student is not already enrolled in the course."""
        if course.students.filter(id=student.id).exists():
            raise ValidationException("Student is already enrolled in this course.")

    @staticmethod
    def validate_user_is_teacher(user: User):
        """Checks that the user has the teacher role."""
        if not user.is_teacher():
            raise UserRoleException("User is not a teacher.")

    @staticmethod
    def validate_teacher_not_assigned(course: Course, teacher: User):
        """Checks that the instructor is not already assigned to the course."""
        if course.teachers.filter(id=teacher.id).exists():
            raise ValidationException("Teacher is already assigned to this course.")


class SubmissionValidator:
    """Contains validation logic related to assignments."""

    @staticmethod
    def validate_student_is_enrolled(course: Course, student: User):
        """Checks that the student is enrolled in the course related to the assignment."""
        if not course.students.filter(id=student.id).exists():
            raise NotEnrolledException("You are not enrolled in this course.")

    @staticmethod
    def validate_submission_not_graded(submission: Submission):
        """Checks that the submission has not been graded yet."""
        if hasattr(submission, "grade"):
            raise AlreadyGradedException("Submission already graded; cannot modify.")

    @staticmethod
    def validate_user_is_submission_owner(submission: Submission, user: User):
        """Checks that the user is the author of the submission."""
        if submission.student_id != user.id:
            raise PermissionDeniedException("Cannot modify others' submissions.")


class GradingValidator:
    """Contains validation logic related to grades."""

    @staticmethod
    def validate_user_is_course_teacher(course: Course, user: User):
        """Checks that the user is a teacher of the course."""
        if not course.teachers.filter(id=user.id).exists():
            raise PermissionDeniedException("Only a course teacher can perform this action.")

    @staticmethod
    def validate_grade_does_not_exist(submission: Submission):
        """Checks that there is no grade for this submission yet."""
        if hasattr(submission, "grade"):
            raise ValidationException("Grade already exists. Use update instead.")

    @staticmethod
    def validate_user_can_comment(grade: Grade, user: User):
        """Checks that the user can comment on the grade (teacher or author)."""
        course = grade.submission.assignment.lecture.course
        is_teacher = course.teachers.filter(id=user.id).exists()
        is_student_owner = grade.submission.student_id == user.id

        if not (is_teacher or is_student_owner):
            raise PermissionDeniedException("Only course teachers or the submission owner can comment.")
