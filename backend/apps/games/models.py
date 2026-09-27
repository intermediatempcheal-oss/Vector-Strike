"""Real game catalog and member progression for the Game Hub.

Phase 8 stores only genuine data rows: games are added through the catalog
seeded from the project's own original game list (never fabricated on the fly),
and member-facing numbers (progress, achievements, missions, challenge
completion) are always derived from actual backend records or member actions.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class GameCategory(models.Model):
    """A canonical game category (Math, Science, Logic, …)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=40, unique=True, db_index=True)
    label = models.CharField(max_length=60)
    # Futuristic display identity (Phase 9) — e.g. "LOGIX" for the logic
    # games. Slugs stay internal/academic so onboarding, interest links and
    # recommendations keep their stable identifiers; users only ever see
    # the codename identity.
    codename = models.CharField(max_length=24, blank=True, default="")
    tagline = models.CharField(max_length=140, blank=True, default="")
    accent = models.CharField(max_length=16, blank=True, default="")
    icon = models.CharField(max_length=40, blank=True, default="")
    description = models.CharField(max_length=180, blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "games_category"
        ordering = ["sort_order", "codename", "label"]
        verbose_name = "game category"
        verbose_name_plural = "game categories"

    def __str__(self):
        return self.codename or self.label


class Game(models.Model):
    """An original Vector Strike game title.

    Artwork is served from real bundled assets; age gating and status are the
    source of truth the recommendation service filters on.
    """

    class Difficulty(models.IntegerChoices):
        RELAXED = 1, "Relaxed"
        EASY = 2, "Easy"
        MODERATE = 3, "Moderate"
        CHALLENGING = 4, "Challenging"
        EXPERT = 5, "Expert"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"

    class GameType(models.TextChoices):
        SOLO = "solo", "Solo"
        VERSUS = "versus", "Versus"
        COOPERATIVE = "co-op", "Co-operative"
        MULTIPLAYER = "multiplayer", "Multiplayer"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=50, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    tagline = models.CharField(max_length=140, blank=True, default="")
    category = models.ForeignKey(
        GameCategory, on_delete=models.PROTECT, related_name="games"
    )
    # Optional extra categories so e.g. a physics/racing game belongs to both.
    secondary_categories = models.ManyToManyField(
        GameCategory, related_name="secondary_games", blank=True
    )
    difficulty = models.IntegerField(choices=Difficulty.choices, default=Difficulty.EASY)
    game_type = models.CharField(
        max_length=24, choices=GameType.choices, default=GameType.SOLO
    )
    # Gameplay mechanics identity (Phase 9): routes a game to its play runtime.
    play_kind = models.CharField(max_length=40, blank=True, default="")
    mechanics = models.CharField(max_length=120, blank=True, default="")
    # Universal gameplay foundation: optional per-game overrides of the
    # mechanic defaults declared in ``apps.games.identity.MECHANICS``.
    game_modes = models.JSONField(default=list, blank=True)
    orientation = models.CharField(max_length=12, blank=True, default="")
    visual_style = models.CharField(max_length=40, blank=True, default="")
    duration_minutes = models.PositiveIntegerField(default=8, blank=True, null=True)
    instructions = models.TextField(blank=True, default="")
    controls = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=24, choices=Status.choices, default=Status.DRAFT
    )
    minimum_age = models.PositiveIntegerField(default=6, null=True)
    maximum_age = models.PositiveIntegerField(blank=True, null=True)
    content_rating = models.CharField(max_length=16, blank=True, default="")
    thumbnail = models.CharField(max_length=255, blank=True, default="")
    banner = models.CharField(max_length=255, blank=True, default="")
    icon = models.CharField(max_length=40, blank=True, default="")
    release_date = models.DateField(blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "games_game"
        ordering = ["title"]
        indexes = [
            models.Index(fields=["status", "release_date"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["status", "-release_date"]),
            models.Index(fields=["status", "difficulty"]),
            models.Index(fields=["status", "game_type", "release_date"]),
        ]
        verbose_name = "game"
        verbose_name_plural = "games"

    def __str__(self):
        return self.title

    @property
    def category_slug(self):
        return self.category.slug


class UserGameProgress(models.Model):
    """A member's real, per-game progression record."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_progress",
        db_index=True,
    )
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="player_progress"
    )
    current_level = models.PositiveIntegerField(default=1)
    xp = models.PositiveIntegerField(default=0)
    score = models.PositiveIntegerField(default=0)
    completion_percentage = models.PositiveIntegerField(default=0)
    best_accuracy = models.PositiveIntegerField(default=0)
    best_combo = models.PositiveIntegerField(default=0)
    best_time_seconds = models.PositiveIntegerField(blank=True, null=True)
    playtime_seconds = models.PositiveIntegerField(default=0)
    last_played_at = models.DateTimeField(blank=True, null=True)
    games_played = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    streak_days = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "games_user_game_progress"
        constraints = [
            models.UniqueConstraint(fields=["user", "game"], name="uniq_user_game")
        ]
        indexes = [
            models.Index(fields=["user", "-last_played_at"]),
        ]
        verbose_name = "user game progress"
        verbose_name_plural = "user game progress"

    def __str__(self):
        return f"{self.user.display_identity} / {self.game.slug}"


class Achievement(models.Model):
    """A platform achievement template. Unlocked rows are stored in UserAchievement."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=60, unique=True, db_index=True)
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=200, blank=True, default="")
    icon = models.CharField(max_length=40, blank=True, default="")
    kind = models.CharField(max_length=30, default="lifetime")
    target = models.PositiveIntegerField(default=1)
    xp_reward = models.PositiveIntegerField(default=0)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "games_achievement"
        ordering = ["sort_order", "title"]
        verbose_name = "achievement"
        verbose_name_plural = "achievements"

    def __str__(self):
        return self.title


class UserAchievement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="achievements"
    )
    achievement = models.ForeignKey(
        Achievement, on_delete=models.CASCADE, related_name="earned"
    )
    earned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "games_user_achievement"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "achievement"], name="uniq_user_achievement"
            )
        ]
        verbose_name = "user achievement"
        verbose_name_plural = "user achievements"

    def __str__(self):
        return f"{self.user.display_identity} earned {self.achievement.slug}"


