from django.contrib import admin

from apps.games.models import (
    Achievement,
    DailyChallenge,
    Event,
    Game,
    GameCategory,
    GameSession,
    Mission,
    UserAchievement,
    UserGameProgress,
    UserMission,
)


@admin.register(GameCategory)
class GameCategoryAdmin(admin.ModelAdmin):
    list_display = ("label", "slug", "sort_order", "is_active")
    prepopulated_fields = {"slug": ("label",)}
    ordering = ("sort_order", "label")


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "difficulty",
        "status",
        "minimum_age",
        "release_date",
        "is_featured",
        "is_new",
    )
    list_filter = ("status", "category", "difficulty")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "slug")


@admin.register(UserGameProgress)
class UserGameProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "game", "current_level", "completion_percentage", "last_played_at")
    list_filter = ("game",)
    search_fields = ("user__username", "game__title")


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "kind", "target", "xp_reward", "is_active")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    list_display = ("user", "achievement", "earned_at")
    search_fields = ("user__username",)


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "kind", "target", "xp_reward", "is_active")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(UserMission)
class UserMissionAdmin(admin.ModelAdmin):
    list_display = ("user", "mission", "progress", "completed", "completed_at")


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "game",
        "status",
        "score",
        "accuracy",
        "level_reached",
        "duration_seconds",
        "xp_earned",
        "started_at",
    )
    list_filter = ("status", "game")
    search_fields = ("user__username", "game__title")


@admin.register(DailyChallenge)
class DailyChallengeAdmin(admin.ModelAdmin):
    list_display = ("title", "date", "game", "reward_xp", "active")
    ordering = ("-date",)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "status", "starts_at", "ends_at")
    prepopulated_fields = {"slug": ("title",)}