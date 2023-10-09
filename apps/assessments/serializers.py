from rest_framework import serializers

from .models import Category, Subcategory, Assessment, Question, Choice, AssessmentDifficultyRating, FollowAssessment
from apps.attempts.models import Attempt


class SubcategoryReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ["name", "image"]


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategoryReadOnlySerializer(many=True, read_only=True, source="subcategory_set")

    class Meta:
        model = Category
        fields = "__all__"


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = "__all__"


class AssessmentSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source="user.username")
    subcategory_name = serializers.ReadOnlyField(source="subcategory.name")

    class Meta:
        model = Assessment
        exclude = ["is_private"]
        read_only_fields = ("user", "average_score", "user_difficulty_rating", "is_active", "created_at", "updated_at")


class AssessmentDetailSerializer(serializers.ModelSerializer):
    language_name = serializers.ReadOnlyField(source="language.name")
    category_name = serializers.ReadOnlyField(source="subcategory.category.name")
    subcategory_name = serializers.ReadOnlyField(source="subcategory.name")
    user_username = serializers.ReadOnlyField(source="user.username")
    followers_count = serializers.SerializerMethodField()
    available_attempts = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = "__all__"

    def get_followers_count(self, obj):
        return FollowAssessment.objects.filter(assessment=obj, follower__is_active=True).count()

    def get_available_attempts(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            attempts_made = Attempt.objects.filter(user=user, assessment=obj).count()
            return obj.allowed_attempts - attempts_made
        return 0


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"
        read_only_fields = ("is_active",)


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = "__all__"


class AssessmentDifficultyRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentDifficultyRating
        fields = "__all__"
        read_only_fields = ["user", "created_at", "updated_at"]


class FollowAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FollowAssessment
        fields = "__all__"
        read_only_fields = ["follower", "created_at"]
