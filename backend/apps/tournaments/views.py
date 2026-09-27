"""Vector Strike Tournaments API (Phase 11).

Every value is derived from genuine tournament/participant/result rows in
PostgreSQL �?" no fabricated events, no invented competitors, no client-owned
eligibility, no client-supplied membership. Participation (join/leave), age
eligibility, availability, duplication and full-capacity handling are always
decided server-side in a transaction.
"""

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.tournaments import serializers as t_serializers
from apps.tournaments import services as t_services
from apps.tournaments.models import Tournament, TournamentParticipant


def _qs():
    now = timezone.now()
    return (
        Tournament.objects.select_related("game")
        .prefetch_related("rules", "rounds")
        .annotate(
            participant_count=Count(
                "participants",
                filter=Q(participants__status=TournamentParticipant.Status.ACTIVE),
            )
        )
        .order_by("-is_featured", "start_at")
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def tournament_list_view(request):
    """Live rails: featured, live, upcoming, ending soon, completed, mine."""
    now = timezone.now()
    qs = _qs().filter(
        status__in=[Tournament.Status.UPCOMING, Tournament.Status.LIVE, Tournament.Status.COMPLETED]
    )
    featured = list(qs.filter(is_featured=True)[:8])
    live = _live_payload(qs, now)
    upcoming = _upcoming_payload(qs, now)
    ending = _ending_payload(qs, now)
    completed = _completed_payload(qs, now)

    mine_qs = _qs().filter(participants__user=request.user)
    mine = [
        t_serializers.tournament_payload(t, request.user)
        for t in mine_qs[:20]
    ]

    return Response(
        {
            "featured": [t_serializers.tournament_payload(t, request.user) for t in featured],
            "live_now": live,
            "upcoming": upcoming,
            "ending_soon": ending,
            "my_tournaments": mine,
            "completed": completed,
            "rails": ["featured", "live_now", "upcoming", "ending_soon", "my_tournaments", "completed"],
        }
    )


def _live_payload(qs, now):
    return [
        t_serializers.tournament_payload(t, request_user=request.user)
        for t in qs.filter(
            status=Tournament.Status.LIVE,
            start_at__lte=now,
            end_at__gte=now,
        )[:20]
    ]


def _upcoming_payload(qs, now):
    return [
        t_serializers.tournament_payload(t, request.user)
        for t in qs.filter(
            status__in=[Tournament.Status.UPCOMING, Tournament.Status.LIVE],
            start_at__gt=now,
        )[:20]
    ]


def _ending_payload(qs, now):
    return [
        t_serializers.tournament_payload(t, request.user)
        for t in qs.filter(
            status__in=[Tournament.Status.LIVE, Tournament.Status.ENDING_SOON],
            end_at__lte=now + timezone.timedelta(hours=6),
            end_at__gte=now,
        )[:20]
    ]


def _completed_payload(qs, now):
    return [
        t_serializers.tournament_payload(t, request.user)
        for t in qs.filter(status=Tournament.Status.COMPLETED, end_at__lt=now)[:20]
    ]


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def tournament_detail_view(request, slug):
    tournament = _qs().filter(slug=slug).first()
    if tournament is None:
        return Response({"detail": "Tournament not found."}, status=404)
    return Response(t_serializers.tournament_detail_payload(tournament, request.user))


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def tournament_join_view(request, slug):
    """Server-authoritative join with eligibility + availability + duplicate checks."""
    tournament = _qs().filter(slug=slug).first()
    if tournament is None:
        return Response({"detail": "Tournament not found."}, status=404)
    try:
        participant = t_services.join_tournament(tournament, request.user)
    except t_services.TournamentEligibilityError as exc:
        return Response({"detail": str(exc)}, status=409)
    return Response(participant, status=201)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def tournament_leave_view(request, slug):
    tournament = _qs().filter(slug=slug).first()
    if tournament is None:
        return Response({"detail": "Tournament not found."}, status=404)
    try:
        participant = t_services.leave_tournament(tournament, request.user)
    except t_services.TournamentEligibilityError as exc:
        return Response({"detail": str(exc)}, status=409)
    return Response(participant)
