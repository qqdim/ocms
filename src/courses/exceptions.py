class CourseException(Exception):
    """Base exception for course-related errors."""
    pass


class PermissionDeniedException(CourseException):
    """Raised when user doesn't have required permissions."""
    pass


class ValidationException(CourseException):
    """Raised when business validation fails."""
    pass


class NotEnrolledException(CourseException):
    """Raised when user is not enrolled in course."""
    pass


class AlreadyGradedException(CourseException):
    """Raised when trying to modify already graded submission."""
    pass


class UserRoleException(CourseException):
    """Raised when user doesn't have required role."""
    pass
