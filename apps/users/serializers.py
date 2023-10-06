from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Follow
from apps.assessments.models import FollowAssessment


class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True, required=True, style={"input_type": "password"})

    class Meta:
        model = get_user_model()
        fields = ("username", "email", "password", "password2")
        extra_kwargs = {"password": {"write_only": True, "style": {"input_type": "password"}}}

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("La contraseña debe tener al menos 8 caracteres.")

        if not any(char.isdigit() for char in value):
            raise serializers.ValidationError("La contraseña debe contener al menos un número.")

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

    class Meta:
        model = get_user_model()
        fields = "__all__"

    def get_follower_count(self, obj):
        return Follow.objects.filter(followed=obj, follower__is_active=True).count()

    def get_following_count(self, obj):
        return Follow.objects.filter(follower=obj, followed__is_active=True).count()

    def get_following_assessments_count(self, obj):
        return FollowAssessment.objects.filter(follower=obj, assessment__is_active=True).count()


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["username", "first_name", "email", "date_joined"]


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
