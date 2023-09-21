from rest_framework import viewsets
from .serializers import UserSerializer
from .models import CustomUser
from .permissions import CustomUserPermissions


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [CustomUserPermissions]
