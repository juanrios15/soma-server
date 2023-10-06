from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import UserSerializer, UserDetailSerializer, UserMeSerializer, FollowSerializer
from .models import CustomUser, Follow
from .permissions import CustomUserPermissions, FollowPermissions


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    permission_classes = [CustomUserPermissions]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserDetailSerializer
        elif self.action == "me":
            return UserMeSerializer
        return UserSerializer

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request, *args, **kwargs):
        """
        Return basic information about the authenticated user.
        """
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer_class()(request.user)
        return Response(serializer.data)


class FollowViewSet(viewsets.ModelViewSet):
    queryset = Follow.objects.all()
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