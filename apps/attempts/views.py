from datetime import datetime, timedelta

from django.db.models import Q, Avg
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from .models import Attempt, QuestionAttempt
from .serializers import AttemptSerializer, QuestionAttemptSerializer
from .permissions import AttemptBasedPermissions
from apps.assessments.models import Assessment, Question


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

    def perform_create(self, serializer):
        assessment_id = self.request.data.get("assessment")
        try:
            assessment = Assessment.objects.get(pk=assessment_id, is_active=True)
        except Assessment.DoesNotExist:
            raise ValidationError("The specified assessment does not exist or is not active.")
        if assessment.user == self.request.user:
            raise ValidationError("You cannot attempt your own assessment.")

        previous_attempts_count = Attempt.objects.filter(assessment=assessment, user=self.request.user).count()
        if previous_attempts_count >= assessment.allowed_attempts:
            raise ValidationError("You don't have any attempts left for this assessment.")

        serializer.save(user=self.request.user)

    def update_assessment_average_score(self, assessment):
        avg_score = Attempt.objects.filter(assessment=assessment, end_time__isnull=False).aggregate(
            avg_score=Avg("score")
        )["avg_score"]
        assessment.average_score = avg_score or 0
        assessment.save()

    @action(detail=True, methods=["POST"], url_path="finalize")
    def finalize_attempt(self, request, pk=None):
        attempt = self.get_object()
        attempt.end_time = datetime.now()

        expected_end_time = attempt.start_time + timedelta(minutes=attempt.assessment.time_limit)
        if attempt.end_time > expected_end_time:
            return Response(
                {"error": "The attempt exceeded the allowed time limit."}, status=status.HTTP_400_BAD_REQUEST
            )

        total_questions = attempt.assessment.number_of_questions
        correct_answers_count = attempt.question_attempts.filter(is_correct=True).count()
        attempt.score = (correct_answers_count / total_questions) * 100
        attempt.approved = attempt.score >= attempt.assessment.min_score
        attempt.save()

        self.update_assessment_average_score(attempt.assessment)

        return Response(
            {"detail": "Attempt finalized successfully.", "score": attempt.score, "approved": attempt.approved},
            status=status.HTTP_200_OK,
        )


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

    def perform_create(self, serializer):
        question = Question.objects.get(pk=self.request.data["question"])

        correct_choices_ids = set(question.choices.filter(correct_answer=True).values_list("id", flat=True))
        selected_choices_ids = set([int(choice_id) for choice_id in self.request.data["selected_choices"]])

        is_correct = correct_choices_ids == selected_choices_ids
        serializer.save(is_correct=is_correct)
