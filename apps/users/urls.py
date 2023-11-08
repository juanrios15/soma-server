from django.urls import path, include
from rest_framework import routers

from .views import UserViewSet, ReadOnlyUserViewSet, FollowViewSet, UserPointsViewSet, CountryListView


app_name = "users"

router = routers.DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"topusers", ReadOnlyUserViewSet, basename="topusers")
router.register(r"follows", FollowViewSet, basename="follows")
router.register(r"userpoints", UserPointsViewSet, basename="userpoints")

urlpatterns = [
    path("", include(router.urls)),
    path('countries/', CountryListView.as_view(), name='country-list'),
]
