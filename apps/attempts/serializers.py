from rest_framework import serializers

from .models import Attempt, QuestionAttempt


class AttemptSerializer(serializers.ModelSerializer):
    assessment_time_limit = serializers.ReadOnlyField(source="assessment.time_limit")

    class Meta:
        model = Attempt
        fields = "__all__"
        read_only_fields = ("user", "score", "approved", "start_time", "end_time")


class QuestionAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionAttempt
        fields = "__all__"
        read_only_fields = ("is_correct",)
