import pytest
from unittest.mock import patch, Mock

from courses.services.submission_service import SubmissionService
from courses.exceptions import NotEnrolledException, AlreadyGradedException, PermissionDeniedException
from .factories import (
    TeacherFactory,
    StudentFactory,
    HomeworkAssignmentFactory,
    SubmissionFactory,
    GradedSubmissionFactory,
    CourseFactory,
    LectureFactory,
)


@pytest.mark.django_db
class TestSubmissionService:
    def test_create_submission(self, student):
        """Tests that a submission can be created successfully."""
        assignment = HomeworkAssignmentFactory()
        # Студент должен быть записан на курс, чтобы сдать работу
        assignment.lecture.course.students.add(student)

        with patch("courses.services.submission_service.logger") as mock_logger:
            submission = SubmissionService.create_submission(
                assignment=assignment, student=student, text="My homework solution"
            )

            assert submission.assignment == assignment
            assert submission.student == student

            mock_logger.info.assert_any_call(
                f"Creating submission for assignment {assignment.id} by student {student.id}"
            )
            mock_logger.info.assert_any_call(f"Submission {submission.id} created successfully")

    def test_create_submission_not_enrolled(self, student):
        """Tests that a student cannot submit to a course they are not enrolled in."""
        assignment = HomeworkAssignmentFactory()

        with pytest.raises(NotEnrolledException, match="You are not enrolled in this course."):
            SubmissionService.create_submission(assignment=assignment, student=student, text="My homework solution")

    def test_update_submission(self, student):
        """Tests that a student can update their own submission."""
        submission = SubmissionFactory(student=student)

        with patch("courses.services.submission_service.logger") as mock_logger:
            updated_submission = SubmissionService.update_submission(
                submission=submission, user=student, text="Updated submission text"
            )

            assert updated_submission.text == "Updated submission text"
            mock_logger.info.assert_any_call(f"Updating submission {submission.id}")
            mock_logger.info.assert_any_call(f"Submission {submission.id} updated successfully")

    def test_update_submission_fails_if_graded(self, student):
        """Tests that a submission cannot be updated after it has been graded."""
        submission = GradedSubmissionFactory(student=student)

        with pytest.raises(AlreadyGradedException, match="Submission already graded; cannot modify."):
            SubmissionService.update_submission(submission=submission, user=student, text="This should fail")

    def test_update_submission_permission_denied(self, student):
        """Tests that a user cannot update another user's submission."""
        submission = SubmissionFactory()  # Создано другим студентом

        with pytest.raises(PermissionDeniedException, match="Cannot modify others' submissions."):
            SubmissionService.update_submission(
                submission=submission,
                user=student,  # Попытка редактирования от имени другого студента
                text="This should fail",
            )

    def test_get_submissions_for_user(self, teacher, student):
        """Tests that users can only see submissions they are allowed to see."""
        # --- Студент видит только свои работы ---
        submission1 = SubmissionFactory(student=student)
        SubmissionFactory()  # Работа другого студента, которую не должен видеть student

        student_submissions = SubmissionService.get_submissions_for_user(student)
        assert student_submissions.count() == 1
        assert submission1 in student_submissions

        # --- Учитель видит работы по своему курсу ---
        course = CourseFactory(created_by=teacher)
        lecture = LectureFactory(course=course)
        assignment = HomeworkAssignmentFactory(lecture=lecture)
        submission2 = SubmissionFactory(assignment=assignment)
        SubmissionFactory()  # Работа по другому курсу, которую не должен видеть teacher

        teacher_submissions = SubmissionService.get_submissions_for_user(teacher)
        assert teacher_submissions.count() == 1
        assert submission2 in teacher_submissions

    def test_can_user_view_submission(self, teacher, student):
        """Tests the permission logic for viewing a single submission."""
        submission = SubmissionFactory(student=student)
        course_teacher = submission.assignment.lecture.course.created_by

        # Владелец может видеть свою работу
        assert SubmissionService.can_user_view_submission(submission, student) is True
        # Учитель курса может видеть работу
        assert SubmissionService.can_user_view_submission(submission, course_teacher) is True
        # Посторонний учитель не может видеть работу
        assert SubmissionService.can_user_view_submission(submission, teacher) is False
