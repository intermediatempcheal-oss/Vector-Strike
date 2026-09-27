import uuid

from django.conf import settings
from django.db import models


class Profile(models.Model):
    """Extended, extensible profile attached to a Vector Strike user.

    Kept deliberately lean up front; progressively richer fields (avatar,
    badges, clan, stats…) attach here without touching the user table.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(max_length=120, blank=True, default="")
    avatar = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Avatar URL/path; an empty value uses the default generated avatar.",
    )
    bio = models.CharField(max_length=240, blank=True, default="")
    language = models.CharField(max_length=8, default="en")
    country = models.CharField(max_length=8, blank=True, default="")
    skill_level = models.CharField(max_length=24, blank=True, default="beginner")
    # Genuine starting progression — configured globally so new accounts always
    # begin at the true starting level with zero XP.
    level = models.PositiveIntegerField(default=settings.PROFILE_STARTING_LEVEL)
    xp = models.PositiveIntegerField(default=settings.PROFILE_STARTING_XP)
    rank = models.CharField(
        max_length=32, default=settings.PROFILE_STARTING_RANK, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "profiles_profile"
        verbose_name = "profile"
        verbose_name_plural = "profiles"

    def __str__(self):
        return f"{self.display_name or self.user.display_identity}"


class Interest(models.Model):
    """A canonical onboarding interest/category (e.g. Mathematics, Space).

    These are stable rows referenced by ``UserInterest`` through a foreign
    key so recommender queries stay fast and normalized.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=40, unique=True, db_index=True)
    label = models.CharField(max_length=60)
    description = models.CharField(max_length=160, blank=True, default="")
    icon = models.CharField(max_length=40, blank=True, default="")
    accent = models.CharField(max_length=16, blank=True, default="")
    category = models.CharField(max_length=30, default="learning")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "profiles_interest"
        ordering = ["sort_order", "label"]
        verbose_name = "interest"
        verbose_name_plural = "interests"

    def __str__(self):
        return self.label


class UserInterest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_interests",
    )
    interest = models.ForeignKey(
        Interest, on_delete=models.CASCADE, related_name="user_links"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "profiles_user_interest"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "interest"], name="uniq_user_interest"
            )
        ]
        verbose_name = "user interest"
        verbose_name_plural = "user interests"

    def __str__(self):
        return f"{self.user.display_identity} -> {self.interest.slug}"


class PlayStyle(models.Model):
    """How the user enjoys playing (feeds the future recommendation engine)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=50, unique=True, db_index=True)
    label = models.CharField(max_length=80)
    description = models.CharField(max_length=180, blank=True, default="")
    icon = models.CharField(max_length=40, blank=True, default="")
    accent = models.CharField(max_length=16, blank=True, default="")
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "profiles_play_style"
        ordering = ["sort_order", "label"]
        verbose_name = "play style"
        verbose_name_plural = "play styles"

    def __str__(self):
        return self.label


class UserPlayStyle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_play_styles",
    )
    play_style = models.ForeignKey(
        PlayStyle, on_delete=models.CASCADE, related_name="user_links"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "profiles_user_play_style"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "play_style"], name="uniq_user_play_style"
            )
        ]
        verbose_name = "user play style"
        verbose_name_plural = "user play styles"

    def __str__(self):
        return f"{self.user.display_identity} -> {self.play_style.slug}"