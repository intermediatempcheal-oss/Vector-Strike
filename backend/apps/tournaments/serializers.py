from rest_framework import serializers

"""Vector Strike Tournaments ï¿½?" JSON payloads.

Pure functions that produce the exact shape the Vector Strike frontend renders.
Every number is read from a real Tournament/TournamentParticipant/TournamentResult
row (or derived from genuine timestamps). None of these helpers invent members,
scores, ranks or participation state.
"""

from datetime import timedelta

from django.utils import timezone

from apps.tournaments.models import Tournament, TournamentParticipant


def live_status(tournament, now=None):
    """Backend-derivable status from real timestamps (never client-set)."""
    now = now or timezone.now()
    if tournament.status == Tournament.Status.CANCELLED:
        return tournament.status
    if tournament.status == Tournament.Status.COMPLETED:
        return tournament.status
    if tournament.start_at is None:
        return Tournament.Status.DRAFT
    if now < tournament.start_at and tournament.start_at - now <= timedelta(hours=24):
        return Tournament.Status.UPCOMING
    if tournament.start_at <= now:
        if tournament.end_at and now >= tournament.end_at:
            return Tournament.Status.COMPLETED
        if tournament.end_at and tournament.end_at - now <= timedelta(hours=6):
            return Tournament.Status.ENDING_SOON
        return Tournament.Status.LIVE
    return Tournament.Status.UPCOMING


def identity_payload(user):
    from apps.accounts.serializers import UserIdentitySerializer

    return UserIdentitySerializer(user).data


def tournament_payload(tournament, user):
    """Card-level (and list-level) tournament representation."""

    def _status_label(status):
        return {
            "upcoming": "Upcoming",
            "live": "Live Now",
            "ending_soon": "Ending Soon",
            "completed": "Completed",
            "cancelled": "Cancelled",
            "draft": "Draft",
        }.get(status, status)

    now = timezone.now()
    status = live_status(tournament, now)
    participant_count = tournament.participants.filter(
        status__in=[TournamentParticipant.Status.ACTIVE]
    ).count()
    joined = tournament.participants.filter(
        user=user,
        status__in=[TournamentParticipant.Status.ACTIVE],
    ).exists()
    entry_action = None
    if status in (Tournament.Status.UPCOMING, Tournament.Status.LIVE, Tournament.Status.ENDING_SOON):
        entry_action = "continue" if joined else "join"

    return {
        "slug": tournament.slug,
        "title": tournament.title,
        "description": tournament.description,
        "banner": tournament.banner or "",
        "thumbnail": tournament.thumbnail or "",
        "phase": tournament.phase,
        "category": tournament.category or "",
        "game": {
            "slug": tournament.game.slug if tournament.game else "",
            "title": tournament.game.title if tournament.game else "",
        },
        "status": status,
        "status_label": _status_label(status),
        "start_at": tournament.start_at.isoformat() if tournament.start_at else None,
        "end_at": tournament.end_at.isoformat() if tournament.end_at else None,
        "registration_opens_at": (
            tournament.registration_opens_at.isoformat()
            if tournament.registration_opens_at
            else None
        ),
        "registration_closes_at": (
            tournament.registration_closes_at.isoformat()
            if tournament.registration_closes_at
            else None
        ),
        "participant_count": participant_count,
        "maximum_participants": tournament.maximum_participants,
        "minimum_age": tournament.minimum_age,
        "maximum_age": tournament.maximum_age,
        "prize_pool": tournament.prize_pool or {},
        "entry_type": tournament.entry_type,
        "entry_requirement": tournament.entry_requirement or "",
        "joined": joined,
        "entry_action": entry_action,
        "format": tournament.format,
        "is_featured": tournament.is_featured,
    }


def tournament_detail_payload(tournament, user):
    data = tournament_payload(tournament, user)
    data["rules"] = [
        {
            "title": rule.title,
            "body": rule.body,
            "sort_order": rule.sort_order,
        }
        for rule in tournament.rules.all()
    ]
    data["rounds"] = [
        {
            "number": rnd.number,
            "label": rnd.label,
            "starts_at": rnd.starts_at.isoformat() if rnd.starts_at else None,
            "ends_at": rnd.ends_at.isoformat() if rnd.ends_at else None,
            "status": rnd.status,
        }
        for rnd in tournament.rounds.all()
    ]
    data["participants"] = [
        {
            "username": p.user.username,
            "display_name": getattr(p.user.profile, "display_name", "") or p.user.username,
            "avatar": getattr(getattr(p.user, "profile", None), "avatar", "") or "",
            "status": p.status,
            "joined_at": p.joined_at.isoformat() if p.joined_at else None,
        }
        for p in tournament.participants.filter(
            status__in=[TournamentParticipant.Status.ACTIVE]
        ).select_related("user__profile")[:24]
    ]
    participant = tournament.participants.filter(
        user=user, status__in=[TournamentParticipant.Status.ACTIVE]
    ).first()
    data["my_participation"] = None
    if participant:
        data["my_participation"] = {
            "status": participant.status,
            "joined_at": participant.joined_at.isoformat() if participant.joined_at else None,
            "score": participant.score,
            "rank": participant.rank,
        }
    return data


