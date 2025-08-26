import pytest
from django.contrib.auth import get_user_model
from courses.models import Course
from courses.services import CourseService
from courses.exceptions import UserRoleException, ValidationException

User = get_user_model()


@pytest.fixture
def setup_users_and_course():
    """Creates basic objects: teacher, student and course."""
    teacher = User.objects.create_user(username="teacher", password="123", role=User.Roles.TEACHER)
    student = User.objects.create_user(username="student", password="123", role=User.Roles.STUDENT)
    course = Course.objects.create(title="Test Course", created_by=teacher)
    course.teachers.add(teacher)
    return teacher, student, course


@pytest.mark.django_db
def test_add_student_to_course_successfully(setup_users_and_course):
    """Checking if a student has been successfully added to a course.    """
    teacher, student, course = setup_users_and_course
    service = CourseService()
    service.add_student_to_course(course=course, student_id=student.id)
    assert course.students.filter(id=student.id).exists()


@pytest.mark.django_db
def test_add_teacher_as_student_raises_error(setup_users_and_course):
    """Checking that it is not possible to add a teacher as a student    """
    teacher, student, course = setup_users_and_course
    another_teacher = User.objects.create_user(username="teacher2", password="123", role=User.Roles.TEACHER)
    service = CourseService()

    with pytest.raises(UserRoleException, match="User is not a student."):
        service.add_student_to_course(course=course, student_id=another_teacher.id)


@pytest.mark.django_db
def test_add_already_enrolled_student_raises_error(setup_users_and_course):
    """Checking that it is not possible to add a student to a course twice.    """
    teacher, student, course = setup_users_and_course
    service = CourseService()

    course.students.add(student)
    with pytest.raises(ValidationException, match="Student is already enrolled in this course."):
        service.add_student_to_course(course=course, student_id=student.id)