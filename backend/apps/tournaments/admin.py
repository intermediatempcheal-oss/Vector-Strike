"""Vector Strike Tournaments �?" Django admin (registered against real fields).

Every column, filter, search and inline is a REAL field from the REAL
tournament tables. Backend rows own all tournament truth; the admin only
ever reads/writes genuine tournament, participant, rule, round and result
rows �?" it never invents players, rounds, phases, schedules, rules, scores,
ranks or results.
"""

from django.contrib import admin

from apps.tournaments.models import (
    Tournament,
    TournamentParticipant,
    TournamentResult,
    TournamentRound,
    TournamentRule,
)


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "slug",
        "status",
        "game_type",
        "start_at",
        "end_at",
    )
    list_filter = ("status", "visibility", "game_type")
    prepopulated_fields = {"slug": ("title",)}
    search_fields = ("title", "slug", "description", "tagline")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(TournamentParticipant)
class TournamentParticipantAdmin(admin.ModelAdmin):
    list_display = ("tournament", "user", "status", "raw_score", "rank", "joined_at")
    list_filter = ("status",)
    search_fields = ("tournament__title", "user__username", "user__email")


@admin.register(TournamentRule)
class TournamentRuleAdmin(admin.ModelAdmin):
    list_display = ("tournament", "sort_order", "title")
    list_filter = ("tournament",)
    search_fields = ("title", "body")


@admin.register(TournamentRound)
class TournamentRoundAdmin(admin.ModelAdmin):
    list_display = ("tournament", "number", "label", "scheduled_at")
    list_filter = ("tournament",)
    search_fields = ("label",)


@admin.register(TournamentResult)
class TournamentResultAdmin(admin.ModelAdmin):
    list_display = ("tournament", "participant", "score", "rank", "recorded_at")
    list_filter = ("tournament",)
    search_fields = ("participant__username", "participant__email")
