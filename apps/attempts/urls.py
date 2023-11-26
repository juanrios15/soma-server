from django.urls import path, include
from rest_framework import routers

from .views import AttemptViewSet, QuestionAttemptViewSet, GlobalStatsAPIView


app_name = "attempts"

router = routers.DefaultRouter()
router.register(r"attempts", AttemptViewSet, basename="attempts")
router.register(r"question_attempts", QuestionAttemptViewSet, basename="question_attempts")


urlpatterns = [
    path("", include(router.urls)),
    path('global_stats/', GlobalStatsAPIView.as_view(), name='global_stats'),
]
