from rest_framework import permissions

from .models import Attempt


class AttemptBasedPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            return request.user.is_authenticated

        if view.action in ["update", "partial_update", "destroy"]:
            return False

        return True
