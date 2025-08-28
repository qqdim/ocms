from django.urls import include, path

urlpatterns = [
    path("auth/", include("api.v1.authentication.urls")),
    path("users/", include("api.v1.users.urls")),
    path("", include("api.v1.courses.urls")),
]
