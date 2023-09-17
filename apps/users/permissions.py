from rest_framework import permissions


class CustomUserPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if view.action in ["update", "partial_update", "destroy"]:
            return obj == request.user
        return True
