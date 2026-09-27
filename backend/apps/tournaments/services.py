"""Vector Strike Tournaments �?" transactional domain services.

Backend owns eligibility, availability, join/leave and duplicate prevention.
No member, score, rank, participant or result is ever fabricated or derived
from the frontend.
"""

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from apps.tournaments.models import Tournament, TournamentParticipant
from apps.tournaments import serializers as t_serializers


def _age_tier(user_age, tournament):
    if user_age is None:
        return False, None, "Your age has not been recorded"
    if tournament.minimum_age and user_age < tournament.minimum_age:
        return False, None, f"You must be at least {tournament.minimum_age}"
    if tournament.maximum_age and user_age > tournament.maximum_age:
        return False, None, f"Not eligible above {tournament.maximum_age}"
    return True, user_age, ""


def _availability(tournament, now):
    status = t_serializers.live_status(tournament, now)
    if status in (Tournament.Status.CANCELLED, Tournament.Status.COMPLETED):
        return False, "This tournament is no longer open"
    if status == Tournament.Status.UPCOMING:
        if (
            tournament.registration_opens_at
            and now < tournament.registration_opens_at
        ):
            return False, "Registration has not opened yet"
    if (
        tournament.registration_closes_at
        and now > tournament.registration_closes_at
    ):
        return False, "Registration has closed"
    if tournament.maximum_participants and (
        tournament.participants.filter(
            status__in=[TournamentParticipant.Status.ACTIVE]
        ).count()
        >= tournament.maximum_participants
    ):
        return False, "This tournament is full"
    return True, ""


def join_tournament(tournament, user):
    """Server-side join with eligibility, availability and duplicate checks.

    Transaction-safe: uniqueness is enforced by DB constraint + select-for-update
    inside the transaction. Raises ``TournamentEligibilityError`` on rejection.
    """
    now = timezone.now()
    profile = getattr(user, "profile", None)
    user_age = getattr(profile, "age", None) if profile else None

    eligible, _age, age_msg = _age_tier(user_age, tournament)
    if not eligible:
        raise TournamentEligibilityError(age_msg)
    available, avail_msg = _availability(tournament, now)
    if not available:
        raise TournamentEligibilityError(avail_msg)

    with transaction.atomic():
        dup = (
            TournamentParticipant.objects.select_for_update()
            .filter(tournament=tournament, user=user)
            .first()
        )
        if dup:
            if dup.status == TournamentParticipant.Status.LEFT:
                dup.status = TournamentParticipant.Status.ACTIVE
                dup.joined_at = now
                dup.save(update_fields=["status", "joined_at", "updated_at"])
                return _participation_payload(dup)
            raise TournamentEligibilityError("You have already joined this tournament")
        participant = TournamentParticipant.objects.create(
            tournament=tournament,
            user=user,
            status=TournamentParticipant.Status.ACTIVE,
        )
    return _participation_payload(participant)


def leave_tournament(tournament, user):
    """Server-side leave. Only an actual participant can leave."""
    now = timezone.now()
    with transaction.atomic():
        participant = (
            TournamentParticipant.objects.select_for_update()
            .filter(tournament=tournament, user=user)
            .first()
        )
        if participant is None or participant.status == TournamentParticipant.Status.LEFT:
            raise TournamentEligibilityError("You are not a participant in this tournament")
        participant.status = TournamentParticipant.Status.LEFT
        participant.updated_at = now
        participant.save(update_fields=["status", "updated_at"])
    return _participation_payload(participant)


def _participation_payload(participant):
    return {
        "slug": participant.tournament.slug,
        "status": participant.status,
        "joined_at": participant.joined_at.isoformat() if participant.joined_at else None,
    }


def eligible_for(user, now=None):
    now = now or timezone.now()
    profile = getattr(user, "profile", None)
    user_age = getattr(profile, "age", None) if profile else None
    qs = Tournament.objects.filter(status__in=[Tournament.Status.UPCOMING, Tournament.Status.LIVE])
    ids = []
    for tournament in qs.select_related("game")[:50]:
        age_ok, _, _ = _age_tier(user_age, tournament)
        avail, _ = _availability(tournament, now)
        joined = tournament.participants.filter(
            user=user, status__in=[TournamentParticipant.Status.ACTIVE]
        ).exists()
        if (age_ok and avail) or joined:
            ids.append(tournament.id)
    return list(Tournament.objects.filter(id__in=ids).select_related("game"))


class TournamentEligibilityError(Exception):
    """A typed, member-safe rejection from the backend (never a client guess)."""

    def __init__(self, detail):
        self.detail = detail
        super().__init__(detail)
