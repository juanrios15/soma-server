from rest_framework import viewsets

from .serializers import UserSerializer, UserDetailSerializer, FollowSerializer
from .models import CustomUser, Follow
from .permissions import CustomUserPermissions, FollowPermissions


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    permission_classes = [CustomUserPermissions]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UserDetailSerializer
        return UserSerializer


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