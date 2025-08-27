import factory
from factory.django import DjangoModelFactory
from factory import Faker, SubFactory, LazyAttribute, LazyFunction
from django.contrib.auth import get_user_model
from datetime import datetime, timezone

from courses.models import Course, Lecture, HomeworkAssignment, Submission, Grade, GradeComment

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Faker("user_name")
    email = Faker("email")
    first_name = Faker("first_name")
    last_name = Faker("last_name")
    is_active = True
    role = User.Roles.STUDENT

    @factory.post_generation
    def set_password(self, create, extracted, **kwargs):
        if not create:
            return
        password = extracted if extracted else "testpass123"
        self.set_password(password)
        self.save()


class TeacherFactory(UserFactory):
    role = User.Roles.TEACHER
    username = Faker("user_name")
    email = Faker("email")


class StudentFactory(UserFactory):
    role = User.Roles.STUDENT
    username = Faker("user_name")
    email = Faker("email")


class CourseFactory(DjangoModelFactory):
    class Meta:
        model = Course

    title = Faker("catch_phrase")
    description = Faker("text", max_nb_chars=500)
    created_by = SubFactory(TeacherFactory)

    @factory.post_generation
    def teachers(self, create, extracted, **kwargs):
        if not create:
            return

        # Add creator as teacher by default
        self.teachers.add(self.created_by)

        if extracted:
            for teacher in extracted:
                self.teachers.add(teacher)

    @factory.post_generation
    def students(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for student in extracted:
                self.students.add(student)


class LectureFactory(DjangoModelFactory):
    class Meta:
        model = Lecture

    topic = Faker("sentence", nb_words=4)
    course = SubFactory(CourseFactory)
    created_by = LazyAttribute(lambda obj: obj.course.created_by)


class HomeworkAssignmentFactory(DjangoModelFactory):
    class Meta:
        model = HomeworkAssignment

    text = Faker("text", max_nb_chars=1000)
    lecture = SubFactory(LectureFactory)
    created_by = LazyAttribute(lambda obj: obj.lecture.created_by)
    due_date = Faker("future_datetime", end_date="+30d", tzinfo=timezone.utc)


class SubmissionFactory(DjangoModelFactory):
    class Meta:
        model = Submission

    assignment = SubFactory(HomeworkAssignmentFactory)
    student = SubFactory(StudentFactory)
    text = Faker("text", max_nb_chars=2000)

    @factory.post_generation
    def enroll_student(self, create, extracted, **kwargs):
        """Automatically enroll the student in the course"""
        if create:
            self.assignment.lecture.course.students.add(self.student)


class GradeFactory(DjangoModelFactory):
    class Meta:
        model = Grade

    submission = SubFactory(SubmissionFactory)
    score = Faker("random_int", min=0, max=100)
    comment = Faker("text", max_nb_chars=500)
    graded_by = LazyAttribute(lambda obj: obj.submission.assignment.lecture.created_by)


class GradeCommentFactory(DjangoModelFactory):
    class Meta:
        model = GradeComment

    grade = SubFactory(GradeFactory)
    author = LazyAttribute(lambda obj: obj.grade.submission.student)
    text = Faker("text", max_nb_chars=300)


# Specialized factories for specific test scenarios


class CourseWithStudentsFactory(CourseFactory):
    """Factory that creates a course with enrolled students"""

    @factory.post_generation
    def students(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for student in extracted:
                self.students.add(student)
        else:
            # Create 3 students by default
            students = StudentFactory.create_batch(3)
            self.students.add(*students)


class CourseWithTeachersFactory(CourseFactory):
    """Factory that creates a course with multiple teachers"""

    @factory.post_generation
    def teachers(self, create, extracted, **kwargs):
        if not create:
            return

        # Add creator as teacher
        self.teachers.add(self.created_by)

        if extracted:
            for teacher in extracted:
                self.teachers.add(teacher)
        else:
            # Create 2 additional teachers by default
            teachers = TeacherFactory.create_batch(2)
            self.teachers.add(*teachers)


class LectureWithAssignmentsFactory(LectureFactory):
    """Factory that creates a lecture with homework assignments"""

    @factory.post_generation
    def assignments(self, create, extracted, **kwargs):
        if not create:
            return

        count = extracted if extracted else 2
        HomeworkAssignmentFactory.create_batch(count, lecture=self)


class GradedSubmissionFactory(SubmissionFactory):
    """Factory that creates a submission with a grade"""

    @factory.post_generation
    def create_grade(self, create, extracted, **kwargs):
        if create:
            GradeFactory(submission=self)


class SubmissionWithCommentsFactory(SubmissionFactory):
    """Factory that creates a submission with grade and comments"""

    @factory.post_generation
    def create_grade_with_comments(self, create, extracted, **kwargs):
        if create:
            grade = GradeFactory(submission=self)
            # Create comments from both teacher and student
            GradeCommentFactory(grade=grade, author=grade.graded_by)
            GradeCommentFactory(grade=grade, author=self.student)
