from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Course, Grade, GradeComment, HomeworkAssignment, Lecture, Submission
from .services import (
    CourseService,
    LectureService,
    HomeworkService,
    SubmissionService,
    GradingService,
)

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    """Serializer for minimal user details."""

    class Meta:
        """Meta information for UserMiniSerializer."""

        model = User
        fields = ("id", "username", "role")
        read_only_fields = ["created_by"]


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for course details."""

    teachers = UserMiniSerializer(many=True, read_only=True)
    students = UserMiniSerializer(many=True, read_only=True)
    created_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "description",
            "created_by",
            "teachers",
            "students",
            "created_at",
        )

    def create(self, validated_data):
        """Create course using service layer."""

        user = self.context["request"].user
        return CourseService.create_course(
            title=validated_data["title"], description=validated_data.get("description", ""), created_by=user
        )


class LectureSerializer(serializers.ModelSerializer):
    """Serializer for lecture details."""

    course_id = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), source="course", write_only=True)
    created_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = Lecture
        fields = (
            "id",
            "topic",
            "presentation",
            "course_id",
            "created_by",
            "created_at",
        )
        read_only_fields = ("created_by", "created_at")

    def create(self, validated_data):
        """Create lecture using service layer."""

        user = self.context["request"].user
        return LectureService.create_lecture(
            topic=validated_data["topic"],
            course=validated_data["course"],
            created_by=user,
            presentation=validated_data.get("presentation"),
        )

    def update(self, instance, validated_data):
        """Update lecture using service layer."""

        return LectureService.update_lecture(instance, **validated_data)


class HomeworkAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for homework assignment details."""

    lecture_id = serializers.PrimaryKeyRelatedField(queryset=Lecture.objects.all(), source="lecture", write_only=True)
    created_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = HomeworkAssignment
        fields = ("id", "lecture_id", "text", "due_date", "created_by", "created_at")

    def create(self, validated_data):
        """Create homework assignment using service layer."""

        user = self.context["request"].user
        return HomeworkService.create_homework_assignment(
            text=validated_data["text"],
            lecture=validated_data["lecture"],
            created_by=user,
            due_date=validated_data.get("due_date"),
        )

    def update(self, instance, validated_data):
        """Update homework assignment using service layer."""

        return HomeworkService.update_homework_assignment(instance, **validated_data)


class SubmissionSerializer(serializers.ModelSerializer):
    """Serializer for submission details."""

    assignment_id = serializers.PrimaryKeyRelatedField(
        queryset=HomeworkAssignment.objects.all(), source="assignment", write_only=True
    )
    student = UserMiniSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = (
            "id",
            "assignment_id",
            "student",
            "text",
            "attachment",
            "submitted_at",
        )
        read_only_fields = ("student", "submitted_at")

    def create(self, validated_data):
        """Create submission using service layer."""

        user = self.context["request"].user
        return SubmissionService.create_submission(
            assignment=validated_data["assignment"],
            student=user,
            text=validated_data.get("text", ""),
            attachment=validated_data.get("attachment"),
        )

    def update(self, instance, validated_data):
        """Update submission using service layer."""

        user = self.context["request"].user
        return SubmissionService.update_submission(instance, user, **validated_data)


class GradeSerializer(serializers.ModelSerializer):
    """Serializer for grade details."""

    submission_id = serializers.PrimaryKeyRelatedField(
        queryset=Submission.objects.all(), source="submission", write_only=True
    )
    graded_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = Grade
        fields = ("id", "submission_id", "score", "comment", "graded_by", "graded_at")

    def create(self, validated_data):
        """Create grade using service layer."""

        user = self.context["request"].user
        return GradingService.create_grade(
            submission=validated_data["submission"],
            score=validated_data["score"],
            graded_by=user,
            comment=validated_data.get("comment", ""),
        )

    def update(self, instance, validated_data):
        """Update grade using service layer."""

        user = self.context["request"].user
        return GradingService.update_grade(instance, user, **validated_data)


class GradeCommentSerializer(serializers.ModelSerializer):
    """Serializer for grade comment details."""

    author = UserMiniSerializer(read_only=True)

    class Meta:
        model = GradeComment
        fields = ("id", "grade", "author", "text", "created_at")
        read_only_fields = ("author", "created_at")

    def create(self, validated_data):
        """Create grade comment using service layer."""

        user = self.context["request"].user
        return GradingService.create_grade_comment(
            grade=validated_data["grade"], author=user, text=validated_data["text"]
        )
