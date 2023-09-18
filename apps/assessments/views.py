from django.db.models import Q
from rest_framework import viewsets

from .models import Category, Subcategory, Assessment, Question, Choice, AssessmentDifficultyRating
from .serializers import (
    CategorySerializer,
    SubcategorySerializer,
    AssessmentSerializer,
    QuestionSerializer,
    ChoiceSerializer,
    AssessmentDifficultyRatingSerializer,
)
from .permissions import AssessmentPermissions, QuestionChoicePermissions


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
    }

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Assessment.objects.filter(Q(is_private=False) | Q(user=self.request.user))
        return Assessment.objects.filter(is_private=False, is_active=True)


class QuestionViewSet(viewsets.ModelViewSet):
    permission_classes = [QuestionChoicePermissions]
    serializer_class = QuestionSerializer
    filterset_fields = {
        "description": ("exact", "icontains"),
        "assessment": ("exact", "in"),
    }

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Question.objects.filter(assessment__user=self.request.user)
        return Question.objects.none()


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


class AssessmentDifficultyRatingViewSet(viewsets.ModelViewSet):
    queryset = AssessmentDifficultyRating.objects.all()
    serializer_class = AssessmentDifficultyRatingSerializer
    filterset_fields = {
        "assessment": ("exact", "in"),
        "user": ("exact", "in"),
        "difficulty": ("exact", "gte", "lte"),
    }
