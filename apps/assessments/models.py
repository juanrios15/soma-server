import os

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Subcategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()

    class Meta:
        verbose_name_plural = "Subcategories"

    def __str__(self):
        return f"{self.category.name} - {self.name}"


def content_file_name(instance, filename):
    return os.path.join("profile_pics", filename)


class Assessment(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    minimum_requirements = models.TextField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    image = models.ImageField(upload_to=content_file_name, blank=True, null=True)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    min_score = models.PositiveIntegerField(default=70, validators=[MinValueValidator(60), MaxValueValidator(100)])
    number_of_questions = models.PositiveIntegerField(
        default=10, validators=[MinValueValidator(5), MaxValueValidator(50)]
    )
    allowed_attempts = models.PositiveIntegerField(default=2, validators=[MinValueValidator(2), MaxValueValidator(10)])
    time_limit = models.PositiveIntegerField(default=20, validators=[MinValueValidator(1), MaxValueValidator(120)])
    difficulty = models.FloatField(default=5.0, validators=[MinValueValidator(1.0), MaxValueValidator(10.0)])
    user_difficulty_rating = models.FloatField(default=5.0)

    def __str__(self):
        return self.name


class Question(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="questions")
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.description[:50] + "..." if len(self.description) > 50 else self.description


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    description = models.TextField()
    correct_answer = models.BooleanField(default=False)

    def __str__(self):
        return self.description[:50] + "..." if len(self.description) > 50 else self.description


class AssessmentDifficultyRating(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="difficulty_ratings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="difficulty_ratings_given"
    )
    difficulty = models.FloatField(validators=[MinValueValidator(1), MaxValueValidator(10)])

    class Meta:
        verbose_name = "Assessment difficulty rating"
        verbose_name_plural = "Assessment difficulty ratings"
        unique_together = [["user", "assessment"]]

    def __str__(self):
        return f"{self.user.username} rated {self.assessment} with {self.difficulty} difficulty"
