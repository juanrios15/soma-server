from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.assessments.models import Assessment, Question, Choice


class Attempt(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="attempts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attempts")
    score = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0.0)
    approved = models.BooleanField(default=False)
    questions_provided = models.BooleanField(default=False)
    is_finished = models.BooleanField(default=False)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    points_obtained = models.IntegerField(default=0)

    def __str__(self):
        return f"Attempt by {self.user.username} on {self.assessment.name} - Score: {self.score}"


class QuestionAttempt(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="question_attempts")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="question_attempts")
    selected_choices = models.ManyToManyField(Choice, related_name="question_attempts")
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Question Attempt for {self.attempt.user.username} - {self.question.description}"
