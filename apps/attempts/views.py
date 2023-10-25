import random
from datetime import datetime, timedelta

from django.db.models import Q, Avg, Prefetch, Max
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from .models import Attempt, QuestionAttempt
from .serializers import AttemptSerializer, QuestionAttemptSerializer
from .permissions import AttemptBasedPermissions
from apps.assessments.models import Assessment, Question, Choice
from apps.users.models import UserPoints


class AttemptViewSet(viewsets.ModelViewSet):
    permission_classes = [AttemptBasedPermissions]
    serializer_class = AttemptSerializer
    filterset_fields = {
        "assessment": ("exact", "in"),
        "user": ("exact", "in"),
        "score": ("exact", "gte", "lte"),
        "approved": ("exact",),
        "start_time": ("exact", "gte", "lte"),
    }
    ordering_fields = ["start_time"]
    ordering = ["start_time"]

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
        assessment.attempts_count = Attempt.objects.filter(assessment=assessment).count() + 1
        self.update_assessment_average_score(assessment)
        self.update_user_average_score(self.request.user)
        serializer.save(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        # Getting random questions for attempt:
        if request.user == instance.user and not instance.questions_provided:
            assessment = instance.assessment
            number_of_questions = assessment.number_of_questions
            random_questions = Question.objects.filter(assessment=assessment).order_by("?")[:number_of_questions]
            random_questions_with_choices = random_questions.prefetch_related(
                Prefetch("choices", queryset=Choice.objects.all(), to_attr="fetched_choices")
            )
            questions_data = [
                {
                    "question_id": q.id,
                    "description": q.description,
                    "choices": [
                        {"choice_id": c.id, "description": c.description}
                        for c in random.sample(q.fetched_choices, len(q.fetched_choices))
                    ],
                }
                for q in random_questions_with_choices
            ]
            response_data = serializer.data
            response_data["questions"] = questions_data
            instance.questions_provided = True
            instance.save(update_fields=["questions_provided"])
            return Response(response_data)
        return Response(serializer.data)

    def update_assessment_average_score(self, assessment):
        avg_score = Attempt.objects.filter(assessment=assessment).aggregate(avg_score=Avg("score"))["avg_score"]
        assessment.average_score = avg_score or 0
        assessment.save()

    def update_user_average_score(self, user):
        """
        Update the user's average score based on the best score for each assessment.
        """
        best_scores = Attempt.objects.filter(user=user).values("assessment").annotate(best_score=Max("score"))
        average_score = best_scores.aggregate(avg_best_score=Avg("best_score"))["avg_best_score"] or 0
        user.average_score = average_score
        user.save()

    def calculate_points(self, assessment, score):
        """Helper function to calculate points based on the formula."""
        D_teacher = assessment.difficulty
        D_students = assessment.user_difficulty_rating or D_teacher
        return score * ((D_teacher + D_students) / 20.0)

    @action(detail=True, methods=["POST"])
    def finalize_attempt(self, request, pk=None):
        attempt = self.get_object()
        attempt.end_time = timezone.now()

        expected_end_time = attempt.start_time + timedelta(minutes=attempt.assessment.time_limit, seconds=5)
        if attempt.end_time > expected_end_time:
            return Response(
                {"error": "The attempt exceeded the allowed time limit."}, status=status.HTTP_400_BAD_REQUEST
            )
        if not isinstance(request.data, list):
            return Response({"error": "Expected a list of answers."}, status=status.HTTP_400_BAD_REQUEST)
        answers = request.data
        question_attempts_to_create = []
        for answer in answers:
            question_id = answer.get("question_id")
            selected_choices = set(answer.get("choices", []))

            try:
                question = Question.objects.get(pk=question_id)
            except Question.DoesNotExist:
                return Response(
                    {"error": f"Question with id {question_id} does not exist."}, status=status.HTTP_400_BAD_REQUEST
                )
            correct_choices_ids = set(question.choices.filter(correct_answer=True).values_list("id", flat=True))
            is_correct = correct_choices_ids == selected_choices

            question_attempts_to_create.append(
                QuestionAttempt(attempt=attempt, question_id=question_id, is_correct=is_correct)
            )
        QuestionAttempt.objects.bulk_create(question_attempts_to_create)

        for qa, answer in zip(question_attempts_to_create, answers):
            qa.selected_choices.set(answer.get("choices", []))

        # Calculating score:
        total_questions = attempt.assessment.number_of_questions
        correct_answers_count = attempt.question_attempts.filter(is_correct=True).count()
        attempt.score = (correct_answers_count / total_questions) * 100
        attempt.approved = attempt.score >= attempt.assessment.min_score
        # Calculating points:
        attempt.points_obtained = self.calculate_points(attempt.assessment, attempt.score)
        best_attempt = (
            Attempt.objects.filter(assessment=attempt.assessment, user=request.user)
            .exclude(pk=attempt.pk)
            .order_by("-points_obtained")
            .first()
        )
        user_points, created = UserPoints.objects.get_or_create(
            user=attempt.user, category=attempt.assessment.subcategory.category, defaults={"total_points": 0}
        )
        if not best_attempt or attempt.points_obtained > best_attempt.points_obtained:
            if best_attempt:
                difference = attempt.points_obtained - best_attempt.points_obtained
                attempt.user.points += difference
                user_points.total_points += difference
            else:
                attempt.user.points += attempt.points_obtained
                user_points.total_points += attempt.points_obtained
            attempt.user.save()
            user_points.save()
        attempt.is_finished = True
        attempt.save()
        self.update_user_average_score(attempt.user)
        self.update_assessment_average_score(attempt.assessment)
        return Response(
            {
                "detail": "Attempt finalized successfully.",
                "score": attempt.score,
                "approved": attempt.approved,
                "points_obtained": attempt.points_obtained,
            },
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
            return QuestionAttempt.objects.filter(attempt__assessment__user=self.request.user)
        return QuestionAttempt.objects.none()

    def perform_create(self, serializer):
        question = Question.objects.get(pk=self.request.data["question"])

        # Checking if answer is correct:
        correct_choices_ids = set(question.choices.filter(correct_answer=True).values_list("id", flat=True))
        selected_choices_ids = set([int(choice_id) for choice_id in self.request.data["selected_choices"]])

        is_correct = correct_choices_ids == selected_choices_ids
        serializer.save(is_correct=is_correct)
