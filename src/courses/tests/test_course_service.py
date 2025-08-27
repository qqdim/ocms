import pytest
from unittest.mock import patch

from courses.services.course_service import CourseService
from courses.exceptions import UserRoleException, ValidationException
from .factories import CourseFactory, TeacherFactory, StudentFactory, CourseWithTeachersFactory


@pytest.mark.django_db
class TestCourseService:
    def test_create_course(self, teacher):
        with patch("courses.services.course_service.logger") as mock_logger:
            course = CourseService.create_course(title="New Course", description="New Description", created_by=teacher)

            assert course.title == "New Course"
            assert course.description == "New Description"
            assert course.created_by == teacher
            assert teacher in course.teachers.all()

            # Check logging
            mock_logger.info.assert_any_call(f"Creating course 'New Course' by user {teacher.id}")
            mock_logger.info.assert_any_call(f"Course {course.id} created successfully")

    def test_add_student_to_course_success(self, student):
        course = CourseFactory()

        with patch("courses.services.course_service.logger") as mock_logger:
            CourseService.add_student_to_course(course, student.id)

            assert student in course.students.all()
            mock_logger.info.assert_called_with(f"Student {student.id} added to course {course.id}")

    def test_add_student_to_course_not_student_role(self):
        course = CourseFactory()
        teacher = TeacherFactory()

        with pytest.raises(UserRoleException) as exc_info:
            CourseService.add_student_to_course(course, teacher.id)

        assert str(exc_info.value) == "User is not a student."
        assert teacher not in course.students.all()

    def test_add_student_to_course_already_enrolled(self):
        student = StudentFactory()
        course = CourseFactory(students=[student])

        with pytest.raises(ValidationException) as exc_info:
            CourseService.add_student_to_course(course, student.id)

        assert str(exc_info.value) == "Student is already enrolled in this course."

    def test_add_student_to_course_user_not_found(self):
        course = CourseFactory()

        with pytest.raises(Exception):
            CourseService.add_student_to_course(course, 99999)

    def test_remove_student_from_course(self):
        student = StudentFactory()
        course = CourseFactory(students=[student])

        with patch("courses.services.course_service.logger") as mock_logger:
            CourseService.remove_student_from_course(course, student.id)

            assert student not in course.students.all()
            mock_logger.info.assert_called_with(f"Student {student.id} removed from course {course.id}")

    def test_add_teacher_to_course_success(self):
        course = CourseFactory()
        new_teacher = TeacherFactory()

        with patch("courses.services.course_service.logger") as mock_logger:
            CourseService.add_teacher_to_course(course, new_teacher.id)

            assert new_teacher in course.teachers.all()
            mock_logger.info.assert_called_with(f"Teacher {new_teacher.id} added to course {course.id}")

    def test_add_teacher_to_course_not_teacher_role(self):
        course = CourseFactory()
        student = StudentFactory()

        with pytest.raises(UserRoleException) as exc_info:
            CourseService.add_teacher_to_course(course, student.id)

        assert str(exc_info.value) == "User is not a teacher."
        assert student not in course.teachers.all()

    def test_add_teacher_to_course_already_assigned(self):
        teacher = TeacherFactory()
        course = CourseFactory(teachers=[teacher])

        with pytest.raises(ValidationException) as exc_info:
            CourseService.add_teacher_to_course(course, teacher.id)

        assert str(exc_info.value) == "Teacher is already assigned to this course."

    def test_get_course_students(self):
        students = StudentFactory.create_batch(3)
        course = CourseFactory(students=students)

        retrieved_students = CourseService.get_course_students(course)

        assert len(retrieved_students) == 3
        for student in students:
            assert student in retrieved_students

    def test_get_course_students_empty(self):
        course = CourseFactory()
        students = CourseService.get_course_students(course)
        assert len(students) == 0

    def test_get_course_teachers(self):
        additional_teachers = TeacherFactory.create_batch(2)
        course = CourseFactory(teachers=additional_teachers)

        retrieved_teachers = CourseService.get_course_teachers(course)

        # Should have creator + additional teachers
        assert len(retrieved_teachers) == 3
        assert course.created_by in retrieved_teachers
        for teacher in additional_teachers:
            assert teacher in retrieved_teachers

    def test_get_course_teachers_only_creator(self):
        course = CourseFactory()
        teachers = CourseService.get_course_teachers(course)

        assert len(teachers) == 1
        assert course.created_by in teachers

    def test_is_user_course_teacher_true(self):
        teacher = TeacherFactory()
        course = CourseFactory(teachers=[teacher])

        result = CourseService.is_user_course_teacher(course, teacher)
        assert result is True

    def test_is_user_course_teacher_creator(self):
        course = CourseFactory()

        result = CourseService.is_user_course_teacher(course, course.created_by)
        assert result is True

    def test_is_user_course_teacher_false(self):
        course = CourseFactory()
        student = StudentFactory()

        result = CourseService.is_user_course_teacher(course, student)
        assert result is False

    def test_is_user_course_student_true(self):
        student = StudentFactory()
        course = CourseFactory(students=[student])

        result = CourseService.is_user_course_student(course, student)
        assert result is True

    def test_is_user_course_student_false(self):
        course = CourseFactory()
        teacher = TeacherFactory()

        result = CourseService.is_user_course_student(course, teacher)
        assert result is False

    def test_is_user_course_student_not_enrolled(self):
        course = CourseFactory()
        student = StudentFactory()

        result = CourseService.is_user_course_student(course, student)
        assert result is False

    def test_course_with_many_students_and_teachers(self):
        """Test using specialized factories"""
        course = CourseWithTeachersFactory()
        students = StudentFactory.create_batch(5)
        course.students.set(students)

        # Test bulk operations
        assert course.teachers.count() == 3  # Creator + 2 additional
        assert course.students.count() == 5

        # Test service methods with many users
        retrieved_teachers = CourseService.get_course_teachers(course)
        retrieved_students = CourseService.get_course_students(course)

        assert len(retrieved_teachers) == 3
        assert len(retrieved_students) == 5

    def test_course_permissions_multiple_users(self):
        """Test permissions with multiple users"""
        teachers = TeacherFactory.create_batch(3)
        students = StudentFactory.create_batch(3)
        course = CourseFactory(teachers=teachers, students=students)

        # Test all teachers have permission
        for teacher in teachers:
            assert CourseService.is_user_course_teacher(course, teacher)

        # Test all students are enrolled
        for student in students:
            assert CourseService.is_user_course_student(course, student)

        # Test creator has teacher permission
        assert CourseService.is_user_course_teacher(course, course.created_by)

        # Test cross-role permissions
        for teacher in teachers:
            assert not CourseService.is_user_course_student(course, teacher)

        for student in students:
            assert not CourseService.is_user_course_teacher(course, student)
