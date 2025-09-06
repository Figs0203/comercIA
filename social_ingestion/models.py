from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class SocialSource(models.Model):
    """Modelo que representa una fuente de redes sociales para monitorear"""
    PLATFORM_CHOICES = [
        ("x", "X/Twitter"),
        ("telegram", "Telegram"),
    ]

    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)
    handle = models.CharField(max_length=255, help_text="@usuario, canal, chat o query API")
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["platform", "handle"]),
        ]

    def __str__(self) -> str:
        return f"{self.platform}:{self.handle}"


class SocialPost(models.Model):
    """Modelo que almacena publicaciones de redes sociales con categorías detectadas"""
    platform = models.CharField(max_length=20)
    post_id = models.CharField(max_length=255, unique=True)
    author = models.CharField(max_length=255)
    text = models.TextField()
    published_at = models.DateTimeField(default=timezone.now)
    raw_payload = models.JSONField(null=True, blank=True)
    matched_categories = models.CharField(max_length=255, blank=True, help_text="Categorias detectadas")

    class Meta:
        ordering = ["-published_at"]
        indexes = [
            models.Index(fields=["platform", "post_id"]),
            models.Index(fields=["published_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.platform}:{self.post_id}"


class SocialAccount(models.Model):
    """Modelo que vincula cuentas de usuarios con sus perfiles de redes sociales"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='social_account')
    platform = models.CharField(max_length=20, default='x')
    username = models.CharField(max_length=255, help_text='Username de X sin @')
    external_user_id = models.CharField(max_length=64, help_text='ID numérico de X', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["platform", "username"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.username} -> {self.platform}:{self.username}"

# Create your models here.
