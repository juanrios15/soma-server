from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import UserSerializer, UserDetailSerializer, UserMeSerializer, FollowSerializer, UserPointsSerializer
from .models import CustomUser, Follow, UserPoints
from .permissions import CustomUserPermissions, FollowPermissions


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
        return UserSerializer

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
    }
    ordering_fields = ["total_points"]
