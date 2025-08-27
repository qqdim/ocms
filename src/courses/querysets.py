from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Q

User = get_user_model()


class CourseQuerySet(models.QuerySet):
    """Custom QuerySet for Course model."""

    def with_relations(self):
        """Prefetch related objects for efficient loading."""
        return self.select_related('created_by').prefetch_related(
            'teachers', 'students', 'lectures'
        )

    def for_teacher(self, teacher):
        """Get courses where user is a teacher."""
        return self.filter(teachers=teacher)

    def for_student(self, student):
        """Get courses where user is a student."""
        return self.filter(students=student)

    def active(self):
        """Get active courses (can be extended with active field)."""
        return self.all()

    def by_title_contains(self, title: str):
        """Filter courses by title containing text."""
        return self.filter(title__icontains=title)


class LectureQuerySet(models.QuerySet):
    """Custom QuerySet for Lecture model."""

    def with_relations(self):
        """Prefetch related objects for efficient loading."""
        return self.select_related('course', 'created_by').prefetch_related(
            'assignments', 'assignments__submissions'
        )

    def for_course(self, course_id: int):
        """Get lectures for specific course."""
        return self.filter(course_id=course_id)

    def by_topic_contains(self, topic: str):
        """Filter lectures by topic containing text."""
        return self.filter(topic__icontains=topic)

    def with_presentations(self):
        """Get lectures that have presentations."""
        return self.exclude(presentation='')


class SubmissionQuerySet(models.QuerySet):
    """Custom QuerySet for Submission model."""

    def with_relations(self):
        """Prefetch related objects for efficient loading."""
        return self.select_related(
            'assignment', 'assignment__lecture', 'assignment__lecture__course', 'student'
        ).prefetch_related('grade', 'grade__comments')

    def for_student(self, student):
        """Get submissions by student."""
        return self.filter(student=student)

    def for_assignment(self, assignment_id: int):
        """Get submissions for specific assignment."""
        return self.filter(assignment_id=assignment_id)

    def graded(self):
        """Get submissions that have grades."""
        return self.filter(grade__isnull=False)

    def ungraded(self):
        """Get submissions that don't have grades."""
        return self.filter(grade__isnull=True)

    def for_course_teachers(self, teacher):
        """Get submissions visible to course teacher."""
        return self.filter(assignment__lecture__course__teachers=teacher)


class HomeworkAssignmentQuerySet(models.QuerySet):
    """Custom QuerySet for HomeworkAssignment model."""

    def with_relations(self):
        """Prefetch related objects for efficient loading."""
        return self.select_related(
            'lecture', 'lecture__course', 'created_by'
        ).prefetch_related('submissions', 'submissions__grade')

    def for_lecture(self, lecture_id: int):
        """Get assignments for specific lecture."""
        return self.filter(lecture_id=lecture_id)

    def with_due_dates(self):
        """Get assignments that have due dates."""
        return self.exclude(due_date__isnull=True)

    def overdue(self):
        """Get assignments that are overdue."""
        from django.utils import timezone
        return self.filter(due_date__lt=timezone.now())


class GradeQuerySet(models.QuerySet):
    """Custom QuerySet for Grade model."""

    def with_relations(self):
        """Prefetch related objects for efficient loading."""
        return self.select_related(
            'submission', 'submission__assignment', 'submission__student', 'graded_by'
        ).prefetch_related('comments')

    def for_student(self, student):
        """Get grades for specific student."""
        return self.filter(submission__student=student)

    def by_grader(self, grader):
        """Get grades created by specific teacher."""
        return self.filter(graded_by=grader)

    def high_scores(self, threshold: int = 80):
        """Get grades above threshold."""
        return self.filter(score__gte=threshold)

    def low_scores(self, threshold: int = 60):
        """Get grades below threshold."""
        return self.filter(score__lt=threshold)


class GradeCommentQuerySet(models.QuerySet):
    """Custom QuerySet for GradeComment model."""

    def with_relations(self):
        """Prefetch related objects for efficient loading."""
        return self.select_related(
            'grade', 'author', 'grade__submission', 'grade__submission__student'
        )

    def for_grade(self, grade_id: int):
        """Get comments for a specific grade."""
        return self.filter(grade_id=grade_id)

    def visible_to(self, user):
        """Get comments that are visible to the user, either because they are the student."""
        if user.is_anonymous:
            return self.none()

        student_condition = Q(grade__submission__student=user)
        teacher_condition = Q(grade__submission__assignment__lecture__course__teachers=user)

        return self.filter(student_condition | teacher_condition)