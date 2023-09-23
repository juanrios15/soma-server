from django.contrib import admin

from .models import Category, Subcategory, Assessment, Question, Choice, AssessmentDifficultyRating, FollowAssessment


admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(Assessment)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(AssessmentDifficultyRating)
admin.site.register(FollowAssessment)
