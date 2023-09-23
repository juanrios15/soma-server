from django.db.models import Q, Count, Avg, Case, When, IntegerField
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from .models import Category, Subcategory, Assessment, Question, Choice, AssessmentDifficultyRating, FollowAssessment
from .serializers import (
    CategorySerializer,
    SubcategorySerializer,
    AssessmentSerializer,
    AssessmentDetailSerializer,
    QuestionSerializer,
    ChoiceSerializer,
    AssessmentDifficultyRatingSerializer,
    FollowAssessmentSerializer,
)
from .permissions import AssessmentPermissions, QuestionChoicePermissions, FollowAssessmentPermissions
from apps.attempts.models import Attempt


def validate_question(question):
    total_choices = question.choices.count()
    correct_choices = question.choices.filter(correct_answer=True).count()
    if question.is_multiple_choice:
        if total_choices < 3:
            return "The question should have at least 3 choices."
        if correct_choices < 2:
            return "The question should have at least 2 correct choices."
    else:
        if total_choices < 2:
            return "The question should have at least 2 choices."
        if correct_choices != 1:
            return "The question should have only 1 correct choice."
    return None


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filterset_fields = {
        "name": ("exact", "icontains"),
    }


class SubcategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Subcategory.objects.all()
    serializer_class = SubcategorySerializer
    filterset_fields = {
        "category": ("exact", "in"),
        "name": ("exact", "icontains"),
    }


