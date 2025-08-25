import logging
from typing import Optional
from django.db.models import QuerySet

from ..models import HomeworkAssignment, Lecture

logger = logging.getLogger(__name__)


class HomeworkService:
    """Service class for homework assignment operations."""
    
    @staticmethod
    def create_homework_assignment(text: str, lecture: Lecture, created_by, due_date=None) -> HomeworkAssignment:
        """Create a new homework assignment."""

        logger.info(f"Creating homework assignment for lecture {lecture.id} by user {created_by.id}")
        assignment = HomeworkAssignment.objects.create(
            text=text,
            lecture=lecture,
            created_by=created_by,
            due_date=due_date
        )
        
        logger.info(f"Homework assignment {assignment.id} created successfully")
        return assignment
    
    @staticmethod
    def get_assignments_by_lecture(lecture_id: Optional[int] = None) -> QuerySet[HomeworkAssignment]:
        """Get homework assignments, optionally filtered by lecture."""

        queryset = HomeworkAssignment.objects.select_related("lecture", "lecture__course").all()
        if lecture_id:
            queryset = queryset.filter(lecture_id=lecture_id)
            
        return queryset.order_by("-created_at")
    
    @staticmethod
    def update_homework_assignment(assignment: HomeworkAssignment, **validated_data) -> HomeworkAssignment:
        """Update homework assignment with validated data."""

        logger.info(f"Updating homework assignment {assignment.id}")
        for field, value in validated_data.items():
            setattr(assignment, field, value)
        
        assignment.save()
        logger.info(f"Homework assignment {assignment.id} updated successfully")
        return assignment