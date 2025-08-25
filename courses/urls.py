from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CourseViewSet, LectureViewSet, HomeworkAssignmentViewSet, SubmissionViewSet, GradeCommentViewSet

router = DefaultRouter()
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'lectures', LectureViewSet, basename='lecture')
router.register(r'assignments', HomeworkAssignmentViewSet, basename='assignment')
router.register(r'submissions', SubmissionViewSet, basename='submission')
router.register(r'grade-comments', GradeCommentViewSet, basename='grade-comment')

urlpatterns = [
    path('', include(router.urls)),
]
