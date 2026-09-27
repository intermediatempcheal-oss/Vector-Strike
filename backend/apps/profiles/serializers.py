"""Vector Strike Profile + Stack serializers (Phase 12 — backend-first, real-rows-only).

The two classes at the top (``InterestSerializer``, ``PlayStyleSerializer``)
are the REAL account-flow contract that ``apps.accounts.views`` imports at
startup — they serialize the REAL ``Interest`` and ``PlayStyle`` rows. The
seven Stack/Profile classes below are the Phase-12 additive Stack surface;
every value they carry comes from the real engine in ``apps.profiles.services``
(real XP math using the games ``XP_PER_LEVEL``, real Profile/XP rows, real
achievement rows, real timed events). Nothing is invented, nothing is cached
client-side, and XP/level/rank are always derived server-side.
"""

from rest_framework import serializers

from apps.accounts.serializers import UserIdentitySerializer
from apps.profiles.models import Interest, PlayStyle


class InterestSerializer(serializers.ModelSerializer):
    """Real Interest row — the account-flow contract (unchanged from Phase 8)."""

    class Meta:
        model = Interest
        fields = (
            "id",
            "slug",
            "label",
            "description",
            "icon",
            "accent",
            "category",
            "sort_order",
            "is_active",
        )
        read_only_fields = fields


class PlayStyleSerializer(serializers.ModelSerializer):
    """Real PlayStyle row — the account-flow contract (unchanged from Phase 8)."""

    class Meta:
        model = PlayStyle
        fields = (
            "id",
            "slug",
            "label",
            "description",
            "icon",
            "accent",
            "sort_order",
            "is_active",
        )
        read_only_fields = fields


class ProfileReadSerializer(serializers.Serializer):
    """Real identity + real profile row. NEVER exposes password/tokens/private
    verification/guardian/email/phone — identity comes from the guarded
    ``UserIdentitySerializer`` the whole platform already trusts."""

    identity = serializers.SerializerMethodField()
    display_name = serializers.CharField()
    avatar = serializers.SerializerMethodField()
    bio = serializers.CharField(allow_blank=True, default="")
    language = serializers.CharField(allow_blank=True, default="")
    country = serializers.CharField(allow_blank=True, default="")
    skill_level = serializers.CharField(allow_blank=True, default="")
    completed_onboarding = serializers.BooleanField()

    def get_identity(self, obj):
        return UserIdentitySerializer(obj["user"]).data

    def get_avatar(self, obj):
        user = obj["user"]
        payload = getattr(user, "_avatar_payload", None) or _avatar_payload(user)
        return payload


class ProfilePatchSerializer(serializers.Serializer):
    """Only backend-supported, server-validated editable fields."""

    display_name = serializers.CharField(max_length=64, allow_blank=True, required=False)
    bio = serializers.CharField(max_length=300, allow_blank=True, required=False)
    language = serializers.CharField(max_length=35, allow_blank=True, required=False)
    country = serializers.CharField(max_length=60, allow_blank=True, required=False)
    skill_level = serializers.ChoiceField(
        choices=(
            "",
            "novice",
            "casual",
            "intermediate",
            "competitive",
            "pro",
        ),
        required=False,
    )


class StackOverviewSerializer(serializers.Serializer):
    """Real Stack overview — level/XP ring + genuine aggregate stats."""

    identity = serializers.SerializerMethodField()
    level = serializers.IntegerField()
    xp = serializers.IntegerField()
    xp_into_level = serializers.IntegerField()
    xp_needed_for_next = serializers.IntegerField()
    progress_fraction = serializers.FloatField()
    stats = serializers.DictField()

    def get_identity(self, obj):
        return UserIdentitySerializer(obj["user"]).data


class StackProgressSerializer(serializers.Serializer):
    """Real level/XP progression breakdown + game/challenge/tournament progress."""

    identity = serializers.SerializerMethodField()
    level = serializers.IntegerField()
    xp = serializers.IntegerField()
    xp_into_level = serializers.IntegerField()
    xp_needed_for_next = serializers.IntegerField()
    progress_fraction = serializers.FloatField()
    game_progress = serializers.DictField()
    challenge_progress = serializers.DictField()
    tournament_progress = serializers.DictField()

    def get_identity(self, obj):
        return UserIdentitySerializer(obj["user"]).data


class StackAchievementsSerializer(serializers.Serializer):
    """Real achievement collection — sorted, real unlock state, real timestamps."""

    identity = serializers.SerializerMethodField()
    unlocked = serializers.IntegerField()
    total = serializers.IntegerField()
    items = serializers.ListField(child=serializers.DictField())

    def get_identity(self, obj):
        return UserIdentitySerializer(obj["user"]).data


class StackActivitySerializer(serializers.Serializer):
    """Real chronological activity feed, paginated server-side."""

    identity = serializers.SerializerMethodField()
    events = serializers.ListField(child=serializers.DictField())
    per_page = serializers.IntegerField()
    total = serializers.IntegerField()
    has_more = serializers.BooleanField()

    def get_identity(self, obj):
        return UserIdentitySerializer(obj["user"]).data


class StackMilestonesSerializer(serializers.Serializer):
    """Real milestone timeline — only genuine progression events."""

    identity = serializers.SerializerMethodField()
    milestones = serializers.ListField(child=serializers.DictField())

    def get_identity(self, obj):
        return UserIdentitySerializer(obj["user"]).data
