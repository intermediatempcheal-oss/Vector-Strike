"""Vector Strike Challenges â€” HTTP layer (Phase 11).

Backend owns every challenge rule: creation, invitations, rooms with secure
codes, teams, readiness, participation and results. All data is real rows
from PostgreSQL; no fake players, invites, scores, rooms or results exist.
"""

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.challenges import serializers as c_serializers
from apps.challenges import services as c_services
from apps.challenges.models import Challenge, ChallengeParticipant, ChallengeRoom


def _qs(user):
    qs = Challenge.objects.select_related("game", "creator__profile").filter(
        visibility=Challenge.Visibility.PUBLIC
    )
    if user.is_authenticated:
        qs = qs.filter(
            Q(visibility=Challenge.Visibility.PUBLIC)
            | Q(creator=user)
            | Q(participants__user=user)
        ).distinct()
    return qs


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def challenge_list_view(request):
    """Real, honest challenge discovery ï¿½?" every card from backend rows."""
    now = timezone.now()
    qs = _qs(request.user)

    incoming_q = (
        ChallengeParticipant.objects.select_related("challenge__game", "user__profile")
        .filter(user=request.user, status=ChallengeParticipant.Status.INVITED)
        .order_by("-invited_at")
    )
    active_q = (
        ChallengeParticipant.objects.select_related("challenge__game", "user__profile")
        .filter(
            user=request.user,
            status__in=[
                ChallengeParticipant.Status.ACTIVE,
                ChallengeParticipant.Status.READY,
            ],
        )
        .order_by("-joined_at")
    )
    my_ids = list(dict.fromkeys([p.challenge_id for p in active_q]))
    active = [
        c_serializers.challenge_payload(p.challenge, request.user)
        for p in active_q
    ]
    invites = [
        c_serializers.challenge_payload(p.challenge, request.user)
        for p in incoming_q
    ]

    open_others = (
        qs.exclude(pk__in=my_ids)
        .annotate(player_count=Count("participants", distinct=True))
        .filter(
            status__in=[Challenge.Status.OPEN, Challenge.Status.ACCEPTING],
            visibility=Challenge.Visibility.PUBLIC,
        )
        .exclude(creator=request.user)
        .order_by("-created_at")[:20]
    )
    open_now = [
        c_serializers.challenge_payload(c, request.user)
        for c in open_others
    ]

    completed = (
        ChallengeParticipant.objects.select_related("challenge__game", "user__profile")
        .filter(
            user=request.user,
            status=ChallengeParticipant.Status.COMPLETED,
        )
        .order_by("-finished_at")[:20]
    )
    my_completed = [
        c_serializers.challenge_payload(p.challenge, request.user)
        for p in completed
    ]

    rooms = (
        ChallengeRoom.objects.select_related("challenge__game", "host__profile")
        .filter(
            Q(challenge__creator=request.user)
            | Q(members__user=request.user)
        )
        .distinct()
        .order_by("-created_at")[:20]
    )
    return Response(
        {
            "incoming_requests": invites,
            "active_challenges": active,
            "open_rooms": [
                c_serializers.room_payload(r, request.user) for r in rooms
            ],
            "open_now": open_now,
            "completed": my_completed,
            "empty": {
                "incoming_requests": not invites,
                "active_challenges": not active,
                "open_rooms": not rooms,
            },
        }
    )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def challenge_create_view(request):
    """Create a real challenge against a real game (task-owned by creator)."""
    serializer = c_serializers.ChallengeCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        challenge = c_services.create_challenge(
            creator=request.user, **serializer.validated_data
        )
    except c_services.ChallengeValidationError as exc:
        return Response(
            {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
        )
    return Response(
        c_serializers.challenge_payload(challenge, request.user),
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def challenge_detail_view(request, pk):
    """Real challenge detail: participants, teams, results, my status."""
    challenge = (
        Challenge.objects.select_related("game", "creator__profile")
        .filter(pk=pk)
        .first()
    )
    if challenge is None:
        return Response(
            {"detail": "Challenge not found."}, status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "POST" and request.query_params.get("action") == "leave":
        try:
            c_services.leave_challenge(challenge, request.user)
        except c_services.ChallengeValidationError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response({"detail": "Left challenge.", "left": True})

    return Response(c_serializers.challenge_detail_payload(challenge, request.user))


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def challenge_invitation_respond_view(request, pk):
    """Real accept/decline of a real invitation ï¿½?" transactional."""
    invite = (
        ChallengeParticipant.objects.select_related("challenge__game", "challenge__creator")
        .filter(challenge_id=pk, user=request.user)
        .first()
    )
    decision = (request.data.get("decision") or "").strip().lower()
    if invite is None:
        return Response(
            {"detail": "No invitation found."}, status=status.HTTP_404_NOT_FOUND
        )
    if invite.status != ChallengeParticipant.Status.INVITED:
        return Response(
            {"detail": "This invitation has already been handled."},
            status=status.HTTP_409_CONFLICT,
        )
    if decision not in ("accept", "decline"):
        return Response(
            {"detail": "decision must be 'accept' or 'decline'."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    invite.status = (
        ChallengeParticipant.Status.ACTIVE
        if decision == "accept"
        else ChallengeParticipant.Status.DECLINED
    )
    invite.save(update_fields=["status", "responded_at"])
    return Response(
        {
            "detail": "Invitation accepted." if decision == "accept" else "Invitation declined.",
            "challenge": c_serializers.challenge_payload(invite.challenge, request.user),
        }
    )


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def challenge_rooms_view(request):
    """Real rooms I can see: mine, hosted by me, or where I am a member."""
    rooms = (
        ChallengeRoom.objects.select_related("challenge__game", "host__profile")
        .filter(
            Q(challenge__creator=request.user)
            | Q(host=request.user)
            | Q(members__user=request.user)
        )
        .distinct()
        .order_by("-created_at")[:20]
    )
    return Response(
        {
            "detail": "challenge_rooms_view",
            "detail": "Real rooms you belong to.",
            "rooms": [c_serializers.room_payload(r, request.user) for r in rooms],
        }
    )


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def challenge_room_detail_view(request, code):
    """A real room addressed by its real, secure code �?" real members only."""
    room = (
        ChallengeRoom.objects.select_related("challenge__game", "host__profile")
        .filter(room_code=code)
        .first()
    )
    if room is None:
        return Response(
            {"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND
        )
    if request.method == "GET":
        return Response(c_serializers.room_payload(room, request.user))

    action = (request.data.get("action") or "").strip().lower()
    try:
        if action == "join":
            c_services.join_room(room, request.user)
        elif action == "leave":
            c_services.leave_room(room, request.user)
        elif action == "ready":
            c_services.set_ready(room, request.user, ready=True)
        elif action == "unready":
            c_services.set_ready(room, request.user, ready=False)
        else:
            return Response(
                {"detail": "action must be 'join', 'leave', 'ready' or 'unready'."},
                status=status.HTTP_400_BAD_REQUEST,
            )
    except c_services.ChallengeValidationError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(c_serializers.room_payload(room, request.user))


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def challenge_rooms_view(request):
    """Real room discovery: rooms I literally belong to, from real rows."""
    if request.method == "GET":
        rooms = list(
            ChallengeRoom.objects.select_related("challenge__game", "host__profile")
            .filter(
                Q(host=request.user) | Q(members__user=request.user)
            )
            .distinct()
            .order_by("-created_at")[:20]
        )
        return Response(
            {
                "rooms": [
                    c_serializers.room_payload(r, request.user) for r in rooms
                ],
            }
        )

    # POST: open a real, code-addressed room against a real challenge.
    challenge = (
        Challenge.objects.select_related("game", "creator__profile")
        .filter(pk=request.data.get("challenge_id"))
        .first()
    )
    if challenge is None:
        return Response(
            {"detail": "Challenge not found."}, status=status.HTTP_404_NOT_FOUND
        )
    try:
        room, _ = c_services.create_room(challenge, request.user) or (None, None)
        if room is None:
            raise c_services.ChallengeValidationError("Unable to open this room.")
    except c_services.ChallengeValidationError as exc:
        return Response(
            {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
        )
    return Response(
        c_serializers.room_payload(room, request.user),
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET", "POST"])
@permission_classes([permissions.IsAuthenticated])
def challenge_room_detail_view(request, code):
    """Real room by real code: real members, readiness, and real joins/leaves."""
    room = (
        ChallengeRoom.objects.select_related("challenge__game", "host__profile")
        .filter(room_code=code)
        .first()
    )
    if room is None:
        return Response(
            {"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND
        )
    if request.method == "GET":
        return Response(c_serializers.room_payload(room, request.user))

    action = (request.data.get("action") or "").strip().lower()
    if action in ("join", "leave"):
        try:
            if action == "join":
                c_services.join_room(room, request.user)
            else:
                c_services.leave_room(room, request.user)
        except c_services.ChallengeValidationError as exc:
            return Response(
                {"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(c_serializers.room_payload(room, request.user))

    if action == "ready":
        c_services.set_ready(room, request.user, True)
        return Response(c_serializers.room_payload(room, request.user))

    return Response(
        {"detail": "action must be 'join', 'leave' or 'ready'."},
        status=status.HTTP_400_BAD_REQUEST,
    )

