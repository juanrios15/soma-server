from django.contrib import admin

from .models import (
    Language,
    Category,
    Subcategory,
    Assessment,
    Question,
    Choice,
    AssessmentDifficultyRating,
    FollowAssessment,
)


@admin.register(Choice)
class Choicedmin(admin.ModelAdmin):
    list_display = ("id", "question", "description", "correct_answer")
    list_filter = ("question",)
    search_fields = ("question",)


admin.site.register(Language)
admin.site.register(Category)
admin.site.register(Subcategory)
admin.site.register(Assessment)
admin.site.register(Question)
admin.site.register(AssessmentDifficultyRating)
admin.site.register(FollowAssessment)
