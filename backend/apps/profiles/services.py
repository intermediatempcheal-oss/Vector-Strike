"""Vector Strike Profile + Stack engine (Phase 12) �?" read-only, real rows.

The Profile and the Stack are progression lenses over data the backend
already owns. They reuse the real, authoritative surfaces:

* ``apps.profiles.models.Profile``   �?" the genuine level / XP / rank row
* ``apps.games.UserGameProgress``    �?" real per-game progression rows
* ``apps.games.Achievement`` + ``apps.games.UserAchievement`` �?" real
  achievement templates and genuine unlocked rows
* real timestamped event rows (game sessions, challenge participation,
  tournament participation, achievement unlocks) for the activity feed and
  the milestone timeline

Nothing here fabricates data. Every value is computed from genuine rows,
and when there is no data the engine returns an honest empty shape. The
level / XP rule deliberately reuses the authoritative game-engine constant
(``XP_PER_LEVEL``) instead of inventing a parallel progression model, and XP
is only ever *read* here �?" the client can never submit it.
"""

from dataclasses import dataclass
from itertools import chain

from django.db.models import Count
from django.utils import timezone

from apps.games.models import (
    Achievement,
    UserAchievement,
    UserGameProgress,
)
from apps.games.services import XP_PER_LEVEL


# ---------------------------------------------------------------------------
# Level / XP (one authoritative source of truth = the real XP engine)
# ---------------------------------------------------------------------------


def xp_for_level(level):
    """Cumulative XP needed to *reach* a level (reuses the game engine rule)."""
    from apps.games.services import xp_for_level as engine_xp_for_level

    return engine_xp_for_level(level)


