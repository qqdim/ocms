from django.contrib import admin

from .models import Course, Grade, GradeComment, HomeworkAssignment, Lecture, Submission

admin.site.register(Course)
admin.site.register(Lecture)
admin.site.register(HomeworkAssignment)
admin.site.register(Submission)
admin.site.register(Grade)
admin.site.register(GradeComment)
