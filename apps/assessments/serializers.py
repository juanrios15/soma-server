from rest_framework import serializers

from .models import Category, Subcategory, Assessment, Question, Choice, AssessmentDifficultyRating, FollowAssessment


class SubcategoryReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['name', 'image']


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategoryReadOnlySerializer(many=True, read_only=True, source='subcategory_set')
    class Meta:
        model = Category
        fields = "__all__"


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = "__all__"


class AssessmentSerializer(serializers.ModelSerializer):
    subcategory_name = serializers.ReadOnlyField(source='subcategory.name')
    user_username = serializers.ReadOnlyField(source='user.username')
    class Meta:
        model = Assessment
        exclude = ["is_private"]
        read_only_fields = ("user", "average_score", "user_difficulty_rating", "is_active", "created_at", "updated_at")


class AssessmentDetailSerializer(serializers.ModelSerializer):
    followers_count = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        fields = "__all__"

    def get_followers_count(self, obj):
        return FollowAssessment.objects.filter(assessment=obj, follower__is_active=True).count()


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
