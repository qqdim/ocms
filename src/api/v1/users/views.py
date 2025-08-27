from django.contrib.auth import get_user_model
from rest_framework import generics, permissions

from .serializers import RegisterSerializer, UserPublicSerializer

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """API view for user registration."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    """API view for retrieving the current user's details."""

    serializer_class = UserPublicSerializer

    def get_object(self):
        return self.request.user
