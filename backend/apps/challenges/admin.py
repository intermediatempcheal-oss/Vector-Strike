"""Vector Strike Challenges — Django admin (Phase 11).

Every column, filter and search targets a real field on a real relational
row: challenges, participants, invitations, teams, members and results all
come straight from the real PostgreSQL tables the backend owns.
"""

from django.contrib import admin

from apps.challenges.models import (
    Challenge,
    ChallengeInvitation,
    ChallengeParticipant,
    ChallengeRoom,
    ChallengeRoomMember,
    ChallengeResult,
    ChallengeTeam,
    ChallengeTeamMember,
)


@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ("title", "creator", "challenge_type", "status", "visibility", "created_at")
    list_filter = ("challenge_type", "status", "visibility")
    search_fields = ("title", "description", "creator__username", "creator__email")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(ChallengeParticipant)
class ChallengeParticipantAdmin(admin.ModelAdmin):
    list_display = ("challenge", "user", "status", "score", "rank", "joined_at")
    list_filter = ("status",)
    search_fields = ("challenge__title", "user__username", "user__email")
    readonly_fields = ("joined_at",)


@admin.register(ChallengeInvitation)
class ChallengeInvitationAdmin(admin.ModelAdmin):
    list_display = ("challenge", "sender", "recipient", "status", "created_at")
    list_filter = ("status",)
    search_fields = ("challenge__title", "sender__username", "recipient__username")


@admin.register(ChallengeTeam)
class ChallengeTeamAdmin(admin.ModelAdmin):
    list_display = ("name", "challenge", "created_at")
    search_fields = ("name", "challenge__title")
    readonly_fields = ("created_at",)


@admin.register(ChallengeTeamMember)
class ChallengeTeamMemberAdmin(admin.ModelAdmin):
    list_display = ("team", "user", "is_ready", "joined_at")
    list_filter = ("is_ready",)
    search_fields = ("team__name", "user__username")
    readonly_fields = ("joined_at",)


@admin.register(ChallengeRoom)
class ChallengeRoomAdmin(admin.ModelAdmin):
    list_display = ("room_code", "challenge", "host", "status", "expires_at", "created_at")
    list_filter = ("status",)
    search_fields = ("room_code", "challenge__title", "host__username")
    readonly_fields = ("room_code", "created_at")


@admin.register(ChallengeRoomMember)
class ChallengeRoomMemberAdmin(admin.ModelAdmin):
    list_display = ("room", "user", "status", "is_ready", "joined_at")
    list_filter = ("status", "is_ready")
    search_fields = ("room__room_code", "user__username")
    readonly_fields = ("joined_at",)


@admin.register(ChallengeResult)
class ChallengeResultAdmin(admin.ModelAdmin):
    list_display = ("challenge", "participant", "score", "rank", "completed_at")
    list_filter = ("challenge",)
    search_fields = ("participant__user__username",)
    readonly_fields = ("completed_at",)
