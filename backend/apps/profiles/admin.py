from django.contrib import admin

from apps.profiles.models import Interest, PlayStyle, Profile, UserInterest, UserPlayStyle


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "language", "country", "skill_level")
    search_fields = ("user__email", "user__username", "user__vector_id", "display_name")


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    list_display = ("slug", "label", "category", "sort_order", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("slug", "label")


@admin.register(PlayStyle)
class PlayStyleAdmin(admin.ModelAdmin):
    list_display = ("slug", "label", "sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("slug", "label")


@admin.register(UserInterest)
class UserInterestAdmin(admin.ModelAdmin):
    list_display = ("user", "interest")
    search_fields = ("user__email", "user__vector_id", "interest__label")


@admin.register(UserPlayStyle)
class UserPlayStyleAdmin(admin.ModelAdmin):
    list_display = ("user", "play_style")
    search_fields = ("user__email", "user__vector_id", "play_style__label")