from django.urls import path, include
from rest_framework import routers

from .views import UserViewSet, FollowViewSet, UserPointsViewSet


app_name = "users"

router = routers.DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"follows", FollowViewSet, basename="follows")
router.register(r"userpoints", UserPointsViewSet, basename="userpoints")

urlpatterns = [
    path("", include(router.urls)),
]
