from django.db.models import Q
from rest_framework import viewsets

from .models import Attempt, QuestionAttempt
from .serializers import AttemptSerializer, QuestionAttemptSerializer
from .permissions import AttemptBasedPermissions


class AttemptViewSet(viewsets.ModelViewSet):
    permission_classes = [AttemptBasedPermissions]
    serializer_class = AttemptSerializer
    filterset_fields = {
        "assessment": ("exact", "in"),
        "user": ("exact", "in"),
        "score": ("exact", "gte", "lte"),
        "approved": ("exact",),
    }

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Attempt.objects.filter(Q(user=self.request.user) | Q(assessment__user=self.request.user))
        return Attempt.objects.none()


class QuestionAttemptViewSet(viewsets.ModelViewSet):
    permission_classes = [AttemptBasedPermissions]
    queryset = QuestionAttempt.objects.all()
    serializer_class = QuestionAttemptSerializer
    filterset_fields = {
        "attempt": ("exact", "in"),
        "question": ("exact", "in"),
        "selected_choices": ("exact", "in"),
        "is_correct": ("exact",),
    }

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return QuestionAttempt.objects.filter(
                Q(attempt__user=self.request.user) | Q(attempt__assessment__user=self.request.user)
            )
        return QuestionAttempt.objects.none()
