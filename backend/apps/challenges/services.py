"""Vector Strike Challenges — real transactional services (Phase 11).

The backend owns every challenge rule: creation, invitations (real rows via
ChallengeInvitation), rooms with secure unpredictable codes and real members,
teams with real members, readiness, participation, scores, ranks and results.
No player, team, invite, room, score, rank or result ever exists except as a
real row the backend created. Clients can never write players, invites, teams,
scores, ranks, results or rooms into a challenge.
"""

import secrets as _secrets
import uuid as _uuid
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from apps.challenges.models import (
    Challenge,
    ChallengeInvitation,
    ChallengeParticipant,
    ChallengeRoom,
    ChallengeRoomMember,
    ChallengeTeam,
    ChallengeTeamMember,
)


class ChallengeValidationError(Exception):
    """A real business-rule rejection the backend owns (surfaced as 4xx)."""


def _now():
    return timezone.now()


def _slug_from_title(title, used):
    base = slugify(title)[:56] or "challenge"
    slug = base
    n = 1
    while slug in used or Challenge.objects.filter(slug=slug).exists():
        n += 1
        slug = f"{base[:50]}-{n}"
    return slug


@transaction.atomic
def create_challenge(creator, *, title, slug=None, game_slug=None,
                     challenge_type="solo", visibility="friends",
                     description="", invitee_username="",
                     maximum_participants=4, rules=None):
    """The only way a real challenge comes into existence: a real row.

    A real creator always becomes a real ChallengeParticipant (ACTIVE). A real
    invited member becomes a real ChallengeInvitation row only �?" nothing
    else; that member joins the challenge only by accepting for real.
    """
    from apps.games.models import Game

    title = (title or "").strip()
    if not title:
        raise ChallengeValidationError("Give the challenge a real title.")
    if len(title) > 120:
        raise ChallengeValidationError("Keep the title under 120 characters.")

    game = Game.objects.filter(slug=game_slug).first()
    if game is None:
        raise ChallengeValidationError("Choose a game that really exists.")

    final_slug = slug or _slug_from_title(title, set())
    if Challenge.objects.filter(slug=final_slug).exists():
        final_slug = _slug_from_title(title, set())
        # collision resolved above; guaranteed fresh by the loop

    max_participants = min(max(2, int(maximum_participants or 4)), 16)
    challenge = Challenge.objects.create(
        slug=final_slug,
        title=title,
        description=(description or "").strip()[:4000],
        creator=creator,
        game=game,
        challenge_type=challenge_type if challenge_type in ("solo", "team", "friend") else "solo",
        visibility=visibility if visibility in ("private", "friends", "public") else "friends",
        maximum_participants=max_participants,
        rules=rules or {},
        status=Challenge.Status.OPEN,
        start_at=_now(),
        expires_at=_now() + timedelta(days=14),
    )
    ChallengeParticipant.objects.create(
        challenge=challenge,
        user=creator,
        status=ChallengeParticipant.Status.ACTIVE,
    )

    invitee = (
        get_user_model()
        .objects.filter(username__iexact=(invitee_username or "").strip())
        .exclude(pk=creator.pk)
        .first()
    )
    if invitee is not None:
        ChallengeInvitation.objects.create(
            challenge=challenge,
            sender=creator,
            recipient=invitee,
            status=ChallengeInvitation.Status.PENDING,
        )
    return challenge


@transaction.atomic
def leave_challenge(challenge, user):
    """A real member really leaves a real challenge (row-level truth)."""
    participant = (
        challenge.participants.filter(user=user)
        .select_for_update()
        .first()
    )
    if participant is None:
        raise ChallengeValidationError("You are not part of this challenge.")
    active_host = challenge.participants.filter(
        status=ChallengeParticipant.Status.ACTIVE
    ).exclude(user=user)
    if not active_host.exists() and not challenge.participants.filter(user=user).exclude(
        pk=participant.pk
    ).exists():
        challenge.status = Challenge.Status.CANCELLED
        challenge.save(update_fields=["status"])
    participant.status = ChallengeParticipant.Status.LEFT
    participant.save(update_fields=["status"])
    return participant


