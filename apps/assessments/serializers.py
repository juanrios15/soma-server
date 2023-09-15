from rest_framework import serializers

from .models import Category, Subcategory, Assessment, Question, Choice, AssessmentDifficultyRating


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = "__all__"


class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = "__all__"


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = "__all__"


class AssessmentDifficultyRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentDifficultyRating
        fields = "__all__"
