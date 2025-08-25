from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = settings.AUTH_USER_MODEL


class Course(models.Model):
    """Model representing a course with title, description, and participants."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_courses")
    teachers = models.ManyToManyField(User, related_name="teaching_courses", blank=True)
    students = models.ManyToManyField(User, related_name="enrolled_courses", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return string representation of the course."""
        return self.title


class Lecture(models.Model):
    """Model representing a lecture within a course."""

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lectures")
    topic = models.CharField(max_length=255)
    presentation = models.FileField(upload_to="presentations/", blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return string representation of the lecture."""
        return f"{self.course.title} — {self.topic}"


class HomeworkAssignment(models.Model):
    """Model representing a homework assignment for a lecture."""

    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name="assignments")
    text = models.TextField()
    due_date = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return string representation of the homework assignment."""
        return f"HW for {self.lecture.topic}"


class Submission(models.Model):
    """Model representing a submission for a homework assignment."""

    assignment = models.ForeignKey(HomeworkAssignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    attachment = models.FileField(upload_to="submissions/", blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("assignment", "student")

    def __str__(self):
        """Return string representation of the submission."""
        return f"Submission {self.id} by {self.student}"


class Grade(models.Model):
    """Model representing a grade for a submission."""

    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name="grade")
    score = models.PositiveSmallIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    comment = models.TextField(blank=True)
    graded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    graded_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        """Return string representation of the grade."""
        return f"Grade {self.score} for submission {self.submission_id}"


class GradeComment(models.Model):
    """Model representing a comment on a grade."""

    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return string representation of the grade comment."""
        return f"Comment by {self.author} on grade {self.grade_id}"
