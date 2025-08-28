from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

from courses.exceptions import (
    PermissionDeniedException,
    ValidationException,
    UserRoleException,
    AlreadyGradedException,
)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return response

    if isinstance(exc, PermissionDeniedException):
        return Response({"detail": str(exc)}, status=status.HTTP_403_FORBIDDEN)

    if isinstance(exc, (ValidationException, UserRoleException, AlreadyGradedException)):
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
