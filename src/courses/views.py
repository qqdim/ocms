from django.shortcuts import get_object_or_404
from rest_framework import decorators, permissions, response, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser

from .models import Course, GradeComment, HomeworkAssignment, Lecture, Submission
from .permissions import IsCourseStudentOrTeacherReadOnly, IsCourseTeacher, IsTeacher
from .serializers import (
    CourseSerializer,
    GradeCommentSerializer,
    GradeSerializer,
    HomeworkAssignmentSerializer,
    LectureSerializer,
    SubmissionSerializer,
    UserMiniSerializer,
)
from .services import (
    CourseService,
    LectureService,
    HomeworkService,
    SubmissionService,
    GradingService,
)
from .exceptions import (
    CourseException,
    PermissionDeniedException,
    ValidationException,
    UserRoleException,
    NotEnrolledException,
    AlreadyGradedException,
)


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet for managing courses."""

    queryset = Course.objects.all().order_by("-created_at")
    serializer_class = CourseSerializer

    def get_permissions(self):
        """Get permissions based on the action."""
        if self.action in ["create"]:
            return [permissions.IsAuthenticated(), IsTeacher()]
        if self.action in [
            "update",
            "partial_update",
            "destroy",
            "add_student",
            "remove_student",
            "add_teacher",
        ]:
            return [permissions.IsAuthenticated(), IsCourseTeacher()]
        return [permissions.IsAuthenticated()]

    def handle_service_exception(self, e):
        """Convert service exceptions to appropriate HTTP responses."""

        if isinstance(e, UserRoleException):
            return response.Response({"detail": str(e)}, status=400)
        elif isinstance(e, ValidationException):
            return response.Response({"detail": str(e)}, status=400)
        elif isinstance(e, PermissionDeniedException):
            return response.Response({"detail": str(e)}, status=403)
        else:
            return response.Response({"detail": "An error occurred."}, status=500)

    @decorators.action(detail=True, methods=["get"], url_path="students")
    def list_students(self, request, pk=None):
        """List all students in the course."""
        course = self.get_object()
        students = CourseService.get_course_students(course)
        return response.Response(UserMiniSerializer(students, many=True).data)

    @decorators.action(detail=True, methods=["post"], url_path="students")
    def add_student(self, request, pk=None):
        """Add a student to the course."""
        course = self.get_object()
        student_id = request.data.get("student_id")
        
        try:
            CourseService.add_student_to_course(course, student_id)
            return response.Response({"detail": "Student added."})
        except CourseException as e:
            return self.handle_service_exception(e)

    @decorators.action(detail=True, methods=["delete"], url_path="students/(?P<student_id>[^/.]+)")
    def remove_student(self, request, pk=None, student_id=None):
        """Remove a student from the course."""
        course = self.get_object()
        
        try:
            CourseService.remove_student_from_course(course, student_id)
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        except CourseException as e:
            return self.handle_service_exception(e)

    @decorators.action(detail=True, methods=["get"], url_path="teachers")
    def list_teachers(self, request, pk=None):
        """List all teachers in the course."""
        course = self.get_object()
        teachers = CourseService.get_course_teachers(course)
        return response.Response(UserMiniSerializer(teachers, many=True).data)

    @decorators.action(detail=True, methods=["post"], url_path="teachers")
    def add_teacher(self, request, pk=None):
        """Add a teacher to the course."""
        course = self.get_object()
        teacher_id = request.data.get("teacher_id")
        
        try:
            CourseService.add_teacher_to_course(course, teacher_id)
            return response.Response({"detail": "Teacher added."})
        except CourseException as e:
            return self.handle_service_exception(e)


class LectureViewSet(viewsets.ModelViewSet):
    """ViewSet for managing lectures."""

    queryset = Lecture.objects.select_related("course").all()
    serializer_class = LectureSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_permissions(self):
        """Get permissions based on the action."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsCourseTeacher()]
        if self.action in ["retrieve"]:
            return [permissions.IsAuthenticated(), IsCourseStudentOrTeacherReadOnly()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """Get queryset based on course filter."""
        course_id = self.request.query_params.get("course")
        return LectureService.get_lectures_by_course(course_id)

    def perform_create(self, serializer):
        """Save the lecture instance."""
        serializer.save()


class HomeworkAssignmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing homework assignments."""

    queryset = HomeworkAssignment.objects.select_related("lecture", "lecture__course").all()
    serializer_class = HomeworkAssignmentSerializer

    def get_permissions(self):
        """Get permissions based on the action."""
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsCourseTeacher()]
        if self.action in ["retrieve"]:
            return [permissions.IsAuthenticated(), IsCourseStudentOrTeacherReadOnly()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """Get queryset based on lecture filter."""
        lecture_id = self.request.query_params.get("lecture")
        return HomeworkService.get_assignments_by_lecture(lecture_id)

    def perform_create(self, serializer):
        """Save the homework assignment instance."""
        serializer.save()


class SubmissionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing submissions."""

    queryset = Submission.objects.select_related("assignment", "assignment__lecture__course").all()
    serializer_class = SubmissionSerializer

    def get_permissions(self):
        """Get permissions for the viewset."""
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """Get queryset based on assignment filter."""
        assignment_id = self.request.query_params.get("assignment")
        return SubmissionService.get_submissions_for_user(self.request.user, assignment_id)

    def perform_update(self, serializer):
        """Save the updated submission instance."""
        serializer.save()

    def handle_service_exception(self, e):
        """Convert service exceptions to appropriate HTTP responses."""

        if isinstance(e, AlreadyGradedException):
            return response.Response({"detail": str(e)}, status=400)
        elif isinstance(e, PermissionDeniedException):
            return response.Response({"detail": str(e)}, status=403)
        else:
            return response.Response({"detail": "An error occurred."}, status=500)

    @decorators.action(detail=True, methods=["get", "post", "patch"], url_path="grade")
    def grade(self, request, pk=None):
        """Handle grading actions for a submission."""
        submission = self.get_object()
        
        try:
            if request.method.lower() == "get":
                if not GradingService.can_user_view_grade(submission.grade if hasattr(submission, "grade") else None, request.user):
                    return response.Response({"detail": "Not allowed."}, status=403)
                
                if hasattr(submission, "grade"):
                    return response.Response(GradeSerializer(submission.grade).data)
                return response.Response(status=204)
            
            elif request.method.lower() == "post":
                data = request.data.copy()
                data["submission_id"] = submission.id
                
                serializer = GradeSerializer(data=data, context={"request": request})
                serializer.is_valid(raise_exception=True)
                grade = serializer.save()
                return response.Response(GradeSerializer(grade).data)
            
            elif request.method.lower() == "patch":
                if not hasattr(submission, "grade"):
                    return response.Response({"detail": "No grade exists to update."}, status=400)
                
                data = request.data.copy()
                serializer = GradeSerializer(submission.grade, data=data, partial=True, context={"request": request})
                serializer.is_valid(raise_exception=True)
                grade = serializer.save()
                return response.Response(GradeSerializer(grade).data)
                
        except CourseException as e:
            return self.handle_service_exception(e)


class GradeCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing grade comments."""

    queryset = GradeComment.objects.select_related("grade", "author", "grade__submission__assignment__lecture__course")
    serializer_class = GradeCommentSerializer

    def get_permissions(self):
        """Get permissions for the viewset."""
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """Get queryset based on grade filter."""
        grade_id = self.request.query_params.get("grade")
        return GradingService.get_grade_comments_for_user(self.request.user, grade_id)

    def perform_create(self, serializer):
        """Save the grade comment instance."""
        serializer.save()