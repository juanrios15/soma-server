from rest_framework import permissions


class CustomUserPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ["create", "send_reset_code", "reset_password", "google_auth"]:
            return True
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if view.action in ["update", "partial_update", "destroy"]:
            return obj == request.user
        return True


class FollowPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.is_authenticated
        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.method == 'DELETE':
            return obj.follower == request.user or obj.followed == request.user
        return False
