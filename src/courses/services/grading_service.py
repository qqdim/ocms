import logging
from typing import Optional

from ..models import Grade, GradeComment, Submission
from ..exceptions import PermissionDeniedException, ValidationException

logger = logging.getLogger(__name__)


class GradingService:
    """Service class for grading operations."""
    
    @staticmethod
    def create_grade(submission: Submission, score: int, graded_by, comment: str = "") -> Grade:
        """Create a new grade for submission."""

        course = submission.assignment.lecture.course
        if not course.teachers.filter(id=graded_by.id).exists():
            raise PermissionDeniedException("Only a course teacher can grade this submission.")

        if hasattr(submission, "grade"):
            raise ValidationException("Grade already exists. Use update instead.")
        
        logger.info(f"Creating grade for submission {submission.id} by teacher {graded_by.id}")
        
        grade = Grade.objects.create(
            submission=submission,
            score=score,
            comment=comment,
            graded_by=graded_by
        )
        logger.info(f"Grade {grade.id} created successfully")
        return grade
    
    @staticmethod
    def update_grade(grade: Grade, user, **validated_data) -> Grade:
        """Update existing grade."""

        course = grade.submission.assignment.lecture.course
        if not course.teachers.filter(id=user.id).exists():
            raise PermissionDeniedException("Only a course teacher can update this grade.")
        
        logger.info(f"Updating grade {grade.id}")
        
        for field, value in validated_data.items():
            setattr(grade, field, value)
        
        grade.save()
        logger.info(f"Grade {grade.id} updated successfully")
        return grade
    
    @staticmethod
    def can_user_view_grade(grade: Grade, user) -> bool:
        """Check if user can view the grade."""

        course = grade.submission.assignment.lecture.course
        is_student_owner = grade.submission.student_id == user.id
        is_course_teacher = course.teachers.filter(id=user.id).exists()
        return is_student_owner or is_course_teacher
    
    @staticmethod
    def create_grade_comment(grade: Grade, author, text: str) -> GradeComment:
        """Create a comment on a grade."""

        course = grade.submission.assignment.lecture.course
        is_teacher = course.teachers.filter(id=author.id).exists()
        is_student_owner = grade.submission.student_id == author.id
        
        if not (is_teacher or is_student_owner):
            raise PermissionDeniedException("Only course teachers or the submission owner can comment.")
        
        logger.info(f"Creating comment on grade {grade.id} by user {author.id}")
        
        comment = GradeComment.objects.create(
            grade=grade,
            author=author,
            text=text
        )
        
        logger.info(f"Grade comment {comment.id} created successfully")
        return comment
    
