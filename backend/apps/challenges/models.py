"""Vector Strike Challenges domain �?" Phase 11.

Direct player-versus-player and team-versus-team competition against real
games. Every challenge, participant, invitation, room, team, member, ready
flag, score, rank and result is a genuine relational row owned by the backend.
Nothing is fabricated, invitations/rooms/participants/{scores,ranks,teams}
always come from real rows and the backend owns eligibility, availability,
joining, leaving, readiness and result recording. API payloads only ever
serialize truth; clients can never write players, teams or scores into a
challenge or its rooms.
"""

import secrets
import string
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.games.models import Game, GameSession


def _now():
    return timezone.now()


class Challenge(models.Model):
    """A real competition between real members on a real game."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        INVITED = "invited", "Invited"
        LIVE = "live", "Live"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    class Visibility(models.TextChoices):
        PRIVATE = "private", "Private"
        FRIENDS = "friends", "Friends"
        PUBLIC = "public", "Public"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=64, unique=True, db_index=True)
    description = models.TextField(blank=True, default="")
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_challenges",
    )
    game = models.ForeignKey(Game, on_delete=models.PROTECT, related_name="challenges")
    game_session = models.ForeignKey(GameSession, on_delete=models.SET_NULL, null=True, blank=True, related_name="challenges")
    challenge_type = models.CharField(max_length=16, default="solo")  # solo | team | friend
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.DRAFT, db_index=True
    )
    visibility = models.CharField(
        max_length=16, choices=Visibility.choices, default=Visibility.FRIENDS
    )
    rules = models.JSONField(default=dict, blank=True)
    start_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "challenges_challenge"
        indexes = [
            models.Index(fields=["status", "-created_at"], name="challenge_status_created"),
            models.Index(fields=["creator", "-created_at"], name="challenge_creator_created"),
        ]

    def __str__(self):
        return self.title


class ChallengeParticipant(models.Model):
    """A real member participating in a real challenge."""

    class Status(models.TextChoices):
        INVITED = "invited", "Invited"
        ACTIVE = "active", "Active"
        LEFT = "left", "Left"
        COMPLETED = "completed", "Completed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="challenge_participations"
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.INVITED, db_index=True
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    score = models.BigIntegerField(default=0)
    rank = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = "challenges_challenge_participant"
        constraints = [
            models.UniqueConstraint(
                fields=["challenge", "user"], name="uniq_challenge_participant_pair"
            )
        ]
        indexes = [
            models.Index(fields=["challenge", "status"], name="challenge_part_status"),
        ]

    def __str__(self):
        return f"{self.user} in {self.challenge.title}"


class ChallengeInvitation(models.Model):
    """A real invitation from one member to another for a real challenge."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name="invitations"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_challenge_invites"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_challenge_invites"
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True
    )
    message = models.CharField(max_length=280, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "challenges_challenge_invitation"
        constraints = [
            models.UniqueConstraint(
                fields=["challenge", "recipient"], name="uniq_challenge_invite_recipient"
            )
        ]

    def __str__(self):
        return f"Invite {self.sender} -> {self.recipient}"


class ChallengeTeam(models.Model):
    """A real displayed team inside a team challenge (members are real)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name="teams"
    )
    name = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "challenges_challenge_team"
        constraints = [
            models.UniqueConstraint(fields=["challenge", "name"], name="uniq_team_per_challenge")
        ]

    def __str__(self):
        return self.name


class ChallengeTeamMember(models.Model):
    """A real member row inside a real team."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(
        ChallengeTeam, on_delete=models.CASCADE, related_name="members"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="challenge_team_memberships"
    )
    is_ready = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "challenges_challenge_team_member"
        constraints = [
            models.UniqueConstraint(fields=["team", "user"], name="uniq_team_member_pair")
        ]

    def __str__(self):
        return f"{self.user} on {self.team.name}"


class ChallengeRoom(models.Model):
    """A real, secure, code-addressed lobby for a challenge."""

    class Status(models.TextChoices):
        WAITING = "waiting", "Waiting"
        READY = "ready", "Ready"
        LIVE = "live", "Live"
        COMPLETED = "completed", "Completed"
        EXPIRED = "expired", "Expired"
        CANCELLED = "cancelled", "Cancelled"

    CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no 0/O/1/I confusion

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name="rooms"
    )
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="hosted_challenge_rooms"
    )
    room_code = models.CharField(max_length=10, unique=True, db_index=True)
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.WAITING, db_index=True
    )
    maximum_participants = models.PositiveIntegerField(default=4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "challenges_challenge_room"
        indexes = [
            models.Index(fields=["status", "room_code"], name="challenge_room_code"),
            models.Index(fields=["host", "-created_at"], name="challenge_room_host"),
        ]

    def __str__(self):
        return f"Room {self.room_code} ({self.status})"

    @staticmethod
    def generate_room_code():
        """Unpredictable, non-sequential, collision-resistant room code."""
        alphabet = ChallengeRoom.CODE_ALPHABET
        for _ in range(200):
            code = "".join(secrets.choice(alphabet) for _ in range(6))
            if not ChallengeRoom.objects.filter(room_code=code).exists():
                return code
        raise RuntimeError("Unable to allocate a room code.")


class ChallengeRoomMember(models.Model):
    """A real member physically present in a real room lobby."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        LEFT = "left", "Left"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(
        ChallengeRoom, on_delete=models.CASCADE, related_name="members"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="challenge_room_memberships"
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.ACTIVE, db_index=True
    )
    is_host = models.BooleanField(default=False)
    is_ready = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    ready_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "challenges_challenge_room_member"
        constraints = [
            models.UniqueConstraint(fields=["room", "user"], name="uniq_room_member_pair")
        ]
        indexes = [
            models.Index(fields=["room", "status"], name="challenge_room_member_status"),
        ]

    def __str__(self):
        return f"{self.user} in {self.room.room_code}"


class ChallengeResult(models.Model):
    """A genuine result recorded when a challenge actually completes."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenge = models.ForeignKey(
        Challenge, on_delete=models.CASCADE, related_name="results"
    )
    participant = models.ForeignKey(
        ChallengeParticipant, on_delete=models.CASCADE, related_name="results"
    )
    score = models.BigIntegerField(default=0)
    rank = models.PositiveIntegerField(null=True, blank=True)
    result_data = models.JSONField(default=dict, blank=True)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "challenges_challenge_result"
        indexes = [
            models.Index(fields=["challenge", "-score"], name="challenge_result_score"),
        ]

    def __str__(self):
        return f"Result {self.score} for {self.challenge.title}"
