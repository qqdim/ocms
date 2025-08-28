import pytest
from unittest.mock import patch, Mock

from courses.services.lecture_service import LectureService
from .factories import TeacherFactory, CourseFactory, LectureFactory


@pytest.mark.django_db
class TestLectureService:
    def test_create_lecture(self, teacher):
        """Tests that a lecture can be created with and without a presentation."""
        course = CourseFactory(created_by=teacher)

        # --- Test case 1: Without presentation ---
        with patch("courses.services.lecture_service.logger") as mock_logger:
            lecture = LectureService.create_lecture(topic="Introduction to Python", course=course, created_by=teacher)

            assert lecture.topic == "Introduction to Python"
            assert lecture.course == course
            assert lecture.created_by == teacher
            assert lecture.presentation.name == ""

            mock_logger.info.assert_any_call(
                f"Creating lecture 'Introduction to Python' for course {course.id} by user {teacher.id}"
            )
            mock_logger.info.assert_any_call(f"Lecture {lecture.id} created successfully")

        # --- Test case 2: With presentation ---
        mock_presentation = Mock()
        mock_presentation.name = "presentation.pdf"

        lecture_with_file = LectureService.create_lecture(
            topic="Advanced Python", course=course, created_by=teacher, presentation=mock_presentation
        )
        assert lecture_with_file.presentation.name == "presentation.pdf"

    def test_get_lectures_by_course(self):
        """Tests fetching all lectures and filtering them by course."""
        course1 = CourseFactory()
        LectureFactory.create_batch(2, course=course1)

        course2 = CourseFactory()
        lecture3 = LectureFactory(course=course2)

        # --- Test case 1: Get all lectures ---
        all_lectures = LectureService.get_lectures_by_course()
        assert all_lectures.count() == 3

        # --- Test case 2: Filter by course ---
        course1_lectures = LectureService.get_lectures_by_course(course_id=course1.id)
        assert course1_lectures.count() == 2
        assert lecture3 not in course1_lectures

        # --- Test case 3: Non-existent course ---
        empty_result = LectureService.get_lectures_by_course(course_id=99999)
        assert empty_result.count() == 0

    def test_update_lecture(self):
        """Tests updating one or multiple fields of a lecture."""
        lecture = LectureFactory(topic="Original Topic")

        # --- Test case 1: Update a single field ---
        with patch("courses.services.lecture_service.logger") as mock_logger:
            updated_lecture = LectureService.update_lecture(lecture=lecture, topic="Updated Topic Only")
            assert updated_lecture.topic == "Updated Topic Only"

            mock_logger.info.assert_any_call(f"Updating lecture {lecture.id}")
            mock_logger.info.assert_any_call(f"Lecture {lecture.id} updated successfully")

        # --- Test case 2: Update multiple fields ---
        new_course = CourseFactory()
        mock_presentation = Mock()
        mock_presentation.name = "new.pptx"

        updated_lecture_multi = LectureService.update_lecture(
            lecture=lecture, topic="Multi Update", course=new_course, presentation=mock_presentation
        )
        assert updated_lecture_multi.topic == "Multi Update"
        assert updated_lecture_multi.course == new_course
        assert updated_lecture_multi.presentation.name == "new.pptx"
