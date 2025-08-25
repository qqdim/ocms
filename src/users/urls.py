from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import MeView, RegisterView

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("jwt/create", TokenObtainPairView.as_view(), name="jwt-create"),
    path("jwt/refresh", TokenRefreshView.as_view(), name="jwt-refresh"),
    path("me", MeView.as_view(), name="me"),
]
