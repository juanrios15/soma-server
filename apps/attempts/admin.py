from django.contrib import admin

from .models import Attempt, QuestionAttempt


admin.site.register(Attempt)
admin.site.register(QuestionAttempt)
