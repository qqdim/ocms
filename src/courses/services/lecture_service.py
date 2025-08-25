import logging
from typing import Optional
from django.db.models import QuerySet

from ..models import Lecture, Course

logger = logging.getLogger(__name__)


class LectureService:
    """Service class for lecture-related operations."""
    
    @staticmethod
    def create_lecture(topic: str, course: Course, created_by, presentation=None) -> Lecture:
        """Create a new lecture."""

        logger.info(f"Creating lecture '{topic}' for course {course.id} by user {created_by.id}")
        lecture = Lecture.objects.create(
            topic=topic,
            course=course,
            created_by=created_by,
            presentation=presentation
        )
        
        logger.info(f"Lecture {lecture.id} created successfully")
        return lecture
    
    @staticmethod
    def get_lectures_by_course(course_id: Optional[int] = None) -> QuerySet[Lecture]:
        """Get lectures, optionally filtered by course."""

        queryset = Lecture.objects.select_related("course").all()
        if course_id:
            queryset = queryset.filter(course_id=course_id)
            
        return queryset.order_by("-created_at")
    
    @staticmethod
    def update_lecture(lecture: Lecture, **validated_data) -> Lecture:
        """Update lecture with validated data."""

        logger.info(f"Updating lecture {lecture.id}")
        for field, value in validated_data.items():
            setattr(lecture, field, value)
        
        lecture.save()
        logger.info(f"Lecture {lecture.id} updated successfully")
        return lecture