class AssessmentViewSet(viewsets.ModelViewSet):
    permission_classes = [AssessmentPermissions]
    serializer_class = AssessmentSerializer
    filterset_fields = {
        "name": ("exact", "icontains"),
        "user": ("exact", "in"),
        "subcategory": ("exact", "in"),
        "number_of_questions": ("exact", "gte", "lte"),
        "allowed_attempts": ("exact", "gte", "lte"),
        "time_limit": ("exact", "gte", "lte"),
        "difficulty": ("exact", "gte", "lte"),
        "user_difficulty_rating": ("exact", "gte", "lte"),
        "is_active": ("exact",),
        "created_at": ("exact", "gte", "lte"),
        "updated_at": ("exact", "gte", "lte"),
    }

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AssessmentDetailSerializer
        return AssessmentSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Assessment.objects.filter(Q(is_private=False) | Q(user=self.request.user))
        return Assessment.objects.filter(is_private=False, is_active=True)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        assessment = self.get_object()
        prev_num = assessment.number_of_questions
        response = super().update(request, *args, **kwargs)

        if prev_num != assessment.number_of_questions and assessment.is_active:
            active_count = Question.objects.filter(assessment=assessment, is_active=True).count()
            if active_count < assessment.number_of_questions:
                assessment.is_active = False
                assessment.save()
                response.data = {
                    "detail": "Assessment updated but made inactive due to insufficient active questions after modifying number_of_questions."
                }
                response.status_code = status.HTTP_200_OK
        return response

    def destroy(self, request, *args, **kwargs):
        assessment = self.get_object()
        assessment.is_active = False
        assessment.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["POST"], url_path="validate-and-activate")
    def validate_and_activate(self, request, pk=None):
        assessment = self.get_object()

        inactive_questions = Question.objects.filter(assessment=assessment, is_active=False)

        for question in inactive_questions:
            error_message = validate_question(question)
            if not error_message:
                question.is_active = True
                question.save()

        active_question_count = Question.objects.filter(assessment=assessment, is_active=True).count()
        if active_question_count < assessment.number_of_questions:
            return Response(
                {
                    "error": f"The assessment should have equal or more than {assessment.number_of_questions} active questions."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        assessment.is_active = True
        assessment.save()

        return Response({"detail": "Assessment validated and activated successfully."}, status=status.HTTP_200_OK)


class QuestionViewSet(viewsets.ModelViewSet):
    permission_classes = [QuestionChoicePermissions]
    serializer_class = QuestionSerializer
    filterset_fields = {
        "description": ("exact", "icontains"),
        "assessment": ("exact", "in"),
        "is_active": ("exact",),
        "is_multiple_choice": ("exact",),
        "created_at": ("exact", "gte", "lte"),
        "updated_at": ("exact", "gte", "lte"),
    }

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Question.objects.filter(assessment__user=self.request.user)
        return Question.objects.none()

    def perform_create(self, serializer):
        assessment = self.request.data.get("assessment")
        if assessment:
            try:
                assessment_instance = Assessment.objects.get(pk=assessment)
            except Assessment.DoesNotExist:
                raise PermissionDenied("The provided assessment does not exist.")

            if assessment_instance.user != self.request.user:
                raise PermissionDenied("You do not own this assessment.")

            serializer.save()
        else:
            raise PermissionDenied("Assessment is required.")

    @action(detail=True, methods=["POST"], url_path="validate-and-activate")
    def validate_and_activate(self, request, pk=None):
        question = self.get_object()
        if question.assessment.user != request.user:
            return Response(
                {"error": "You do not have permission to activate this question."}, status=status.HTTP_403_FORBIDDEN
            )

        error_message = validate_question(question)
        if error_message:
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)

        question.is_active = True
        question.save()
        return Response({"detail": "Question validated and activated successfully."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["POST"], url_path="validate-and-activate-bulk")
    def validate_and_activate_bulk(self, request):
        question_ids = request.data.get("question_ids", [])
        user_owned_questions_count = Question.objects.filter(id__in=question_ids, assessment__user=request.user).count()
        if user_owned_questions_count != len(question_ids):
            return Response({"error": "Some questions do not belong to you."}, status=status.HTTP_403_FORBIDDEN)

        questions = Question.objects.filter(id__in=question_ids).annotate(
            total_choices=Count("choices"),
            correct_choices=Count(Case(When(choices__correct_answer=True, then=1), output_field=IntegerField())),
        )
        errors = []
        to_activate = []
        for question in questions:
            error_message = validate_question(question)
            if error_message:
                errors.append({"question_id": question.id, "error": error_message})
            else:
                to_activate.append(question)
        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        Question.objects.filter(id__in=[q.id for q in to_activate]).update(is_active=True)
        return Response({"detail": "Questions validated and activated successfully."}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        question = self.get_object()
        question.is_active = False
        question.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        question = self.get_object()
        if "is_multiple_choice" in request.data and request.data["is_multiple_choice"] != question.is_multiple_choice:
            question.is_active = False
            question.save()
        if "assessment" in request.data:
            try:
                new_assessment = Assessment.objects.get(pk=request.data["assessment"])
            except Assessment.DoesNotExist:
                return Response(
                    {"error": "The specified assessment does not exist."}, status=status.HTTP_400_BAD_REQUEST
                )
            if new_assessment.user != request.user:
                return Response(
                    {"error": "You can only change to assessments that belong to you."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        return super(QuestionViewSet, self).update(request, *args, **kwargs)


class ChoiceViewSet(viewsets.ModelViewSet):
    permission_classes = [QuestionChoicePermissions]
    serializer_class = ChoiceSerializer
    filterset_fields = {
        "question": ("exact", "in"),
        "correct_answer": ("exact",),
    }

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Choice.objects.filter(question__assessment__user=self.request.user)
        return Choice.objects.none()

    def perform_create(self, serializer):
        """
        Overridden method to create a Choice instance.

        After creating a choice, if the associated question is of type "single answer"
        and there are now more than one correct choices, the question is set to inactive.
        """
        question_id = self.request.data.get("question")
        if not question_id:
            raise PermissionDenied("Question is required.")

        question_instance = Question.objects.filter(pk=question_id).first()
        if not question_instance:
            raise PermissionDenied("The provided question does not exist.")
        if question_instance.assessment.user != self.request.user:
            raise PermissionDenied("You do not own the assessment related to this question.")

        serializer.save()
        choice = serializer.instance
        if not question_instance.is_active:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        if not question_instance.is_multiple_choice and choice.correct_answer:
            existing_correct_choices = question_instance.choices.filter(correct_answer=True, is_active=True).count()

            if existing_correct_choices - 1 > 0:
                question_instance.is_active = False
                question_instance.save()
                return Response(
                    {
                        "message": "Choice created, but the associated question has been deactivated due to multiple correct answers.",
                        "choice": serializer.data,
                    },
                    status=status.HTTP_201_CREATED,
                )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AssessmentDifficultyRatingViewSet(viewsets.ModelViewSet):
    queryset = AssessmentDifficultyRating.objects.all()
    serializer_class = AssessmentDifficultyRatingSerializer
    filterset_fields = {
        "assessment": ("exact", "in"),
        "user": ("exact", "in"),
        "difficulty": ("exact", "gte", "lte"),
    }

    def update_assessment_rating(self, assessment):
        average_rating = AssessmentDifficultyRating.objects.filter(assessment=assessment).aggregate(
            average=Avg("difficulty")
        )["average"]
        assessment.user_difficulty_rating = average_rating
        assessment.save(update_fields=["user_difficulty_rating"])

    def perform_create(self, serializer):
        user = self.request.user
        assessment = serializer.validated_data.get("assessment")
        has_completed_attempt = Attempt.objects.filter(
            user=user, assessment=assessment, end_time__isnull=False
        ).exists()
        if not has_completed_attempt:
            raise ValidationError("You must complete the assessment before rating its difficulty.")
        serializer.save(user=user)
        self.update_assessment_rating(assessment)

    def perform_update(self, serializer):
        if set(serializer.validated_data.keys()) != {"difficulty"}:
            raise ValidationError("Solo se puede modificar el campo de difficulty")
        super().perform_update(serializer)

        assessment = serializer.instance.assessment
        self.update_assessment_rating(assessment)

    def perform_destroy(self, instance):
        assessment = instance.assessment
        super().perform_destroy(instance)

        self.update_assessment_rating(assessment)


class FollowAssessmentViewSet(viewsets.ModelViewSet):
    queryset = FollowAssessment.objects.all()
    serializer_class = FollowAssessmentSerializer
    permission_classes = [FollowAssessmentPermissions]
    http_method_names = ["get", "post", "delete", "head", "options"]
    filterset_fields = {
        "assessment": ("exact", "in"),
        "follower": ("exact", "in"),
        "created_at": ("exact", "gte", "lte"),
    }

    def get_queryset(self):
        return FollowAssessment.objects.filter(follower__is_active=True, assessment__is_active=True)

    def perform_create(self, serializer):
        serializer.save(follower=self.request.user)
