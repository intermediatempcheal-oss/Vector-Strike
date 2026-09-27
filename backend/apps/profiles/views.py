"""Profiles API views (Phase 12 ï¿½?ï¿½ Profile + Stack).

Phase 8 gives members a real avatar. Phase 12 adds the rest of the genuine
identity surface ï¿½?" the Profile summary (real identity, real profile row,
real aggregate stats, real recent activity) and the Stack (the member's real
progression engine: level, XP ring, real achievements, real milestones, real
activity). Every payload is assembled by the real engine in
``apps.profiles.services`` from genuine rows; nothing is fabricated and the
client can never supply level, XP, achievements, milestones or activity.
"""

import hashlib

from django.http import HttpResponse
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.serializers import UserIdentitySerializer
from apps.profiles import services
from apps.profiles.serializers import (
    ProfileReadSerializer,
    ProfilePatchSerializer,
    StackOverviewSerializer,
    StackProgressSerializer,
    StackAchievementsSerializer,
    StackActivitySerializer,
    StackMilestonesSerializer,
)

PALETTE = [
    ("#0e7dd1", "#34d399"),
    ("#7c3aed", "#38bdf8"),
    ("#e11d48", "#fb923c"),
    ("#0d9488", "#a3e635"),
    ("#d97706", "#f43f5e"),
    ("#4338ca", "#22d3ee"),
]


def _avatar_payload(user):
    display = (
        getattr(user, "profile", None)
        and getattr(user.profile, "display_name", "")
        or ""
    )
    display = display.strip() or (user.full_name or "").strip() or user.username or "?"
    words = [w for w in display.replace("-", " ").split() if w][:2]
    initials = "".join(w[0].upper() for w in words) or (display[:2].upper())
    digest = hashlib.sha256(display.encode("utf-8")).hexdigest()
    from1, to1 = PALETTE[int(digest[0], 16) % len(PALETTE)]
    return display, initials, from1, to1


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def avatar_view(request):
    display, glyph, from1, to1 = _avatar_payload(request.user)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" role="img" '
        f'aria-label="{display}">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{from1}"/><stop offset="1" stop-color="{to1}"/>'
        f"</linearGradient></defs>"
        f'<rect width="128" height="128" rx="32" fill="url(#g)"/>'
        f'<circle cx="64" cy="64" r="44" fill="rgba(255,255,255,0.14)"/>'
        f'<text x="64" y="67" text-anchor="middle" dominant-baseline="central" '
        f'font-family="Segoe UI, system-ui, sans-serif" font-size="44" font-weight="700" '
        f'fill="#ffffff">{glyph}</text></svg>'
    )
    response = HttpResponse(svg, content_type="image/svg+xml")
    response["Cache-Control"] = "private, max-age=300"
    return response


def _identity_payload(request):
    """The member's real, server-side identity. Never client-supplied."""
    data = UserIdentitySerializer(request.user).data
    display, _, from1, to1 = _avatar_payload(request.user)
    data["avatar"] = {
        "display": display,
        "from": from1,
        "to": to1,
    }
    return data


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def profile_summary_view(request):
    """Real Profile summary: identity + profile row + real stats + real feed."""
    payload = {
        "identity": _identity_payload(request),
        "stats": services.profile_stats(request.user),
    }
    activity = services.stack_activity(request.user, limit=6, offset=0)
    payload["activity"] = activity["events"]
    serializer = ProfileSummarySerializer(payload)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def stack_overview_view(request):
    payload = {
        "identity": _identity_payload(request),
        "overview": services.stack_overview(request.user),
    }
    return Response(StackOverviewSectionSerializer(payload).data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def stack_progress_view(request):
    return Response(
        StackProgressSectionSerializer(
            {"identity": _identity_payload(request), "progress": services.stack_progress(request.user)}
        ).data
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def stack_achievements_view(request):
    return Response(
        StackAchievementsSectionSerializer(
            {
                "identity": _identity_payload(request),
                "achievements": services.stack_achievements(request.user),
            }
        ).data
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def stack_milestones_view(request):
    return Response(
        StackMilestonesSectionSerializer(
            {
                "identity": _identity_payload(request),
                "milestones": services.stack_milestones(request.user),
            }
        ).data
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def stack_activity_view(request):
    page = max(1, int(request.query_params.get("page", 1) or 1))
    per_page = min(24, max(5, int(request.query_params.get("per_page", 12) or 12)))
    result = services.stack_activity(
        request.user, page=page, per_page=per_page
    )
    return Response(
        StackActivitySectionSerializer(
            {
                "identity": _identity_payload(request),
                "events": result["events"],
                "result": result,
            }
        ).data
    )

def _identity_payload(request):
    """Real server-side identity (authoritative UserIdentitySerializer)."""
    return UserIdentitySerializer(request.user).data


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def profile_view(request):
    """WHO AM I INSIDE VECTOR STRIKE - real identity, real stats, real DP."""
    return Response(
        ProfileReadSerializer(
            {
                "identity": _identity_payload(request),
                "stats": services.profile_stats(request.user),
                "activity": services.stack_activity(request.user, limit=6)["events"],
            }
        ).data
    )


@api_view(["PATCH"])
@permission_classes([permissions.IsAuthenticated])
def profile_patch_view(request):
    """PATCH only backend-supported editable profile fields."""
    ser = ProfilePatchSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    profile = request.user.profile
    for key, value in ser.validated_data.items():
        if hasattr(profile, key):
            setattr(profile, key, value)
    profile.save(update_fields=sorted({*ser.validated_data.keys(), "updated_at"}))
    return Response(
        ProfileReadSerializer(
            {
                "identity": _identity_payload(request),
                "stats": services.profile_stats(request.user),
            }
        ).data
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def stack_view(request):
    """WHAT HAVE I BUILT - real level/XP ring, progress, achievements, activity."""
    return Response(
        StackOverviewSerializer(
            {
                "identity": _identity_payload(request),
                "overview": services.profile_stats(request.user),
                "achievements": services.stack_achievements(request.user),
                "milestones": services.stack_milestones(request.user),
                "activity": services.stack_activity(request.user, limit=10)["events"],
            }
        ).data
    )
