"""Payload builders for the Game Hub and Home API.

These functions deliberately produce plain dicts (no model serialization) so
the aggregation endpoint stays efficient, avoids N+1 queries, and only ever
reflects real database state.
"""

from django.db.models import Count
from django.utils import timezone

from apps.games.models import Game, GameCategory
from apps.games.services import age_eligible_games, xp_for_level

DIFFICULTY_LABELS = {
    Game.Difficulty.RELAXED: "Relaxed",
    Game.Difficulty.EASY: "Easy",
    Game.Difficulty.MODERATE: "Moderate",
    Game.Difficulty.CHALLENGING: "Challenging",
    Game.Difficulty.EXPERT: "Expert",
}


def _stars(difficulty):
    return [i <= difficulty for i in range(1, 6)]


def game_card(game, user=None, progress=None, with_description=False):
    data = {
        "id": game.slug,
        "slug": game.slug,
        "title": game.title,
        "tagline": game.tagline,
        "category": {
            "slug": game.category.slug,
            "label": game.category.label,
            "codename": game.category.codename or game.category.label,
            "accent": game.category.accent or "",
            "icon": game.category.icon or "",
        },
        "categories": [game.category.slug]
        + list(game.secondary_categories.values_list("slug", flat=True)),
        "difficulty": game.difficulty,
        "difficulty_label": DIFFICULTY_LABELS.get(game.difficulty, "Casual"),
        "difficulty_stars": _stars(game.difficulty),
        "game_type": game.game_type,
        "play_kind": game.play_kind or "",
        "mechanics": game.mechanics or "",
        "duration_minutes": game.duration_minutes,
        "content_rating": game.content_rating or "",
        "thumbnail": game.thumbnail or "",
        "banner": game.banner or "",
        "icon": game.icon,
        "minimum_age": game.minimum_age,
        "maximum_age": game.maximum_age,
        "release_date": game.release_date and game.release_date.isoformat() or None,
        "is_new": game.is_new,
        "is_featured": game.is_featured,
        "status": game.status,
    }
    if with_description:
        data["description"] = game.description
    if progress is not None:
        data["progress"] = {
            "current_level": progress.current_level,
            "completion_percentage": progress.completion_percentage,
            "xp": progress.xp,
            "score": progress.score,
            "games_played": progress.games_played,
            "playtime_seconds": progress.playtime_seconds,
            "last_played_at": progress.last_played_at and progress.last_played_at.isoformat() or None,
        }
    return data


def _progress_map(user):
    if user is None:
        return {}
    return {
        row.game_id: row
        for row in user.game_progress.select_related("game__category").filter(
            games_played__gte=1
        )
    }


def game_cards_payload(games, user=None, with_description=False, limit=None):
    games = list(games)
    if limit:
        games = games[:limit]
    progress_by_game = _progress_map(user)
    cards = []
    for game in games:
        try:
            p = progress_by_game.get(game.id)
        except AttributeError:
            p = None
        cards.append(game_card(game, user=user, progress=p, with_description=with_description))
    return cards


def progress_payload(rows):
    """Continue-playing cards from real progress records."""
    out = []
    for row in rows:
        out.append(game_card(row.game, progress=row))
    return out


def start_your_first_payload(user):
    links = list(user.user_interests.select_related("interest").order_by("interest__sort_order"))
    return {
        "interests": [
            {"slug": l.interest.slug, "label": l.interest.label} for l in links
        ]
    }


def profile_progress_payload(profile, request=None):
    if profile is None:
        return None
    xp_now = profile.xp
    next_at = xp_for_level(profile.level + 1)
    pct = min(100, int((xp_now / next_at) * 100)) if next_at else 0
    avatar = (profile.avatar or "").strip()
    if avatar:
        if avatar.startswith(("http://", "https://")):
            avatar_url = avatar
        elif request:
            avatar_url = request.build_absolute_uri(avatar.startswith("/") and avatar or f"/{avatar}")
        else:
            avatar_url = avatar
    else:
        avatar_url = ""
        if request:
            from django.urls import reverse

            avatar_url = request.build_absolute_uri(reverse("profile-avatar"))
    return {
        "display_name": profile.display_name or "",
        "level": profile.level,
        "xp": xp_now,
        "xp_for_next": next_at,
        "xp_progress": pct,
        "rank": profile.rank or "rookie",
        "skill_level": profile.skill_level or "beginner",
        "avatar": avatar,
        "avatar_url": avatar_url,
    }


def discovery_sections_payload(recommended, continue_playing, user):
    """Build 'Because You Like X', 'Try Something New', 'Continue Your Journey'."""
    interest_slugs = set(
        user.user_interests.values_list("interest__slug", flat=True)
    )
    interest_labels = {
        slug: label
        for slug, label in user.user_interests.select_related("interest").values_list(
            "interest__slug", "interest__label"
        )
    }
    played_ids = {cp.game_id for cp in continue_playing}
    recs = [g for g in recommended if g.id not in played_ids]

    like_first = interest_slugs and recs
    sections = []
    if like_first:
        first_slug = next(iter(interest_slugs))
        like_cards = [
            g for g in recs if g.category.slug in interest_slugs
        ]
        if not like_cards:
            like_cards = recs[:4]
        sections.append(
            {
                "key": "because-you-like",
                "title": f"Because You Like {interest_labels.get(first_slug, 'Your Interests')}",
                "games": game_cards_payload(like_cards[:4], user),
            }
        )
    fresh = [g for g in recs if g.category.slug not in interest_slugs]
    if fresh:
        sections.append(
            {
                "key": "try-something-new",
                "title": "Try Something New",
                "games": game_cards_payload(fresh[:4], user),
            }
        )
    journey = sorted(continue_playing, key=lambda r: r.completion_percentage, reverse=True)
    if journey:
        sections.append(
            {
                "key": "continue-journey",
                "title": "Continue Your Journey",
                "games": progress_payload(journey[:4]),
            }
        )
    return sections


