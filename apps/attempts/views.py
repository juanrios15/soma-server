from rest_framework import viewsets

from .models import Attempt, QuestionAttempt
from .serializers import AttemptSerializer, QuestionAttemptSerializer
from .permissions import AttemptBasedPermissions


class AttemptViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AttemptBasedPermissions]
    queryset = Attempt.objects.all()
    serializer_class = AttemptSerializer
    filterset_fields = {
        "assessment": ("exact", "in"),
        "user": ("exact", "in"),
        "score": ("exact", "gte", "lte"),
        "approved": ("exact",),
    }


class QuestionAttemptViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AttemptBasedPermissions]
    queryset = QuestionAttempt.objects.all()
    serializer_class = QuestionAttemptSerializer
    filterset_fields = {
        "attempt": ("exact", "in"),
        "question": ("exact", "in"),
        "selected_choices": ("exact", "in"),
        "is_correct": ("exact",),
    }
