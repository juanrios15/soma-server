from rest_framework import permissions

from .models import Question, Choice


class AssessmentPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.method == "POST":
            return request.user.is_authenticated

        return True

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user


class QuestionChoicePermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action == "create":
            return request.user.is_authenticated

        return True

    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Question):
            owner = obj.assessment.user
        elif isinstance(obj, Choice):
            owner = obj.question.assessment.user
        else:
            return False
        return owner == request.user
