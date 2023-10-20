from rest_framework import serializers

from .models import Attempt, QuestionAttempt


class AttemptSerializer(serializers.ModelSerializer):
    assessment_time_limit = serializers.ReadOnlyField(source="assessment.time_limit")
    assessment_name = serializers.ReadOnlyField(source="assessment.name")
    assessment_min_score = serializers.ReadOnlyField(source="assessment.min_score")
    assessment_number_of_questions = serializers.ReadOnlyField(source="assessment.number_of_questions")

    class Meta:
        model = Attempt
        fields = "__all__"
        read_only_fields = ("user", "score", "approved", "start_time", "end_time")


class QuestionAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAttempt
        fields = "__all__"
        read_only_fields = ("is_correct",)
