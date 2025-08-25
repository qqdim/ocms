from django.contrib.auth import get_user_model
from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, response, decorators, status
from rest_framework.parsers import MultiPartParser, FormParser

from .models import Course, Lecture, HomeworkAssignment, Submission, Grade, GradeComment
from .permissions import IsTeacher, IsCourseTeacher, IsCourseStudentOrTeacherReadOnly
from .serializers import (
    CourseSerializer, LectureSerializer, HomeworkAssignmentSerializer,
    SubmissionSerializer, GradeSerializer, GradeCommentSerializer, UserMiniSerializer
)

User = get_user_model()


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('-created_at')
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.IsAuthenticated(), IsTeacher()]
        if self.action in ['update', 'partial_update', 'destroy', 'add_student', 'remove_student', 'add_teacher']:
            return [permissions.IsAuthenticated(), IsCourseTeacher()]
        return [permissions.IsAuthenticated()]

    @decorators.action(detail=True, methods=['get'], url_path='students')
    def list_students(self, request, pk=None):
        course = self.get_object()
        return response.Response(UserMiniSerializer(course.students.all(), many=True).data)

    @decorators.action(detail=True, methods=['post'], url_path='students')
    def add_student(self, request, pk=None):
        course = self.get_object()
        student_id = request.data.get('student_id')
        student = get_object_or_404(User, id=student_id)
        if not student.is_student():
            return response.Response({'detail': 'User is not a student.'}, status=400)
        course.students.add(student)
        return response.Response({'detail': 'Student added.'})

    @decorators.action(detail=True, methods=['delete'], url_path='students/(?P<student_id>[^/.]+)')
    def remove_student(self, request, pk=None, student_id=None):
        course = self.get_object()
        student = get_object_or_404(User, id=student_id)
        course.students.remove(student)
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    @decorators.action(detail=True, methods=['get'], url_path='teachers')
    def list_teachers(self, request, pk=None):
        course = self.get_object()
        return response.Response(UserMiniSerializer(course.teachers.all(), many=True).data)

    @decorators.action(detail=True, methods=['post'], url_path='teachers')
    def add_teacher(self, request, pk=None):
        course = self.get_object()
        teacher_id = request.data.get('teacher_id')
        teacher = get_object_or_404(User, id=teacher_id)
        if not teacher.is_teacher():
            return response.Response({'detail': 'User is not a teacher.'}, status=400)
        course.teachers.add(teacher)
        return response.Response({'detail': 'Teacher added.'})


class LectureViewSet(viewsets.ModelViewSet):
    queryset = Lecture.objects.select_related('course').all()
    serializer_class = LectureSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsCourseTeacher()]
        if self.action in ['retrieve']:
            return [permissions.IsAuthenticated(), IsCourseStudentOrTeacherReadOnly()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        course_id = self.request.query_params.get('course')
        if course_id:
            qs = qs.filter(course_id=course_id)
        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class HomeworkAssignmentViewSet(viewsets.ModelViewSet):
    queryset = HomeworkAssignment.objects.select_related('lecture', 'lecture__course').all()
    serializer_class = HomeworkAssignmentSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsCourseTeacher()]
        if self.action in ['retrieve']:
            return [permissions.IsAuthenticated(), IsCourseStudentOrTeacherReadOnly()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        lecture_id = self.request.query_params.get('lecture')
        if lecture_id:
            qs = qs.filter(lecture_id=lecture_id)
        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SubmissionViewSet(viewsets.ModelViewSet):
    queryset = Submission.objects.select_related('assignment', 'assignment__lecture__course').all()
    serializer_class = SubmissionSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        assignment_id = self.request.query_params.get('assignment')
        if assignment_id:
            qs = qs.filter(assignment_id=assignment_id)
        if hasattr(user, 'is_student') and user.is_student():
            qs = qs.filter(student=user)
        elif hasattr(user, 'is_teacher') and user.is_teacher():
            qs = qs.filter(assignment__lecture__course__teachers=user)
        else:
            qs = qs.none()
        return qs.order_by('-submitted_at')

    def perform_update(self, serializer):
        instance = self.get_object()
        if hasattr(instance, 'grade'):
            raise PermissionError('Submission already graded; cannot modify.')
        if instance.student_id != self.request.user.id:
            raise PermissionError('Cannot modify others\' submissions.')
        serializer.save()

    @decorators.action(detail=True, methods=['get', 'post', 'patch'], url_path='grade')
    def grade(self, request, pk=None):
        submission = self.get_object()
        course = submission.assignment.lecture.course
        if request.method.lower() in ['post', 'patch']:
            if not course.teachers.filter(id=request.user.id).exists():
                return response.Response({'detail': 'Only course teachers can grade.'}, status=403)
        if request.method.lower() == 'get':
            if submission.student_id != request.user.id and not course.teachers.filter(id=request.user.id).exists():
                return response.Response({'detail': 'Not allowed.'}, status=403)
            if hasattr(submission, 'grade'):
                return response.Response(GradeSerializer(submission.grade).data)
            return response.Response(status=204)
        data = request.data.copy()
        data['submission_id'] = submission.id
        if hasattr(submission, 'grade') and request.method.lower() == 'patch':
            ser = GradeSerializer(submission.grade, data=data, partial=True, context={'request': request})
        elif hasattr(submission, 'grade') and request.method.lower() == 'post':
            return response.Response({'detail': 'Grade already exists. Use PATCH.'}, status=400)
        else:
            ser = GradeSerializer(data=data, context={'request': request})
        ser.is_valid(raise_exception=True)
        grade = ser.save()
        return response.Response(GradeSerializer(grade).data)


class GradeCommentViewSet(viewsets.ModelViewSet):
    queryset = GradeComment.objects.select_related('grade', 'author', 'grade__submission__assignment__lecture__course')
    serializer_class = GradeCommentSerializer

    def get_permissions(self):
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        grade_id = self.request.query_params.get('grade')
        if grade_id:
            qs = qs.filter(grade_id=grade_id)
        user = self.request.user
        return qs.filter(
            models.Q(grade__submission__assignment__lecture__course__teachers=user)
            | models.Q(grade__submission__student=user)
        ).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
