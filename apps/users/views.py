from rest_framework import viewsets, status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import UserSerializer
from .models import CustomUser
from .permissions import CustomUserPermissions


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [CustomUserPermissions]