class Mission(models.Model):
    """A backend-stored mission template. Progress is tracked per user; the
    backend never auto-marks missions complete — real actions update them."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=60, unique=True, db_index=True)
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=220, blank=True, default="")
    kind = models.CharField(max_length=40, default="first_game")
    target = models.PositiveIntegerField(default=1)
    xp_reward = models.PositiveIntegerField(default=0)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "games_mission"
        ordering = ["sort_order", "title"]
        verbose_name = "mission"
        verbose_name_plural = "missions"

    def __str__(self):
        return self.title


class UserMission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="missions"
    )
    mission = models.ForeignKey(
        Mission, on_delete=models.CASCADE, related_name="assignments"
    )
    progress = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "games_user_mission"
        constraints = [
            models.UniqueConstraint(fields=["user", "mission"], name="uniq_user_mission")
        ]
        verbose_name = "user mission"
        verbose_name_plural = "user missions"

    def __str__(self):
        return f"{self.user.display_identity} / {self.mission.slug}"


class DailyChallenge(models.Model):
    """A real, date-scoped challenge referencing a real game."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(unique=True, db_index=True)
    game = models.ForeignKey(Game, on_delete=models.PROTECT, related_name="daily_challenge")
    title = models.CharField(max_length=140)
    description = models.CharField(max_length=220, blank=True, default="")
    reward_xp = models.PositiveIntegerField(default=50)
    goal = models.CharField(max_length=160, blank=True, default="")
    starts_at = models.DateTimeField(db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "games_daily_challenge"
        ordering = ["-date"]
        verbose_name = "daily challenge"
        verbose_name_plural = "daily challenges"

    def __str__(self):
        return f"{self.title} ({self.date})"


class Event(models.Model):
    """A platform event (live or upcoming). Only real, scheduled events exist."""

    class Status(models.TextChoices):
        UPCOMING = "upcoming", "Upcoming"
        LIVE = "live", "Live"
        ENDED = "ended", "Ended"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=60, unique=True, db_index=True)
    title = models.CharField(max_length=120)
    description = models.CharField(max_length=220, blank=True, default="")
    banner = models.CharField(max_length=255, blank=True, default="")
    starts_at = models.DateTimeField(db_index=True)
    ends_at = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.UPCOMING)

    class Meta:
        db_table = "games_event"
        ordering = ["starts_at"]
        verbose_name = "event"
        verbose_name_plural = "events"

    def __str__(self):
        return self.title


class GameSession(models.Model):
    """A real play run owned by a member.

    The backend creates sessions, owns their lifecycle and computes the
    authoritative result on completion — the frontend never writes progression.
    Metrics sent on completion are bounds-checked and clamped server-side so
    score/XP/level manipulation is not meaningful.
    """

    class Status(models.TextChoices):
        STARTED = "started", "Started"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        ABANDONED = "abandoned", "Abandoned"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="game_sessions"
    )
    game = models.ForeignKey(
        Game, on_delete=models.CASCADE, related_name="sessions"
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.STARTED, db_index=True
    )
    started_at = models.DateTimeField(default=timezone.now, db_index=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    score = models.PositiveIntegerField(default=0)
    accuracy = models.PositiveIntegerField(default=0)
    level_reached = models.PositiveIntegerField(default=1)
    duration_seconds = models.PositiveIntegerField(default=0)
    xp_earned = models.PositiveIntegerField(default=0)
    game_mode = models.CharField(max_length=20, default="quick", db_index=True)
    difficulty = models.PositiveIntegerField(default=1)
    mistakes = models.PositiveIntegerField(default=0)
    best_combo = models.PositiveIntegerField(default=0)
    completion_percentage = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "games_game_session"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["user", "-started_at"]),
            models.Index(fields=["user", "game", "status"]),
            models.Index(fields=["game", "status", "completed_at"]),
        ]
        verbose_name = "game session"
        verbose_name_plural = "game sessions"

    def __str__(self):
        return f"{self.user.display_identity} / {self.game.slug} / {self.status}"
