from django.contrib import admin
from . import models


@admin.register(models.SocialSource)
class SocialSourceAdmin(admin.ModelAdmin):
    list_display = ("platform", "handle", "active", "created_at")
    search_fields = ("platform", "handle")
    list_filter = ("platform", "active")


@admin.register(models.SocialPost)
class SocialPostAdmin(admin.ModelAdmin):
    list_display = ("platform", "post_id", "author", "published_at", "matched_categories")
    search_fields = ("post_id", "author", "text")
    list_filter = ("platform", "published_at")


@admin.register(models.SocialAccount)
class SocialAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "username", "user_id", "created_at")
    search_fields = ("user__username", "username", "user_id")
    list_filter = ("platform",)

# Register your models here.