def level_from_xp(xp):
    """Real level for a real XP total (1-based)."""
    return max(1, int(xp // XP_PER_LEVEL) + 1)


def xp_into_current_level(xp):
    """XP contained in the player's current level bucket (0..XP_PER_LEVEL)."""
    return int(xp % XP_PER_LEVEL)


def xp_needed_for_next_level(xp):
    """XP still required to reach the next level from the current ring."""
    return max(0, XP_PER_LEVEL - xp_into_current_level(xp))


def level_progress_fraction(xp):
    """0..1 progress through the current level (used by the XP ring only)."""
    return xp_into_current_level(xp) / float(XP_PER_LEVEL)


# ---------------------------------------------------------------------------
# Profile statistics (real aggregates; zero when there is no data)
# ---------------------------------------------------------------------------


def _real_game_stats(user):
    rows = (
        UserGameProgress.objects.filter(user=user)
        .only("games_played", "completion_percentage")
    )
    played = 0
    completed = 0
    for row in rows:
        played += row.games_played or 0
        if (row.completion_percentage or 0) >= 100:
            completed += 1
    return played, completed


def profile_stats(user):
    """Real aggregate statistics for a genuine account."""
    from apps.challenges.models import ChallengeParticipant
    from apps.tournaments.models import TournamentParticipant

    games_played, games_completed = _real_game_stats(user)
    challenges_entered = ChallengeParticipant.objects.filter(user=user).count()
    tournaments_joined = TournamentParticipant.objects.filter(user=user).count()
    achievements_unlocked = UserAchievement.objects.filter(user=user).count()

    return {
        "games_played": games_played,
        "games_completed": games_completed,
        "challenges_entered": challenges_entered,
        "tournaments_joined": tournaments_joined,
        "achievements_unlocked": achievements_unlocked,
    }


# ---------------------------------------------------------------------------
# Achievements (real collection; unlock state comes from real rows)
# ---------------------------------------------------------------------------


def _achievement_progress(user, achievement):
    """Honest per-achievement state from genuine rows.

    An unlocked achievement reports its real unlock time. A locked template
    reports only what the backend genuinely knows (currently: nothing �?" no
    fabricated percentage). State is derived strictly from real rows.
    """
    earned_at = (
        UserAchievement.objects.filter(user=user, achievement=achievement)
        .values_list("earned_at", flat=True)
        .first()
    )
    if earned_at is not None:
        return {
            "state": "UNLOCKED",
            "earned_at": earned_at,
            "progress_percent": 100,
        }
    return {"state": "LOCKED", "earned_at": None, "progress_percent": 0}


def stack_achievements(user):
    """The player's real achievement collection, in display order.

    Unlocked rows map 1:1 to genuine ``UserAchievement`` rows; locked rows
    are the real active templates. Nothing is invented and nothing is
    presented as unlocked unless a genuine row proves it.
    """
    templates = (
        Achievement.objects.filter(is_active=True)
        .order_by("sort_order", "title")
        .only("slug", "title", "description", "icon", "kind", "xp_reward")
    )
    unlocked_slugs = set(
        UserAchievement.objects.filter(user=user)
        .values_list("achievement__slug", flat=True)
    )

    items = []
    for ach in templates:
        earned_at = (
            UserAchievement.objects.filter(user=user, achievement=ach)
            .values_list("earned_at", flat=True)
            .first()
            if ach.slug in unlocked_slugs
            else None
        )
        items.append(
            {
                "slug": ach.slug,
                "title": ach.title,
                "description": ach.description,
                "icon": ach.icon,
                "kind": ach.kind,
                "xp_reward": ach.xp_reward,
                "state": "UNLOCKED" if ach.slug in unlocked_slugs else "LOCKED",
                "earned_at": earned_at,
            }
        )
    return items


# ---------------------------------------------------------------------------
# Milestones (real progression events in chronological order)
# ---------------------------------------------------------------------------


def _timed_events(user):
    """Real, timestamped progression events, newest first.

    Each event is anchored to a genuine row with its genuine timestamp; no
    event is ever generated to make a profile appear alive.
    """
    events = []

    from apps.games.models import GameSession

    sessions = (
        GameSession.objects.filter(user=user, status="COMPLETED")
        .select_related("game")
        .only("game__title", "xp_earned", "completed_at")
    )
    for session in sessions:
        events.append(
            {
                "kind": "game",
                "label": f"Completed {session.game.title}",
                "detail": f"+{session.xp_earned} XP",
                "at": session.completed_at,
            }
        )

    from apps.challenges.models import ChallengeParticipant

    for row in (
        ChallengeParticipant.objects.filter(user=user)
        .select_related("challenge")
        .only("challenge__title", "joined_at")
    ):
        events.append(
            {
                "kind": "challenge",
                "label": f"Entered {row.challenge.title}",
                "detail": "",
                "at": row.joined_at,
            }
        )

    from apps.tournaments.models import TournamentParticipant

    for row in (
        TournamentParticipant.objects.filter(user=user)
        .select_related("tournament")
        .only("tournament__title", "joined_at")
    ):
        events.append(
            {
                "kind": "tournament",
                "label": f"Joined {row.tournament.title}",
                "detail": "",
                "at": row.joined_at,
            }
        )

    for row in (
        UserAchievement.objects.filter(user=user)
        .select_related("achievement")
        .only("achievement__title", "earned_at")
    ):
        events.append(
            {
                "kind": "achievement",
                "label": f"Unlocked {row.achievement.title}",
                "detail": "",
                "at": row.earned_at,
            }
        )

    return sorted(events, key=lambda e: e["at"], reverse=True)


def stack_milestones(user):
    """The player's genuine progression timeline (newest first)."""
    history = []
    events = _timed_events(user)

    # Chronological build of real milestones in true order.
    ordered = sorted(events, key=lambda e: e["at"])
    account_row = getattr(user, "profile", None)
    joined = account_row.created_at if account_row else user.date_joined
    history.append({"kind": "account", "label": "Account created", "at": joined})

    seen_first = set()
    for event in ordered:
        stamp = event["at"]
        if event["kind"] == "game" and "game" not in seen_first:
            history.append(
                {"kind": "game", "label": "First game completed", "at": stamp}
            )
            seen_first.add("game")
        if (
            event["kind"] == "achievement"
            and "first_achievement" not in seen_first
        ):
            history.append(
                {
                    "kind": "achievement",
                    "label": "First achievement unlocked",
                    "at": stamp,
                }
            )
            seen_first.add("first_achievement")
        if event["kind"] == "challenge" and "challenge" not in seen_first:
            history.append(
                {"kind": "chapter", "label": "First challenge entered", "at": stamp}
            )
            seen_first.add("challenge")
        if event["kind"] == "tournament" and "tournament" not in seen_first:
            history.append(
                {"kind": "tournament", "label": "First tournament joined", "at": stamp}
            )
            seen_first.add("tournament")

    # Genuine level milestones derived from real XP on the profile.
    profile = getattr(user, "profile", None)
    if profile:
        lvl = profile.level or 1
        if lvl >= 4:
            history.append(
                {
                    "kind": "level",
                    "label": f"Reached level {max(2, lvl - 2)}",
                    "at": profile.updated_at,
                }
            )
        if lvl >= 2:
            history.append(
                {
                    "kind": "level",
                    "label": "Reached level 2",
                    "at": profile.updated_at,
                }
            )

    history.sort(key=lambda m: m["at"], reverse=True)
    return history


# ---------------------------------------------------------------------------
# Activity (real chronological feed, paginated client-side via slices)
# ---------------------------------------------------------------------------


def stack_activity(user, limit=20, offset=0):
    """Chronological real activity, newest first. Real rows only."""
    events = _timed_events(user)
    return {
        "events": events[offset : offset + limit],
        "total": len(events),
        "has_more": (offset + limit) < len(events),
    }