def create_room(challenge, user, *, maximum_participants=4):
    """A real, code-addressed lobby row + a real host member row."""
    room = ChallengeRoom.objects.create(
        challenge=challenge,
        host=user,
        room_code=ChallengeRoom.generate_room_code(),
        status=ChallengeRoom.Status.WAITING,
        maximum_participants=max(2, min(int(maximum_participants or 4), 16)),
        expires_at=_now() + timedelta(hours=12),
    )
    ChallengeRoomMember.objects.create(
        room=room, user=user, status=ChallengeRoomMember.Status.ACTIVE,
        is_host=True, is_ready=False,
    )
    return room


def join_room(room, user):
    """Join a real, open, code-addressed lobby as a real member."""
    if room.status not in (ChallengeRoom.Status.WAITING,):
        raise ChallengeValidationError("This room is not accepting players.")
    existing = room.members.filter(user=user).first()
    if existing is not None and existing.status == ChallengeRoomMember.Status.ACTIVE:
        raise ChallengeValidationError("You are already in this room.")
    if (
        room.members.filter(status=ChallengeRoomMember.Status.ACTIVE).count()
        >= room.maximum_participants
    ):
        raise ChallengeValidationError("This room is full.")
    member, _ = ChallengeRoomMember.objects.update_or_create(
        room=room,
        user=user,
        defaults={"status": ChallengeRoomMember.Status.ACTIVE, "is_host": False},
    )
    return member


def leave_room(room, user):
    member = room.members.filter(user=user, status=ChallengeRoomMember.Status.ACTIVE).first()
    if member is None:
        raise ChallengeValidationError("You are not in this room.")
    member.status = ChallengeRoomMember.Status.LEFT
    member.save(update_fields=["status"])
    return member


def set_ready(room, user, ready=True):
    member = room.members.filter(user=user, status=ChallengeRoomMember.Status.ACTIVE).first()
    if member is None:
        raise ChallengeValidationError("You are not in this room.")
    member.is_ready = bool(ready)
    member.save(update_fields=["is_ready"])
    return member


def accept_invitation(challenge, user):
    """Accepting a real invitation turns a real invite into a real ACTIVE part."""
    invite = (
        challenge.invitations.filter(recipient=user)
        .select_for_update()
        .order_by("-created_at")
        .first()
    )
    if invite is None or invite.status != ChallengeInvitation.Status.PENDING:
        raise ChallengeValidationError("You have no pending invitation here.")
    invite.status = ChallengeInvitation.Status.ACCEPTED
    invite.responded_at = _now()
    invite.save(update_fields=["status", "responded_at"])
    participant, _ = ChallengeParticipant.objects.get_or_create(
        challenge=challenge,
        user=user,
        defaults={"status": ChallengeParticipant.Status.ACTIVE},
    )
    return participant


def decline_invitation(challenge, user):
    invite = (
        challenge.invitations.filter(recipient=user)
        .select_for_update()
        .order_by("-created_at")
        .first()
    )
    if invite is None or invite.status != ChallengeInvitation.Status.PENDING:
        raise ChallengeValidationError("You have no pending invitation here.")
    invite.status = ChallengeInvitation.Status.DECLINED
    invite.responded_at = _now()
    invite.save(update_fields=["status", "responded_at"])
    return invite


def record_result(challenge, participant, *, score=None, rank=None, result_data=None):
    """Record a real result row after the game truly completes."""
    from apps.challenges.models import ChallengeResult

    return ChallengeResult.objects.create(
        challenge=challenge,
        participant=participant,
        score=score if score is not None else 0,
        rank=rank,
        result_data=result_data or {},
    )
