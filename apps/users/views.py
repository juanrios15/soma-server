import random
import string

from django.conf import settings
from django.core.mail import send_mail
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django_countries import countries
from google.oauth2 import id_token
from google.auth.transport import requests
import requests as http_requests

from .serializers import (
    UserSerializer,
    UserDetailSerializer,
    ReadOnlyUserSerializer,
    UserEditSerializer,
    UserMeSerializer,
    FollowSerializer,
    UserPointsSerializer,
    PasswordResetSerializer,
)
from .models import CustomUser, Follow, UserPoints
from .permissions import CustomUserPermissions, FollowPermissions


class CountryListView(APIView):
    def get(self, request, *args, **kwargs):
        return Response(countries)


class ReadOnlyUserViewSet(viewsets.ModelViewSet):
    serializer_class = ReadOnlyUserSerializer
    queryset = CustomUser.objects.all()
    filterset_fields = {
        "username": ("exact", "in", "icontains"),
        "average_score": ("exact", "gte", "lte"),
        "points": ("exact", "gte", "lte"),
    }
    ordering_fields = ["points", "average_score"]


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    permission_classes = [CustomUserPermissions]
    filterset_fields = {
        "username": ("exact", "in", "icontains"),
        "email": ("exact", "in", "icontains"),
        "average_score": ("exact", "gte", "lte"),
        "points": ("exact", "gte", "lte"),
    }
    ordering_fields = ["points", "average_score"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserDetailSerializer
        elif self.action == "me":
            return UserMeSerializer
        elif self.action in ["update", "partial_update"]:
            return UserEditSerializer
        return UserSerializer

    @action(detail=False, methods=["post"])
    def google_auth(self, request):
        google_id = request.data.get("google_id")
        if not google_id:
            return Response({"error": "Google ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            idinfo = id_token.verify_oauth2_token(google_id, requests.Request(), settings.GOOGLE_CLIENT_ID)
            if idinfo["iss"] not in ["accounts.google.com", "https://accounts.google.com"]:
                raise ValueError("Wrong issuer.")

            email = idinfo["email"]
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": idinfo.get("given_name", ""),
                    "last_name": idinfo.get("family_name", ""),
                    "username": email.split("@")[0],
                },
            )

            if created and idinfo.get("picture", ""):
                response = http_requests.get(idinfo["picture"])
                if response.status_code == 200:
                    user.profile_picture.save(f"{user.username}_profile.jpg", ContentFile(response.content), save=True)

            token, token_created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "user_id": user.id, "is_new": created})

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=["post"])
    def send_reset_code(self, request, pk=None):
        email = request.data.get("email")

        if not email:
            return Response({"error": "Email is required."}, status=400)

        try:
            user = CustomUser.objects.get(email=email)
        except ObjectDoesNotExist:
            return Response({"error": "User not found."}, status=404)
        reset_code = "".join(random.choices(string.ascii_letters + string.digits, k=6))

        user.reset_code = reset_code
        user.save()

        send_mail(
            "Reset your password",
            f"Use the following code to reset your password: {reset_code}. Access http://localhost:5173/resetpassword to proceed.",
            "juankrios15@gmail.com",
            [user.email],
            fail_silently=False,
        )
        return Response({"message": "Reset code sent to email."})

    @action(detail=False, methods=["post"])
    def reset_password(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            reset_code = serializer.validated_data["reset_code"]
            try:
                user = CustomUser.objects.get(reset_code=reset_code)
            except CustomUser.DoesNotExist:
                return Response(
                    {"detail": "Invalid reset code."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(serializer.validated_data["password"])
            user.reset_code = None
            user.save()
            return Response({"message": "Password reset successfully.", "username": user.email})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request, *args, **kwargs):
        """
        Return basic information about the authenticated user.
        """
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer_class()(request.user, context={"request": request})
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="top-scores")
    def top_scores(self, request, *args, **kwargs):
        """
        Get the top 20 users based on average_score.
        """
        top_users = CustomUser.objects.order_by("-average_score")[:20]
        # TODO: Usar un serializador con menos informacion para no consumir tanto...
        serializer = UserDetailSerializer(top_users, many=True, context={"request": request})
        return Response(serializer.data)


class FollowViewSet(viewsets.ModelViewSet):
    serializer_class = FollowSerializer
    permission_classes = [FollowPermissions]
    http_method_names = ["get", "post", "delete", "head", "options"]
    filterset_fields = {
        "follower": ("exact", "in"),
        "followed": ("exact", "in"),
        "created_at": ("exact", "gte", "lte"),
    }

    def get_queryset(self):
        return Follow.objects.filter(follower__is_active=True, followed__is_active=True)

    def perform_create(self, serializer):
        serializer.save(follower=self.request.user)


class UserPointsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = UserPoints.objects.all()
    serializer_class = UserPointsSerializer
    filterset_fields = {
        "user": ("exact", "in"),
        "category": ("exact", "in"),
        "total_points": ("gte", "lte"),
        "average_score": ("gte", "lte"),
    }
    ordering_fields = ["total_points", "average_score"]
