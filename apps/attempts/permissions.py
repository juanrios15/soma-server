from rest_framework import permissions

from .models import Attempt


class AttemptBasedPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            return request.user.is_authenticated

        if view.action in ["update", "partial_update", "destroy"]:
            return False

        return True

    def has_object_permission(self, request, view, obj):
        is_attempt = isinstance(obj, Attempt)

        attempt_owner = obj.user if is_attempt else obj.attempt.user
        assessment_owner = obj.assessment.user if is_attempt else obj.attempt.assessment.user

        return request.user in [attempt_owner, assessment_owner]