def categories_payload(categories, user):
    return [
        {
            "slug": cat.slug,
            "label": cat.label,
            "codename": cat.codename or cat.label,
            "tagline": cat.tagline or "",
            "accent": cat.accent or "",
            "icon": cat.icon or "",
            "games_count": _category_count(cat, user),
        }
        for cat in categories
    ]


def _category_count(cat, user):
    return age_eligible_games(user.age).filter(category_id=cat.id).count()


def category_identities_payload(categories, user, prefix="game-hub"):
    """Unique futuristic category identities for the hub carousel.

    Several internal categories share an identity (e.g. geography + space +
    adventure are all ORBIT); the hub navigates by codename and merges the
    underlying game sets, so members only ever see the codename surface.
    """
    groups = {}
    for cat in categories:
        key = cat.codename or cat.label
        group = groups.setdefault(
            key,
            {
                "ident": key,
                "label": key,
                "slug": key.lower(),
                "tagline": "",
                "accent": "",
                "icon": "",
                "games_count": 0,
                "categories": [],
            },
        )
        group["tagline"] = cat.tagline or group["tagline"]
        group["accent"] = cat.accent or group["accent"]
        group["icon"] = cat.icon or group["icon"]
        group["games_count"] += _category_count(cat, user)
        group["categories"].append(cat.slug)
    groups = sorted(groups.values(), key=lambda g: (g["games_count"] > 0, g["label"]))
    for group in groups:
        group["link"] = f"/{prefix}/{group['slug']}"
    return groups


def trending_payload(games):
    return {
        "available": bool(games),
        "games": [
            {
                **game_card(g),
                "active_members": g.active_members,
                "total_plays": g.total_plays or 0,
                "last_play": g.last_play and g.last_play.isoformat() or None,
            }
            for g in games
        ],
    }


def challenge_payload(challenge):
    if challenge is None:
        return None
    return {
        "active": challenge.active,
        "title": challenge.title,
        "description": challenge.description,
        "goal": challenge.goal,
        "reward_xp": challenge.reward_xp,
        "expires_at": challenge.expires_at and challenge.expires_at.isoformat() or None,
        "game": game_card(challenge.game),
    }


def achievements_payload(earned):
    return [
        {
            "slug": ua.achievement.slug,
            "title": ua.achievement.title,
            "description": ua.achievement.description,
            "icon": ua.achievement.icon,
            "earned_at": ua.earned_at.isoformat(),
        }
        for ua in earned
    ]


def events_payload(request):
    from apps.games.models import Event

    now = timezone.now()
    events = list(
        Event.objects.filter(
            status__in=(Event.Status.LIVE, Event.Status.UPCOMING),
            starts_at__gte=now - timezone.timedelta(days=1),
        )
        .order_by("starts_at")[:3]
    )
    return [
        {
            "slug": e.slug,
            "title": e.title,
            "description": e.description,
            "banner": e.banner or "",
            "status": e.status,
            "starts_at": e.starts_at.isoformat(),
            "ends_at": e.ends_at and e.ends_at.isoformat() or None,
        }
        for e in events
    ]


# ---------------------------------------------------------------------------
# Phase 9 — Game Hub payloads
# ---------------------------------------------------------------------------


def _best_result(user, game):
    """A member's best completed run for a game, if any (real data only)."""
    from apps.games.models import GameSession

    return (
        GameSession.objects.filter(
            user=user, game=game, status=GameSession.Status.COMPLETED
        )
        .order_by("-score", "-accuracy", "-level_reached", "-completed_at")
        .first()
    )


def session_payload(session):
    return {
        "id": str(session.pk),
        "game_slug": session.game.slug,
        "status": session.status,
        "started_at": session.started_at.isoformat(),
        "completed_at": session.completed_at and session.completed_at.isoformat() or None,
        "score": session.score,
        "accuracy": session.accuracy,
        "level_reached": session.level_reached,
        "duration_seconds": session.duration_seconds,
        "xp_earned": session.xp_earned,
    }


def game_detail_payload(game, user):
    """Pre-play detail page: real progress, best run, instructions, controls."""
    progress = user.game_progress.filter(game=game, games_played__gte=1).first()
    best = _best_result(user, game)
    age = user.age
    related = list(
        age_eligible_games(age)
        .filter(category=game.category)
        .exclude(pk=game.pk)
        .select_related("category")[:4]
    )
    if len(related) < 4:
        seen = {g.pk for g in related} | {game.pk}
        extras = list(
            age_eligible_games(age)
            .filter(play_kind=game.play_kind)
            .exclude(pk__in=seen)
            .select_related("category")[: 4 - len(related)]
        )
        related.extend(extras)

    card = game_card(game, user=user, progress=progress)
    card.update(
        {
            "description": game.description,
            "instructions": game.instructions,
            "controls": game.controls,
            "play_count": progress.games_played if progress else 0,
            "best_score": best.score if best else 0,
            "best_accuracy": best.accuracy if best else 0,
            "best_level": best.level_reached if best else 1,
            "best_completed_at": best and best.completed_at and best.completed_at.isoformat() or None,
            "last_result": (
                session_payload(best) if best and best.score > 0 else None
            ),
            "related_games": game_cards_payload(related, user),
        }
    )
    return card


def hub_categories_payload(player_age):
    return category_identities_payload(
        list(GameCategory.objects.filter(is_active=True)),
        type("User", (), {"age": player_age})(),
    )


def hub_game_list_payload(games, user, has_more):
    return {
        "results": game_cards_payload(games, user),
        "has_more": has_more,
    }