from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from users.services.user_service import UserService

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "role")

    def validate_password(self, value):
        """Validate the password using Django's password validation."""
        validate_password(value)
        return value

    def create(self, validated_data):
        """Delegate user creation to the UserService."""

        try:
            return UserService.create_user(**validated_data)
        except ValueError as e:
            raise serializers.ValidationError(str(e))


class UserPublicSerializer(serializers.ModelSerializer):
    """Serializer for public user details."""

    class Meta:
        """Meta information for UserPublicSerializer."""

        model = User
        fields = ("id", "username", "email", "role")
