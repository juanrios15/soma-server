import os

from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractUser, UserManager
from rest_framework.authtoken.models import Token
from django_countries.fields import CountryField

from apps.assessments.models import Category


class MrvUserManager(UserManager):
    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email=email, username=email, password=password, **extra_fields)


def content_file_name(instance, filename):
    return os.path.join("profile_pics", filename)


class CustomUser(AbstractUser):
    GENDER_CHOICES = (("M", "Male"), ("F", "Female"), ("O", "Other"))
    email = models.EmailField(unique=True)
    birthday = models.DateField(auto_now=False, auto_now_add=False, null=True, blank=True)
    profile_picture = models.ImageField(upload_to=content_file_name, null=True, blank=True)
    biography = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    updated_time = models.DateField(auto_now=True)
    average_score = models.FloatField(default=0)
    points = models.IntegerField(default=0)
    reset_code = models.CharField(max_length=7, null=True, blank=True)
    country = CountryField(blank=True, null=True)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = MrvUserManager()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class UserPoints(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    total_points = models.PositiveIntegerField(default=0)
    average_score = models.FloatField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "category")
        verbose_name_plural = "User Points"

    def __str__(self):
        return f"{self.user.email} - {self.category.name} - {self.total_points} points"


class Follow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following")
    followed = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("follower", "followed")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.follower} -> {self.followed}"
