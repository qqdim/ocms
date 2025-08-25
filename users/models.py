from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        TEACHER = 'TEACHER', 'Teacher'
        STUDENT = 'STUDENT', 'Student'

    role = models.CharField(max_length=7, choices=Roles.choices)

    def is_teacher(self):
        return self.role == self.Roles.TEACHER

    def is_student(self):
        return self.role == self.Roles.STUDENT
