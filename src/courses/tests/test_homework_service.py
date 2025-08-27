import pytest
from unittest.mock import patch
from datetime import datetime, timezone

from courses.services.homework_service import HomeworkService
from .factories import TeacherFactory, LectureFactory, HomeworkAssignmentFactory


@pytest.mark.django_db
class TestHomeworkService:
    def test_create_homework_assignment_without_due_date(self, teacher):
        lecture = LectureFactory(created_by=teacher)

        with patch("courses.services.homework_service.logger") as mock_logger:
            assignment = HomeworkService.create_homework_assignment(
                text="Complete chapter 1 exercises", lecture=lecture, created_by=teacher
            )

            assert assignment.text == "Complete chapter 1 exercises"
            assert assignment.lecture == lecture
            assert assignment.due_date is None

            mock_logger.info.assert_any_call(
                f"Creating homework assignment for lecture {lecture.id} by user {teacher.id}"
            )
            mock_logger.info.assert_any_call(f"Homework assignment {assignment.id} created successfully")

    def test_create_homework_assignment_with_due_date(self, teacher):
        lecture = LectureFactory(created_by=teacher)
        due_date = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

        assignment = HomeworkService.create_homework_assignment(
            text="Complete the final project", lecture=lecture, created_by=teacher, due_date=due_date
        )

        assert assignment.due_date == due_date

    def test_get_assignments_by_lecture(self):
        lecture1 = LectureFactory()
        assignment1 = HomeworkAssignmentFactory(lecture=lecture1)
        assignment2 = HomeworkAssignmentFactory(lecture=lecture1)

        lecture2 = LectureFactory()
        assignment3 = HomeworkAssignmentFactory(lecture=lecture2)

        # Test fetching all assignments
        all_assignments = HomeworkService.get_assignments_by_lecture()
        assert all_assignments.count() == 3

        # Test filtering by a specific lecture
        lecture1_assignments = HomeworkService.get_assignments_by_lecture(lecture_id=lecture1.id)
        assert lecture1_assignments.count() == 2
        assert assignment1 in lecture1_assignments
        assert assignment2 in lecture1_assignments
        assert assignment3 not in lecture1_assignments

    def test_update_homework_assignment(self):
        assignment = HomeworkAssignmentFactory(text="Original text")
        due_date = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

        with patch("courses.services.homework_service.logger") as mock_logger:
            updated_assignment = HomeworkService.update_homework_assignment(
                assignment=assignment, text="Updated text", due_date=due_date
            )

            assert updated_assignment.text == "Updated text"
            assert updated_assignment.due_date == due_date

            mock_logger.info.assert_any_call(f"Updating homework assignment {assignment.id}")
            mock_logger.info.assert_any_call(f"Homework assignment {assignment.id} updated successfully")
