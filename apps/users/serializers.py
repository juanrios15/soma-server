from django.db.models import Avg, Count, Case, When, FloatField
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Follow
from apps.attempts.models import Attempt
from apps.assessments.models import FollowAssessment


class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "password", "password2")
        extra_kwargs = {"password": {"write_only": True, "style": {"input_type": "password"}}}

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("The password must be at least 8 characters long.")

        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("The password must contain at least one number.")

        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("password2", None)
        user = get_user_model().objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserDetailSerializer(serializers.ModelSerializer):
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()
    following_assessments_count = serializers.SerializerMethodField()
    attempts_count = serializers.SerializerMethodField()
    average_score = serializers.SerializerMethodField()
    total_approved = serializers.SerializerMethodField()
    approved_percentage = serializers.SerializerMethodField()
    full_score_percentage = serializers.SerializerMethodField()

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "birthday",
            "profile_picture",
            "biography",
            "gender",
            "follower_count",
            "following_count",
            "following_assessments_count",
            "attempts_count",
            "average_score",
            "total_approved",
            "approved_percentage",
            "full_score_percentage",
        ]

    def get_attempt_statistics(self, obj):
        if not hasattr(obj, "_attempt_stats_cache"):
            obj._attempt_stats_cache = Attempt.objects.filter(user=obj).aggregate(
                total_approved=Count(Case(When(approved=True, then=1))),
                total_attempts=Count("id"),
                full_score_attempts=Count(Case(When(score=100, then=1))),
            )
        return obj._attempt_stats_cache

    def get_follower_count(self, obj):
        return Follow.objects.filter(followed=obj, follower__is_active=True).count()

    def get_following_count(self, obj):
        return Follow.objects.filter(follower=obj, followed__is_active=True).count()

    def get_following_assessments_count(self, obj):
        return FollowAssessment.objects.filter(follower=obj, assessment__is_active=True).count()

    def get_attempts_count(self, obj):
        return self.get_attempt_statistics(obj)["total_attempts"]

    def get_average_score(self, obj):
        return Attempt.objects.filter(user=obj).aggregate(average_score=Avg("score"))["average_score"] or 0

    def get_total_approved(self, obj):
        return self.get_attempt_statistics(obj)["total_approved"]

    def get_approved_percentage(self, obj):
        stats = self.get_attempt_statistics(obj)
        if not stats["total_attempts"]:
            return 0
        return (stats["total_approved"] / stats["total_attempts"]) * 100

    def get_full_score_percentage(self, obj):
        stats = self.get_attempt_statistics(obj)
        if not stats["total_attempts"]:
            return 0
        return (stats["full_score_attempts"] / stats["total_attempts"]) * 100


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id", "username", "first_name", "email", "date_joined"]


class FollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = "__all__"
        read_only_fields = ["follower", "created_at"]

    def validate(self, data):
        user = self.context["request"].user
        if "followed" in data:
            if data["followed"] == user:
                raise serializers.ValidationError("A user cannot follow themselves.")
        else:
            raise serializers.ValidationError("'followed' field is required.")
        return data
