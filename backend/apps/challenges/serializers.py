"""Vector Strike Challenges — real API payloads (Phase 11).

Every card is built only from real relational rows the backend owns: a real
Challenge, real ChallengeParticipant rows, real ChallengeInvitation rows, real
ChallengeRoom/ChallengeRoomMember rows, real ChallengeTeam/ChallengeTeamMember
rows and real ChallengeResult rows. Nothing is fabricated, invited, hosted,
waiting, ready, scored, ranked or completed unless a real row says so.
"""

from datetime import timedelta

from django.utils import timezone

from rest_framework import serializers

from apps.accounts.serializers import UserIdentitySerializer
from apps.challenges.models import (
    Challenge,
    ChallengeInvitation,
    ChallengeParticipant,
    ChallengeResult,
    ChallengeRoom,
    ChallengeRoomMember,
    ChallengeTeam,
    ChallengeTeamMember,
)


def _id(user):
    return UserIdentitySerializer(user).data


def _room_member(m):
    return {
        **_id(m.user),
        "is_host": m.is_host,
        "is_ready": m.is_ready,
        "joined_at": m.joined_at.isoformat(),
        "ready_at": m.ready_at.isoformat() if m.ready_at else None,
    }


def room_payload(room, user):
    """A real lobby from real rows: code, host, live members, my flags."""
    members = [
        _room_member(m)
        for m in room.members.select_related("user__profile").order_by("joined_at")
    ]
    return {
        "id": str(room.id),
        "room_code": room.room_code,
        "status": room.status,
        "host": _id(room.host),
        "host_is_me": room.host_id == user.id,
        "maximum_participants": room.maximum_participants,
        "member_count": len(members),
        "members": members,
        "my_member": next(
            (m for m in members if m.get("username") == user.username), None
        ),
        "created_at": room.created_at.isoformat(),
        "expires_at": room.expires_at.isoformat() if room.expires_at else None,
    }


def challenge_payload(challenge, user):
    """A real challenge card from real rows (never invented)."""
    my_part = challenge.participants.filter(user=user).first()
    invite = (
        challenge.invitations.filter(recipient=user).order_by("-created_at").first()
        if hasattr(challenge, "invitations")
        else None
    )
    open_room = challenge.rooms.filter(status=ChallengeRoom.Status.WAITING).first()
    return {
        "id": str(challenge.id),
        "slug": challenge.slug,
        "title": challenge.title,
        "description": challenge.description,
        "game": {"slug": challenge.game.slug, "title": challenge.game.title},
        "creator": _id(challenge.creator),
        "challenge_type": challenge.challenge_type,
        "status": challenge.status,
        "visibility": challenge.visibility,
        "participant_count": challenge.participants.count(),
        "maximum_participants": challenge.maximum_participants,
        "start_at": challenge.start_at.isoformat() if challenge.start_at else None,
        "expires_at": challenge.expires_at.isoformat() if challenge.expires_at else None,
        "created_at": challenge.created_at.isoformat(),
        "my_status": my_part.status if my_part else None,
        "my_invitation": (invite.status if invite else None),
        "room": room_payload(open_room, user) if open_room else None,
    }


def challenge_detail_payload(challenge, user):
    """Real detail: real participants, invites, rooms, teams, results."""
    payload = challenge_payload(challenge, user)
    parts = (
        challenge.participants.select_related("user__profile")
        .order_by("joined_at")
    )
    payload["participants"] = [
        {
            **_id(p.user),
            "status": p.status,
            "score": p.score,
            "rank": p.rank,
            "joined_at": p.joined_at.isoformat(),
            "ready_at": p.ready_at.isoformat() if p.ready_at else None,
        }
        for p in parts
    ]
    invites = challenge.invitations.select_related(
        "sender__profile", "recipient__profile"
    ).order_by("-created_at")
    payload["invitations"] = [
        {
            "id": str(i.id),
            "sender": _id(i.sender),
            "recipient": _id(i.recipient),
            "status": i.status,
            "message": i.message,
            "created_at": i.created_at.isoformat(),
            "responded_at": i.responded_at.isoformat() if i.responded_at else None,
        }
        for i in invites
    ]
    rooms = challenge.rooms.select_related("host__profile").order_by("-created_at")
    payload["rooms"] = [room_payload(r, user) for r in rooms]
    teams = challenge.teams.prefetch_related("members__user__profile").order_by("created_at")
    payload["teams"] = [
        {
            "id": str(t.id),
            "name": t.name,
            "members": [
                {
                    **_id(m.user),
                    "is_ready": m.is_ready,
                    "joined_at": m.joined_at.isoformat(),
                }
                for m in t.members.order_by("joined_at")
            ],
        }
        for t in teams
    ]
    results = challenge.results.select_related(
        "participant__user__profile"
    ).order_by("-score")
    payload["results"] = [
        {
            "id": str(r.id),
            "participant": _id(r.participant.user),
            "score": r.score,
            "rank": r.rank,
            "result_data": r.result_data,
            "completed_at": r.completed_at.isoformat(),
        }
        for r in results
    ]
    return payload


class ChallengeCreateSerializer(serializers.Serializer):
    """Structural validation only — every business rule stays server-side."""

    title = serializers.CharField(max_length=120, allow_blank=False)
    slug = serializers.SlugField(required=False, allow_blank=True)
    game_slug = serializers.SlugField()
    challenge_type = serializers.ChoiceField(
        choices=["solo", "team", "friend"], default="solo"
    )
    visibility = serializers.ChoiceField(
        choices=[v.value for v in Challenge.Visibility], default=Challenge.Visibility.FRIENDS
    )
    description = serializers.CharField(
        required=False, allow_blank=True, max_length=4000, default=""
    )
    invitee_username = serializers.CharField(
        required=False, allow_blank=True, max_length=120, default=""
    )
    rules = serializers.JSONField(required=False, default=dict)
