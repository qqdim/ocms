from django.shortcuts import get_object_or_404
from rest_framework import decorators, permissions, response, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser

from courses.models import Course, GradeComment, HomeworkAssignment, Lecture, Submission
from courses.permissions import IsCourseStudentOrTeacherReadOnly, IsCourseTeacher, IsTeacher
from .serializers import (
    CourseSerializer,
    GradeCommentSerializer,
    GradeSerializer,
    HomeworkAssignmentSerializer,
    LectureSerializer,
    SubmissionSerializer,
    UserMiniSerializer,
)
from courses.services import (
    CourseService,
    GradingService,
)
from courses.exceptions import (
    CourseException,
    PermissionDeniedException,
    ValidationException,
    UserRoleException,
    AlreadyGradedException,
)


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet for managing courses."""

    queryset = Course.objects.with_relations().order_by("-created_at")
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
        if isinstance(e, (UserRoleException, ValidationException)):
            return response.Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(e, PermissionDeniedException):
            return response.Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        else:
            return response.Response({"detail": "An error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

    queryset = Lecture.objects.none()
    serializer_class = LectureSerializer
    parser_classes = (MultiPartParser, FormParser)

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsCourseTeacher()]
        if self.action in ["retrieve"]:
            return [permissions.IsAuthenticated(), IsCourseStudentOrTeacherReadOnly()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """Get queryset based on course filter."""
        course_id = self.request.query_params.get("course")
        if not course_id:
            return Lecture.objects.none()
        return Lecture.objects.for_course(course_id).with_relations().order_by("-created_at")


class HomeworkAssignmentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing homework assignments."""

    queryset = HomeworkAssignment.objects.none()
    serializer_class = HomeworkAssignmentSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsCourseTeacher()]
        if self.action in ["retrieve"]:
            return [permissions.IsAuthenticated(), IsCourseStudentOrTeacherReadOnly()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """Get queryset based on lecture filter."""
        lecture_id = self.request.query_params.get("lecture")
        if not lecture_id:
            return HomeworkAssignment.objects.none()
        return HomeworkAssignment.objects.for_lecture(lecture_id).with_relations().order_by("-created_at")


class SubmissionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing submissions."""

    queryset = Submission.objects.none()
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Get queryset based on user role and assignment filter."""
        user = self.request.user
        assignment_id = self.request.query_params.get("assignment")

        if user.is_teacher():
            queryset = Submission.objects.for_course_teachers(user)
        elif user.is_student():
            queryset = Submission.objects.for_student(user)
        else:
            return Submission.objects.none()

        if assignment_id:
            queryset = queryset.for_assignment(assignment_id)

        return queryset.with_relations().order_by("-submitted_at")

    def handle_service_exception(self, e):
        """Convert service exceptions to appropriate HTTP responses."""
        if isinstance(e, AlreadyGradedException):
            return response.Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        elif isinstance(e, PermissionDeniedException):
            return response.Response({"detail": str(e)}, status=status.HTTP_403_FORBIDDEN)
        else:
            return response.Response({"detail": "An error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @decorators.action(detail=True, methods=["get", "post", "patch"], url_path="grade")
    def grade(self, request, pk=None):
        """Handle grading actions for a submission."""
        submission = self.get_object()
        try:
            grade_instance = getattr(submission, "grade", None)
            if request.method.lower() == "get":
                if not GradingService.can_user_view_grade(grade_instance, request.user):
                    return response.Response({"detail": "Not allowed."}, status=403)
                return (
                    response.Response(GradeSerializer(grade_instance).data)
                    if grade_instance
                    else response.Response(status=204)
                )

            serializer_context = {"request": request}
            if request.method.lower() == "post":
                serializer = GradeSerializer(data=request.data, context=serializer_context)
            elif request.method.lower() == "patch":
                if not grade_instance:
                    return response.Response({"detail": "No grade exists to update."}, status=400)
                serializer = GradeSerializer(
                    grade_instance, data=request.data, partial=True, context=serializer_context
                )

            serializer.is_valid(raise_exception=True)
            grade = serializer.save(submission_id=submission.id) 
            return response.Response(GradeSerializer(grade).data)

        except CourseException as e:
            return self.handle_service_exception(e)


class GradeCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing grade comments."""

    queryset = GradeComment.objects.none()
    serializer_class = GradeCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Get queryset based on user visibility and grade filter."""
        user = self.request.user
        grade_id = self.request.query_params.get("grade")

        queryset = GradeComment.objects.visible_to(user)
        if grade_id:
            queryset = queryset.for_grade(grade_id)

        return queryset.with_relations().order_by("-created_at")
