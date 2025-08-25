from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Course, Lecture, HomeworkAssignment, Submission, Grade, GradeComment

User = get_user_model()


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'role')
        read_only_fields = ['created_by']


class CourseSerializer(serializers.ModelSerializer):
    teachers = UserMiniSerializer(many=True, read_only=True)
    students = UserMiniSerializer(many=True, read_only=True)
    created_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = Course
        fields = ('id', 'title', 'description', 'created_by', 'teachers', 'students', 'created_at')

    def create(self, validated_data):
        user = self.context['request'].user
        course = Course.objects.create(created_by=user, **validated_data)
        course.teachers.add(user)
        return course


class LectureSerializer(serializers.ModelSerializer):
    course_id = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), source='course', write_only=True)
    created_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = Lecture
        fields = ('id', 'topic', 'presentation', 'course_id', 'created_by', 'created_at')
        read_only_fields = ('created_by', 'created_at')

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class HomeworkAssignmentSerializer(serializers.ModelSerializer):
    lecture_id = serializers.PrimaryKeyRelatedField(queryset=Lecture.objects.all(), source='lecture', write_only=True)
    created_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = HomeworkAssignment
        fields = ('id', 'lecture_id', 'text', 'due_date', 'created_by', 'created_at')

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class SubmissionSerializer(serializers.ModelSerializer):
    assignment_id = serializers.PrimaryKeyRelatedField(queryset=HomeworkAssignment.objects.all(), source='assignment',
                                                       write_only=True)
    student = UserMiniSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = ('id', 'assignment_id', 'student', 'text', 'attachment', 'submitted_at')
        read_only_fields = ('student', 'submitted_at')

    def validate(self, attrs):
        request = self.context['request']
        assignment = attrs['assignment']
        course = assignment.lecture.course
        if not course.students.filter(id=request.user.id).exists():
            raise serializers.ValidationError('You are not enrolled in this course.')
        return attrs

    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        return super().create(validated_data)


class GradeSerializer(serializers.ModelSerializer):
    submission_id = serializers.PrimaryKeyRelatedField(queryset=Submission.objects.all(), source='submission',
                                                       write_only=True)
    graded_by = UserMiniSerializer(read_only=True)

    class Meta:
        model = Grade
        fields = ('id', 'submission_id', 'score', 'comment', 'graded_by', 'graded_at')

    def validate(self, attrs):
        request = self.context['request']
        submission = attrs['submission']
        course = submission.assignment.lecture.course
        if not course.teachers.filter(id=request.user.id).exists():
            raise serializers.ValidationError('Only a course teacher can grade this submission.')
        return attrs

    def create(self, validated_data):
        validated_data['graded_by'] = self.context['request'].user
        return super().create(validated_data)


class GradeCommentSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)

    class Meta:
        model = GradeComment
        fields = ('id', 'grade', 'author', 'text', 'created_at')
        read_only_fields = ('author', 'created_at')

    def validate(self, attrs):
        user = self.context['request'].user
        grade = attrs['grade']
        course = grade.submission.assignment.lecture.course
        is_teacher = course.teachers.filter(id=user.id).exists()
        is_student_owner = grade.submission.student_id == user.id
        if not (is_teacher or is_student_owner):
            raise serializers.ValidationError('Only course teachers or the submission owner can comment.')
        return attrs

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)
