from django.db.models import Q
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.games import serializers as games_serializers
from apps.games.identity import mastery_payload, modes_for
from apps.games.models import Game, GameCategory
from apps.games.services import (
    adaptive_difficulty,
    age_eligible_games,
    complete_session,
    get_recommendation_service,
    hub_context,
    home_context,
    next_games,
)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def home_view(request):
    """Aggregated Game Hub data for the authenticated member.

    The member is always taken from authentication — a frontend-supplied user
    id is never trusted.
    """
    payload = home_context(request.user, request=request)
    return Response(payload)


def _page_params(request):
    try:
        page = max(1, int(request.query_params.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        page_size = max(1, min(48, int(request.query_params.get("page_size", 12))))
    except (TypeError, ValueError):
        page_size = 12
    return page, page_size


def _filtered_games_qs(request, user):
    """Server-side filtering/search/sort for the browsable catalog."""
    qs = age_eligible_games(user.age).select_related("category").prefetch_related(
        "secondary_categories"
    )
    q = (request.query_params.get("q") or "").strip().lower()
    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(tagline__icontains=q)
            | Q(mechanics__icontains=q)
            | Q(category__codename__icontains=q)
        )
    ident = (request.query_params.get("category") or "").strip().lower()
    if ident:
        cats = GameCategory.objects.filter(codename__iexact=ident)
        qs = qs.filter(category__in=cats)
    diff = request.query_params.get("difficulty", "").strip()
    if diff.isdigit():
        qs = qs.filter(difficulty=int(diff))
    gtype = (request.query_params.get("game_type") or "").strip()
    if gtype:
        qs = qs.filter(game_type=gtype)
    mind = request.query_params.get("min_duration", "").strip()
    if mind.isdigit():
        qs = qs.filter(duration_minutes__isnull=False, duration_minutes__gte=int(mind))
    maxd = request.query_params.get("max_duration", "").strip()
    if maxd.isdigit():
        qs = qs.filter(duration_minutes__isnull=False, duration_minutes__lte=int(maxd))
    featured = request.query_params.get("featured", "").strip()
    if featured in {"1", "true", "True"}:
        qs = qs.filter(is_featured=True)
    new_only = request.query_params.get("new", "").strip()
    if new_only in {"1", "true", "True"}:
        qs = qs.filter(is_new=True)
    sort = (request.query_params.get("sort") or "release").strip().lower()
    if sort == "title":
        qs = qs.order_by("title")
    elif sort == "difficulty":
        qs = qs.order_by("difficulty", "title")
    elif sort == "duration":
        qs = qs.order_by("duration_minutes", "title")
    else:
        qs = qs.order_by("-release_date", "-created_at")
    return qs


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def hub_view(request):
    """Game Hub home: continue / recommended / trending / new / quick / deep /
    challenge sections plus the futuristic category carousel."""
    return Response(hub_context(request.user, request=request))


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def hub_categories_view(request):
    return Response(
        {"categories": games_serializers.hub_categories_payload(request.user.age)}
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def hub_category_view(request, ident):
    """A single futuristic identity (e.g. LOGIX) merging its game categories.

    Honest empty states: a category with no age-eligible games reports
    ``games_count = 0`` and the frontend shows the empty state instead of
    fabricating content.
    """
    cats = list(GameCategory.objects.filter(codename__iexact=ident, is_active=True))
    page, page_size = _page_params(request)
    age = request.user.age

    featured = []
    quick = []
    deep = []
    all_games = []
    if cats:
        base = age_eligible_games(age).filter(category__in=cats)
        group = games_serializers.category_identities_payload(cats, request.user)
        body = group[0] if group else {}
        body["slug"] = ident
        body["ident"] = ident
        featured = list(base.filter(is_featured=True).order_by("title")[:6])
        quick = list(base.filter(duration_minutes__lte=6).order_by(
            "duration_minutes", "title"
        )[:6])
        deep = list(
            base.filter(Q(duration_minutes__gte=9) | Q(difficulty__gte=4))
            .order_by("-difficulty", "title")[:6]
        )
        all_games = list(base.order_by("-release_date", "title"))
    else:
        body = {
            "ident": ident,
            "label": ident.upper(),
            "slug": ident,
            "tagline": "",
            "accent": "",
            "icon": "",
            "games_count": 0,
            "categories": [],
        }

    start = (page - 1) * page_size
    paginated = all_games[start : start + page_size]
    return Response(
        {
            "category": body,
            "featured": games_serializers.game_cards_payload(featured, request.user),
            "quick_runs": games_serializers.game_cards_payload(quick, request.user),
            "deep_runs": games_serializers.game_cards_payload(deep, request.user),
            "games": {
                "results": games_serializers.game_cards_payload(paginated, request.user),
                "has_more": len(all_games) > start + len(paginated),
                "total": len(all_games),
                "page": page,
            },
        }
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def hub_games_view(request):
    """Browsable, filterable, paginated game catalog (cuts across categories)."""
    qs = _filtered_games_qs(request, request.user)
    page, page_size = _page_params(request)
    total = qs.count()
    start = (page - 1) * page_size
    results = list(qs[start : start + page_size])
    return Response(
        {
            "results": games_serializers.game_cards_payload(results, request.user),
            "has_more": total > start + len(results),
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def hub_game_view(request, slug):
    """Pre-play detail: real progress, best run, instructions and controls."""
    age = request.user.age
    game = age_eligible_games(age).filter(slug=slug).select_related("category").first()
    if game is None:
        return Response({"detail": "We couldn't load this game."}, status=404)
    return Response(games_serializers.game_detail_payload(game, request.user))


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def hub_session_create_view(request, slug):
    """Open a run. User identity comes from auth, never from the client."""
    age = request.user.age
    game = age_eligible_games(age).filter(slug=slug, status=Game.Status.PUBLISHED).first()
    if game is None:
        return Response({"detail": "We couldn't load this game."}, status=404)
    allowed_modes = modes_for(game)
    mode = str((request.data or {}).get("mode") or allowed_modes[0]).strip().lower()
    if mode not in allowed_modes:
        return Response({"detail": "That mode isn't available for this game."}, status=400)
    difficulty = adaptive_difficulty(request.user, game)
    session = game.sessions.create(user=request.user, game_mode=mode, difficulty=difficulty)
    return Response(
        {
            "session": games_serializers.session_payload(session),
            "game": games_serializers.game_card(game),
        },
        status=201,
    )


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def hub_session_complete_view(request, pk):
    """Authoritative result for a run. Bounds-checked, idempotent, owned."""
    try:
        payload = complete_session(request.user, pk, dict(request.data or {}))
    except ValueError as exc:
        message = str(exc)
        status_code = 404 if message == "session not found" else 400
        return Response({"detail": message}, status=status_code)
    except PermissionError:
        return Response({"detail": "not your session"}, status=403)
    game = Game.objects.select_related("category").get(slug=payload["game_slug"])
    progress = request.user.game_progress.filter(game=game).first()
    payload["mastery"] = mastery_payload(
        game,
        progress.best_accuracy if progress else 0,
        progress.completion_percentage if progress else 0,
        progress.games_played if progress else 0,
    )
    payload["next_difficulty"] = adaptive_difficulty(request.user, game)
    payload["next_games"] = games_serializers.game_cards_payload(
        next_games(request.user, game), request.user
    )
    return Response(payload)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def hub_search_view(request):
    """Real catalog search across games + category identities."""
    q = (request.query_params.get("q") or "").strip()
    games = []
    categories = []
    if len(q) < 2:
        return Response({"query": q, "games": [], "categories": [], "has_more": False})
    games_qs = _filtered_games_qs(request, request.user)[:12]
    games = games_serializers.game_cards_payload(
        list(games_qs), request.user
    )
    categories = [
        c
        for c in games_serializers.hub_categories_payload(request.user.age)
        if q.lower() in c["label"].lower() or q.lower() in (c["tagline"] or "").lower()
    ]
    return Response(
        {
            "query": q,
            "games": games,
            "categories": categories[:6],
            "has_more": False,
        }
    )
