import pytest
from unittest.mock import patch

from courses.services.grading_service import GradingService
from courses.exceptions import PermissionDeniedException, ValidationException
from .factories import (
    TeacherFactory,
    StudentFactory,
    SubmissionFactory,
    GradeFactory,
    GradeCommentFactory,
    GradedSubmissionFactory,
)


@pytest.mark.django_db
class TestGradingService:
    def test_create_grade_success(self, teacher):
        submission = SubmissionFactory()
        course_teacher = submission.assignment.lecture.course.created_by

        with patch("courses.services.grading_service.logger") as mock_logger:
            grade = GradingService.create_grade(
                submission=submission, score=90, graded_by=course_teacher, comment="Excellent work!"
            )

            assert grade.submission == submission
            assert grade.score == 90
            assert grade.comment == "Excellent work!"
            assert grade.graded_by == course_teacher

            # Check logging
            mock_logger.info.assert_any_call(f"Creating grade for submission {submission.id} by teacher {teacher.id}")
            mock_logger.info.assert_any_call(f"Grade {grade.id} created successfully")

    def test_create_grade_permission_denied(self):
        submission = SubmissionFactory()
        unauthorized_teacher = TeacherFactory()

        with pytest.raises(PermissionDeniedException) as exc_info:
            GradingService.create_grade(submission=submission, score=90, graded_by=unauthorized_teacher)

        assert str(exc_info.value) == "Only a course teacher can grade this submission."

    def test_create_grade_permission_denied_student(self, student):
        submission = SubmissionFactory()

        with pytest.raises(PermissionDeniedException) as exc_info:
            GradingService.create_grade(submission=submission, score=90, graded_by=student)

        assert str(exc_info.value) == "Only a course teacher can grade this submission."

    def test_create_grade_already_exists(self):
        # Use specialized factory that creates a graded submission
        submission = GradedSubmissionFactory()
        teacher = submission.assignment.lecture.created_by

        with pytest.raises(ValidationException) as exc_info:
            GradingService.create_grade(submission=submission, score=90, graded_by=teacher)

        assert str(exc_info.value) == "Grade already exists. Use update instead."

    def test_update_grade_success(self):
        grade = GradeFactory()
        teacher = grade.graded_by

        with patch("courses.services.grading_service.logger") as mock_logger:
            updated_grade = GradingService.update_grade(grade=grade, user=teacher, score=95, comment="Updated comment")

            assert updated_grade.score == 95
            assert updated_grade.comment == "Updated comment"

            # Check logging
            mock_logger.info.assert_any_call(f"Updating grade {grade.id}")
            mock_logger.info.assert_any_call(f"Grade {grade.id} updated successfully")

    def test_update_grade_permission_denied(self):
        grade = GradeFactory()
        unauthorized_teacher = TeacherFactory()

        with pytest.raises(PermissionDeniedException) as exc_info:
            GradingService.update_grade(grade=grade, user=unauthorized_teacher, score=95)

        assert str(exc_info.value) == "Only a course teacher can update this grade."

    def test_update_grade_permission_denied_student(self):
        grade = GradeFactory()
        student = StudentFactory()

        with pytest.raises(PermissionDeniedException) as exc_info:
            GradingService.update_grade(grade=grade, user=student, score=95)

        assert str(exc_info.value) == "Only a course teacher can update this grade."

    def test_can_user_view_grade_student_owner(self):
        grade = GradeFactory()
        student = grade.submission.student

        result = GradingService.can_user_view_grade(grade, student)
        assert result is True

    def test_can_user_view_grade_course_teacher(self):
        grade = GradeFactory()
        teacher = grade.graded_by

        result = GradingService.can_user_view_grade(grade, teacher)
        assert result is True

    def test_can_user_view_grade_other_course_teacher(self):
        grade = GradeFactory()
        # Add another teacher to the course
        other_teacher = TeacherFactory()
        grade.submission.assignment.lecture.course.teachers.add(other_teacher)

        result = GradingService.can_user_view_grade(grade, other_teacher)
        assert result is True

    def test_can_user_view_grade_unauthorized(self):
        grade = GradeFactory()
        unauthorized_user = StudentFactory()

        result = GradingService.can_user_view_grade(grade, unauthorized_user)
        assert result is False

    def test_create_grade_comment_by_teacher(self):
        grade = GradeFactory()
        teacher = grade.graded_by

        with patch("courses.services.grading_service.logger") as mock_logger:
            comment = GradingService.create_grade_comment(grade=grade, author=teacher, text="Additional feedback")

            assert comment.grade == grade
            assert comment.author == teacher
            assert comment.text == "Additional feedback"

            # Check logging
            mock_logger.info.assert_any_call(f"Creating comment on grade {grade.id} by user {teacher.id}")
            mock_logger.info.assert_any_call(f"Grade comment {comment.id} created successfully")

    def test_create_grade_comment_by_student_owner(self):
        grade = GradeFactory()
        student = grade.submission.student

        with patch("courses.services.grading_service.logger") as mock_logger:
            comment = GradingService.create_grade_comment(
                grade=grade, author=student, text="Thank you for the feedback"
            )

            assert comment.grade == grade
            assert comment.author == student
            assert comment.text == "Thank you for the feedback"

    def test_create_grade_comment_by_other_course_teacher(self):
        grade = GradeFactory()
        other_teacher = TeacherFactory()
        grade.submission.assignment.lecture.course.teachers.add(other_teacher)

        comment = GradingService.create_grade_comment(
            grade=grade, author=other_teacher, text="Additional teacher feedback"
        )

        assert comment.author == other_teacher
        assert comment.grade == grade

    def test_create_grade_comment_permission_denied(self):
        grade = GradeFactory()
        unauthorized_user = StudentFactory()

        with pytest.raises(PermissionDeniedException) as exc_info:
            GradingService.create_grade_comment(grade=grade, author=unauthorized_user, text="Unauthorized comment")

        assert str(exc_info.value) == "Only course teachers or the submission owner can comment."

    def test_get_grade_comments_for_user_teacher(self):
        grade = GradeFactory()
        teacher = grade.graded_by
        student = grade.submission.student

        # Create comments using factory
        teacher_comment = GradeCommentFactory(grade=grade, author=teacher)
        student_comment = GradeCommentFactory(grade=grade, author=student)

        comments = GradingService.get_grade_comments_for_user(teacher)

        assert teacher_comment in comments
        assert student_comment in comments

    def test_get_grade_comments_for_user_student(self):
        grade = GradeFactory()
        teacher = grade.graded_by
        student = grade.submission.student

        # Create comments using factory
        teacher_comment = GradeCommentFactory(grade=grade, author=teacher)
        student_comment = GradeCommentFactory(grade=grade, author=student)

        comments = GradingService.get_grade_comments_for_user(student)

        assert teacher_comment in comments
        assert student_comment in comments

    def test_get_grade_comments_for_user_with_grade_id_filter(self):
        grade = GradeFactory()
        teacher = grade.graded_by

        # Create comment for this grade
        comment = GradeCommentFactory(grade=grade, author=teacher)

        # Create another grade with comment (should be filtered out)
        other_grade = GradeFactory()
        GradeCommentFactory(grade=other_grade, author=teacher)

        comments = GradingService.get_grade_comments_for_user(teacher, grade_id=grade.id)

        assert comment in comments
        assert comments.count() == 1

    def test_get_grade_comments_for_user_unauthorized(self):
        grade = GradeFactory()
        teacher = grade.graded_by
        unauthorized_user = StudentFactory()

        GradeCommentFactory(grade=grade, author=teacher)

        comments = GradingService.get_grade_comments_for_user(unauthorized_user)

        assert comments.count() == 0

    def test_get_grade_comments_multiple_grades(self):
        """Test getting comments across multiple grades for a teacher"""
        teacher = TeacherFactory()

        # Create multiple submissions in the same course
        course = teacher.created_courses.first() if teacher.created_courses.exists() else None
        if not course:
            # Create course with this teacher
            from .factories import CourseFactory

            course = CourseFactory(created_by=teacher)

        submissions = SubmissionFactory.create_batch(3)
        # Enroll students and add teacher to courses
        for submission in submissions:
            submission.assignment.lecture.course.teachers.add(teacher)

        grades = [GradeFactory(submission=submission, graded_by=teacher) for submission in submissions]
        comments = [GradeCommentFactory(grade=grade, author=teacher) for grade in grades]

        retrieved_comments = GradingService.get_grade_comments_for_user(teacher)

        for comment in comments:
            assert comment in retrieved_comments

    def test_grading_workflow_end_to_end(self):
        """Test complete grading workflow using factories"""
        submission = SubmissionFactory()
        teacher = submission.assignment.lecture.created_by
        student = submission.student

        # Create grade
        grade = GradingService.create_grade(
            submission=submission, score=88, graded_by=teacher, comment="Good work overall"
        )

        # Update grade
        updated_grade = GradingService.update_grade(
            grade=grade, user=teacher, score=90, comment="Excellent after review"
        )

        # Add comments from both teacher and student
        teacher_comment = GradingService.create_grade_comment(
            grade=updated_grade, author=teacher, text="Keep up the good work!"
        )

        student_comment = GradingService.create_grade_comment(
            grade=updated_grade, author=student, text="Thank you for the feedback!"
        )

        # Verify final state
        assert updated_grade.score == 90
        assert updated_grade.comment == "Excellent after review"
        assert updated_grade.comments.count() == 2
        assert teacher_comment in updated_grade.comments.all()
        assert student_comment in updated_grade.comments.all()

        # Test view permissions
        assert GradingService.can_user_view_grade(updated_grade, teacher)
        assert GradingService.can_user_view_grade(updated_grade, student)
