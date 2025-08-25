import logging
from django.db.models import QuerySet, Q
from typing import Optional

from ..exceptions import NotEnrolledException, AlreadyGradedException, PermissionDeniedException
from ..models import Submission, HomeworkAssignment

logger = logging.getLogger(__name__)


class SubmissionService:
    """Service class for submission-related operations."""

    @staticmethod
    def create_submission(assignment: HomeworkAssignment, student, text: str = "", attachment=None) -> Submission:
        """Create a new submission."""

        course = assignment.lecture.course
        if not course.students.filter(id=student.id).exists():
            raise NotEnrolledException("You are not enrolled in this course.")

        logger.info(f"Creating submission for assignment {assignment.id} by student {student.id}")

        submission = Submission.objects.create(
            assignment=assignment,
            student=student,
            text=text,
            attachment=attachment
        )

        logger.info(f"Submission {submission.id} created successfully")
        return submission

    @staticmethod
    def update_submission(submission: Submission, user, **validated_data) -> Submission:
        """Update submission with validation."""

        if hasattr(submission, "grade"):
            raise AlreadyGradedException("Submission already graded; cannot modify.")

        if submission.student_id != user.id:
            raise PermissionDeniedException("Cannot modify others' submissions.")

        logger.info(f"Updating submission {submission.id}")

        for field, value in validated_data.items():
            setattr(submission, field, value)

        submission.save()
        logger.info(f"Submission {submission.id} updated successfully")
        return submission

    @staticmethod
    def get_submissions_for_user(user, assignment_id: Optional[int] = None) -> QuerySet[Submission]:
        """Get submissions visible to the user based on their role."""

        queryset = Submission.objects.select_related("assignment", "assignment__lecture__course").all()

        if assignment_id:
            queryset = queryset.filter(assignment_id=assignment_id)

        if hasattr(user, "is_student") and user.is_student():
            queryset = queryset.filter(student=user)
        elif hasattr(user, "is_teacher") and user.is_teacher():
            queryset = queryset.filter(assignment__lecture__course__teachers=user)
        else:
            queryset = queryset.none()

        return queryset.order_by("-submitted_at")

    @staticmethod
    def can_user_view_submission(submission: Submission, user) -> bool:
        """Check if user can view the submission."""

        course = submission.assignment.lecture.course
        is_student_owner = submission.student_id == user.id
        is_course_teacher = course.teachers.filter(id=user.id).exists()

        return is_student_owner or is_course_teacher
