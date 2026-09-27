"""Vector Strike tournaments domain (Phase 11).

A tournament is a real, backend-owned competition. Every participant row is a
genuine database record derived from the authenticated member's real action
(join/leave/result), never fabricated. Eligibility, availability, status and
participation are always decided server-side from actual rows + PostgreSQL
timezone-aware timestamps.

No participant lists are stored as JSON blobs: participation is a relational
``TournamentParticipant`` row with the proper uniqueness and indexes.
"""

import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.games.models import Game


class Tournament(models.Model):
    """A published competition anyone eligible may enter (join enforced on the
    backend only). Status is derived from start/end timestamps.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        UPCOMING = "upcoming", "Upcoming"
        LIVE = "live", "Live"
        ENDING_SOON = "ending_soon", "Ending soon"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class Visibility(models.TextChoices):
        PUBLIC = "public", "Public"
        INVITE = "invite", "Invite only"

    class GameType(models.TextChoices):
        SOLO = "solo", "Solo"
        TEAM = "team", "Team"
        BOTH = "both", "Both"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=64, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    tagline = models.CharField(max_length=140, blank=True, default="")
    banner = models.CharField(max_length=255, blank=True, default="")
    thumbnail = models.CharField(max_length=255, blank=True, default="")
    game = models.ForeignKey(
        Game, on_delete=models.PROTECT, related_name="tournaments", null=True, blank=True
    )
    category = models.CharField(max_length=64, blank=True, default="")
    game_type = models.CharField(max_length=16, choices=GameType.choices, default=GameType.SOLO)
    visibility = models.CharField(max_length=16, choices=Visibility.choices, default=Visibility.PUBLIC)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.UPCOMING, db_index=True)
    start_at = models.DateTimeField(db_index=True)
    end_at = models.DateTimeField(db_index=True)
    registration_start_at = models.DateTimeField(null=True, blank=True)
    registration_end_at = models.DateTimeField(null=True, blank=True)
    minimum_age = models.PositiveIntegerField(default=0)
    maximum_age = models.PositiveIntegerField(null=True, blank=True)
    entry_type = models.CharField(max_length=24, blank=True, default="")
    entry_requirement = models.CharField(max_length=255, blank=True, default="")
    reward_configuration = models.JSONField(default=dict, blank=True)
    maximum_participants = models.PositiveIntegerField(default=0)
    sort_order = models.PositiveIntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tournaments_tournament"
        ordering = ["-start_at"]
        indexes = [
            models.Index(fields=["status", "start_at"], name="trn_status_start"),
            models.Index(fields=["is_featured", "status"], name="trn_featured_status"),
            models.Index(fields=["game", "status"], name="trn_game_status"),
        ]

    def __str__(self):
        return self.title

    @property
    def participant_count(self):
        return self.participants.filter(status=TournamentParticipant.Status.ACTIVE).count()

    def live_status(self):
        now = timezone.now()
        if self.status == Tournament.Status.CANCELLED:
            return Tournament.Status.CANCELLED
        if self.status == Tournament.Status.DRAFT:
            return Tournament.Status.DRAFT
        if self.end_at and now > self.end_at:
            return Tournament.Status.COMPLETED
        if self.start_at and now >= self.start_at:
            if self.end_at and self.end_at - now <= timedelta(hours=6):
                return Tournament.Status.ENDING_SOON
            return Tournament.Status.LIVE
        return Tournament.Status.UPCOMING


class TournamentParticipant(models.Model):
    """A real member's participation in a tournament.

    One row per (tournament, user) �?" duplication is prevented structurally
    with a unique constraint and enforced again in the join service inside a
    transaction so simultaneous joins cannot create duplicate rows.
    """

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        LEFT = "left", "Left"
        DISQUALIFIED = "disqualified", "Disqualified"
        FINISHED = "finished", "Finished"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(
        Tournament, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tournament_participations"
    )
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    raw_score = models.BigIntegerField(default=0)
    rank = models.PositiveIntegerField(null=True, blank=True)
    result_metadata = models.JSONField(default=dict, blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tournaments_participant"
        constraints = [
            models.UniqueConstraint(fields=["tournament", "user"], name="uniq_tournament_user_participant")
        ]
        indexes = [
            models.Index(fields=["tournament", "status"], name="part_tournament_status"),
            models.Index(fields=["user", "-joined_at"], name="part_user_joined"),
        ]

    def __str__(self):
        return f"{self.user} in {self.tournament.title}"


class TournamentRule(models.Model):
    """A configured rule for a specific tournament (real backend rows)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="rules")
    sort_order = models.PositiveIntegerField(default=0)
    title = models.CharField(max_length=120)
    body = models.TextField(blank=True, default="")
    kind = models.CharField(max_length=32, blank=True, default="")

    class Meta:
        db_table = "tournaments_rule"
        ordering = ["sort_order"]
        indexes = [models.Index(fields=["tournament", "sort_order"], name="rule_tournament_sort")]

    def __str__(self):
        return self.title


class TournamentRound(models.Model):
    """A competition round (qualifier ──> final) with its own result records."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="rounds")
    number = models.PositiveIntegerField()
    label = models.CharField(max_length=80)
    scheduled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "tournaments_round"
        constraints = [models.UniqueConstraint(fields=["tournament", "number"], name="uniq_tournament_round_number")]
        indexes = [models.Index(fields=["tournament", "number"], name="round_tournament_number")]

    def __str__(self):
        return f"{self.tournament.title} R{self.number}"


class TournamentResult(models.Model):
    """A real round/completion result for a member (never fabricated)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="results")
    round = models.ForeignKey(TournamentRound, on_delete=models.CASCADE, related_name="results", null=True, blank=True)
    participant = models.ForeignKey(TournamentParticipant, on_delete=models.CASCADE, related_name="results")
    score = models.BigIntegerField(default=0)
    rank = models.PositiveIntegerField(null=True, blank=True)
    result_data = models.JSONField(default=dict, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tournaments_result"
        indexes = [
            models.Index(fields=["tournament", "-score"], name="res_tournament_score"),
            models.Index(fields=["participant", "round"], name="res_participant_round"),
        ]

    def __str__(self):
        return f"Result {self.score} ({self.tournament.title})"
