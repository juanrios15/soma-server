from django.urls import path, include
from rest_framework import routers

from .views import (
    CategoryViewSet,
    SubcategoryViewSet,
    AssessmentViewSet,
    QuestionViewSet,
    ChoiceViewSet,
    AssessmentDifficultyRatingViewSet,
)


app_name = "assessments"

router = routers.DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="categories")
router.register(r"subcategories", SubcategoryViewSet, basename="subcategories")
router.register(r"assessments", AssessmentViewSet, basename="assessments")
router.register(r"questions", QuestionViewSet, basename="questions")
router.register(r"choice", ChoiceViewSet, basename="choice")
router.register(r"assessmentdifficulty", AssessmentDifficultyRatingViewSet, basename="assessmentdifficulty")


urlpatterns = [
    path("", include(router.urls)),
]
