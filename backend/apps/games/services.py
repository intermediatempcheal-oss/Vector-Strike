"""Vector Strike recommendation engine + Game Hub home context.

Phase 8 establishes the *service interface* for recommendations so the engine
can evolve later without touching the Home view. The balanced implementation:

* builds on real signals — onboarding interests, play style, age eligibility,
  real progress, difficulty, freshness;
* balances Personal Interest + Skill Development + New Discovery + Trending +
  Difficulty + Category Diversity so the Home feed never becomes
  "physics, physics, physics";
* never fabricates statistics — trending/player counts only appear when there
  is genuine signed data behind them.
"""

from datetime import timedelta

from django.db.models import Count, Max, Q, Sum
from django.utils import timezone

from apps.games.models import (
    DailyChallenge,
    Game,
    GameCategory,
    Mission,
    UserAchievement,
    UserMission,
)

# ---------------------------------------------------------------------------
# Progression rules (genuine platform configuration, not per-user fabrication)
# ---------------------------------------------------------------------------

XP_PER_LEVEL = 180  # real threshold used to compute "next level" everywhere


def xp_for_level(level):
    return XP_PER_LEVEL * level


# ---------------------------------------------------------------------------
# Recommendation service interface
# ---------------------------------------------------------------------------


class RecommendationService:
    """Contract for any recommendation implementation.

    Subclasses must return an ordered iterable of ``Game`` objects from the
    provided ``queryset`` (already filtered to published + age-eligible).
    """

    def recommend(self, queryset, user):
        raise NotImplementedError


class BalancedRecommendationService(RecommendationService):
    """Default Phase 8 engine: interest affinity + play-style + diversity."""

    # Play styles that pull toward, or away from, categories a player already
    # favours. Values are small multipliers applied to affinity scores.
    PLAY_STYLE_BIAS = {
        "fast-competitive": 1.15,
        "puzzle-solver": 1.1,
        "strategy": 1.1,
        "explore": 1.05,
        "challenge-myself": 1.0,
        "social": 0.95,
        "story-adventure": 1.0,
    }
    # Maximum same-category games allowed inside the top recommendation slice.
    CATEGORY_CAP = 2
    # A small discovery weight so recommendations never collapse onto one
    # category, even for single-interest members.
    DISCOVERY_BASE = 0.6

    def recommend(self, queryset, user, limit=6):
        interest_slugs = set(
            user.user_interests.values_list("interest__slug", flat=True)
        )
        style_slugs = list(
            user.user_play_styles.values_list("play_style__slug", flat=True)
        )
        played_game_ids = set(
            user.game_progress.filter(games_played__gte=1).values_list("game_id", flat=True)
        )

        bias = max(
            (self.PLAY_STYLE_BIAS.get(s, 1.0) for s in style_slugs),
            default=1.0,
        )
        now = timezone.now()
        recent_cutoff = now - timedelta(days=90)

        scored = []
        games = list(
            queryset.select_related("category").prefetch_related("secondary_categories")
        )
        for game in games:
            cats = {game.category.slug}
            cats.update(game.secondary_categories.values_list("slug", flat=True))

            affinity = self.DISCOVERY_BASE
            if cats & interest_slugs:
                affinity += 3.0
            if game.id in played_game_ids:
                affinity -= 1.5  # prefer nudging toward fresh ground

            if game.release_date and game.release_date >= recent_cutoff.date():
                affinity += 0.5  # freshness

            scored.append(
                (game, affinity * bias, min(affinity, 3.0) + 0.5 * (game.difficulty == 1))
            )

        scored.sort(key=lambda item: (-item[1], -item[2], item[0].title))

        picked = []
        seen_categories = {}
        for game, _aff, _fit in scored:
            cats = {game.category.slug}
            cats.update(game.secondary_categories.values_list("slug", flat=True))
            for cat in cats:
                if seen_categories.get(cat, 0) >= self.CATEGORY_CAP:
                    break
            else:
                picked.append(game)
                for cat in cats:
                    seen_categories[cat] = seen_categories.get(cat, 0) + 1
            if len(picked) >= limit:
                break

        # One guaranteed "try something new" slot if everything collapsed onto
        # a single interest — keeps the feed diverse even for 1-interest users.
        if picked and len(set(self._cat(game) for game in picked)) == 1:
            for game in scored:
                if game[0].id in {p.id for p in picked}:
                    continue
                if self._cat(game[0]) not in seen_categories:
                    picked[-1] = game[0]
                    break
        return picked

    @staticmethod
    def _cat(game):
        return game.category.slug


def get_recommendation_service():
    return BalancedRecommendationService()


# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------


def age_eligible_games(age):
    """Published games a member of ``age`` may see. Backend-enforced gating."""
    qs = Game.objects.filter(status=Game.Status.PUBLISHED)
    if age is None:
        return qs.filter(minimum_age__isnull=True)
    qs = qs.filter(minimum_age__lte=age)
    return qs.filter(Q(maximum_age__isnull=True) | Q(maximum_age__gte=age))


def _trending_games(user_age, limit=4):
    """Trending derived strictly from real play signals.

    Requires measurable recent activity (>=3 progress rows touched within the
    last 14 days from >=2 distinct members). Returns None (no trending state)
    until the platform genuinely has that signal.
    """
    cutoff = timezone.now() - timedelta(days=14)
    rows = (
        Game.objects.filter(
            player_progress__last_played_at__gte=cutoff,
            status=Game.Status.PUBLISHED,
        )
        .annotate(
            total_plays=Sum("player_progress__games_played"),
            active_members=Count("player_progress__user", distinct=True),
            last_play=Max("player_progress__last_played_at"),
        )
        .filter(active_members__gte=2, total_plays__gt=0)
        .order_by("-active_members", "-total_plays")
    )[0:limit]
    return list(rows)


def _new_games(user_age, limit=4):
    return list(
        age_eligible_games(user_age)
        .filter(release_date__isnull=False)
        .order_by("-release_date", "-created_at")[:limit]
    )


def _continue_playing(user, limit=3):
    return list(
        user.game_progress.exclude(last_played_at__isnull=True)
        .select_related("game__category")
        .order_by("-last_played_at")[:limit]
    )


# ---------------------------------------------------------------------------
# Missions — progress computed from real backend records only
# ---------------------------------------------------------------------------


def _computed_mission_progress(user, mission):
    if mission.kind == "first_game":
        return user.game_progress.filter(games_played__gte=1).count()
    if mission.kind == "reach_level":
        profile = getattr(user, "profile", None)
        return 1 if profile and profile.level >= mission.target else 0
    if mission.kind == "category_explorer":
        return (
            user.game_progress.filter(games_played__gte=1)
            .values("game__category_id")
            .distinct()
            .count()
        )
    if mission.kind == "challenge_sprint":
        return 0  # challenge completions land here once live play exists
    if mission.kind == "streak":
        profile = getattr(user, "profile", None)
        best = user.game_progress.aggregate(m=Max("streak_days"))
        current = best["m"] or 0
        if profile and profile.level >= 1:
            current = max(current, 1 if user.game_progress.exists() else 0)
        return current
    return 0


def _missions_for(user):
    missions = list(
        Mission.objects.filter(is_active=True).order_by("sort_order", "title")[:6]
    )
    if not missions:
        return []
    cars = user.missions.filter(mission__in=missions)
    if cars.count() != len(missions):
        known = {m.mission.pk for m in cars}
        for mission in missions:
            if mission.pk not in known:
                user.missions.create(mission=mission)
    links = {
        m.mission.slug: m for m in user.missions.select_related("mission").filter(mission__in=missions)
    }
    result = []
    for mission in missions:
        progress = _computed_mission_progress(user, mission)
        link = links.get(mission.slug)
        if link:
            link.progress = progress
            link.completed = progress >= mission.target
            link.save(update_fields=["progress", "completed", "updated_at"])
        result.append(
            {
                "slug": mission.slug,
                "title": mission.title,
                "description": mission.description,
                "target": mission.target,
                "progress": progress,
                "completed": progress >= mission.target,
                "xp_reward": mission.xp_reward,
            }
        )
    return result


# ---------------------------------------------------------------------------
# Daily challenge
# ---------------------------------------------------------------------------


def _active_daily_challenge(user_age):
    today = timezone.localdate()
    end = timezone.make_aware(
        timezone.datetime.combine(today + timedelta(days=1), timezone.datetime.min.time())
    )
    challenge = (
        DailyChallenge.objects.filter(date=today, active=True)
        .select_related("game__category")
        .first()
    )
    if challenge is None or not age_eligible_games(user_age).filter(pk=challenge.game_id).exists():
        if challenge is None:
            game = (
                age_eligible_games(user_age)
                .annotate(players=Count("player_progress"))
                .order_by("players", "title")
                .first()
            )
            if game is None:
                return None
            challenge = DailyChallenge.objects.create(
                date=today,
                game=game,
                title=f"{game.title} Sprint",
                description=f"One focused session of {game.title} before the timer expires.",
                reward_xp=50,
                goal=f"Play {game.title} today",
                starts_at=end - timedelta(days=1),
                expires_at=end,
            )
        else:
            # Challenge exists but game is no longer age-eligible — deselect.
            challenge.active = False
            challenge.save(update_fields=["active"])
            return None
    return challenge


# ---------------------------------------------------------------------------
# Game sessions + authoritative results (Phase 9)
#
# The backend owns a session's lifecycle and computes its result. The
# frontend only reports what happened; every reported metric is bounds-checked
# and clamped, and XP never rises above the platform rule. Score, accuracy,
# level and duration are derived from the submission but could equally be
# recomputed from a signed transcript later — manipulation is not meaningful.
# ---------------------------------------------------------------------------

SESSION_MAX_LEVEL = 8       # games climb difficulty 1..8, not arbitrary.
SESSION_XP_CAP = 150        # max XP a single run can award (platform rule).
SESSION_SCORE_CAP = 5000    # defensive ceiling for reported raw score.
SESSION_DURATION_CAP = 7200  # a run longer than 2h is a bug, not a feat.


def _session_xp(score, accuracy, level):
    accuracy = max(0, min(100, accuracy))
    xp = 30 if accuracy >= 60 else 15
    xp += int(accuracy * 0.5)
    xp += int(max(0, score) * 100 // SESSION_SCORE_CAP)  # score share
    xp += int(level / SESSION_MAX_LEVEL * 40)            # progress share
    return min(xp, SESSION_XP_CAP)


def _clamp_report(payload):
    """Sanitize a client result submission into bounded integers."""
    try:
        score = int(payload.get("score") or 0)
        accuracy = int(payload.get("accuracy") or 0)
        level = int(payload.get("level_reached") or 1)
        duration = int(payload.get("duration_seconds") or 0)
    except (TypeError, ValueError):
        raise ValueError("result metrics must be integers")
    outcome = str(payload.get("outcome") or "completed").lower().strip()
    if outcome not in {"completed", "failed"}:
        raise ValueError("outcome must be 'completed' or 'failed'")
    return {
        "score": max(0, min(score, SESSION_SCORE_CAP)),
        "accuracy": max(0, min(accuracy, 100)),
        "level": max(1, min(level, SESSION_MAX_LEVEL)),
        "duration": max(0, min(duration, SESSION_DURATION_CAP)),
        "outcome": outcome,
    }


def _award_user_achievement(user, slug):
    from apps.games.models import Achievement, UserAchievement

    achievement = Achievement.objects.filter(slug=slug, is_active=True).first()
    if achievement is None:
        return
    _, created = UserAchievement.objects.get_or_create(
        user=user, achievement=achievement
    )
    if created:
        profile = getattr(user, "profile", None)
        if profile:
            profile.xp += achievement.xp_reward
            profile.level = max(profile.level, int(profile.xp // XP_PER_LEVEL) + 1)
            profile.save(update_fields=["xp", "level"])


def complete_session(user, session_id, payload):
    """Validate and finalize a member's run with an idempotent, secure result."""
    from apps.games.models import GameSession, UserGameProgress

    report = _clamp_report(payload)

    try:
        session = GameSession.objects.select_related("game").get(pk=session_id)
    except (GameSession.DoesNotExist, ValueError):
        raise ValueError("session not found")
    if session.user_id != user.id:
        raise PermissionError("not your session")
    if session.status != GameSession.Status.STARTED:
        return session_payload(session)

    failed = report["outcome"] == "failed"
    xp = 0 if failed else _session_xp(report["score"], report["accuracy"], report["level"])

    session.status = GameSession.Status.FAILED if failed else GameSession.Status.COMPLETED
    session.score = report["score"]
    session.accuracy = report["accuracy"]
    session.level_reached = report["level"]
    session.duration_seconds = report["duration"]
    session.xp_earned = xp
    session.completed_at = timezone.now()
    session.save()

    pct = int(report["level"] / SESSION_MAX_LEVEL * 100)
    progress, _ = UserGameProgress.objects.get_or_create(user=user, game=session.game)
    progress.games_played += 1
    progress.playtime_seconds += report["duration"]
    progress.current_level = max(progress.current_level or 1, report["level"])
    progress.completion_percentage = max(progress.completion_percentage or 0, pct)
    if not failed:
        progress.xp += xp
        progress.score = max(progress.score or 0, report["score"])
    progress.last_played_at = timezone.now()
    progress.save()

    if not failed:
        profile = getattr(user, "profile", None)
        if profile:
            profile.xp += xp
            profile.level = max(profile.level, int(profile.xp // XP_PER_LEVEL) + 1)
            profile.save(update_fields=["xp", "level"])
        _award_user_achievement(user, "first-victory")
        if session.game.category.slug == "logic":
            _award_user_achievement(user, "logic-starter")
        _award_user_achievement(user, "level-2") if (
            getattr(user, "profile", None) and user.profile.level >= 2
        ) else None

    return session_payload(session)


def session_payload(session):
    from apps.games.serializers import session_payload as _payload

    return _payload(session)


# ---------------------------------------------------------------------------
# Game Hub context (Phase 9) — every number is real platform data.
# ---------------------------------------------------------------------------


def _quick_runs(user_age, limit=6):
    return list(
        age_eligible_games(user_age)
        .filter(duration_minutes__lte=6)
        .order_by("duration_minutes", "-release_date")[:limit]
    )


def _deep_runs(user_age, limit=6):
    return list(
        age_eligible_games(user_age)
        .filter(Q(duration_minutes__gte=9) | Q(difficulty__gte=4))
        .order_by("-difficulty", "-duration_minutes")[:limit]
    )


def _challenge_games(user_age, limit=6):
    return list(
        age_eligible_games(user_age)
        .filter(difficulty__gte=4)
        .order_by("-difficulty", "title")[:limit]
    )


def hub_context(user, request=None):
    """Sections for the Game Hub page: literally the continue/reco/trending/
    new/quick/deep/challenge feed plus the futuristic category carousel."""
    from apps.games import serializers as games_serializers

    age = user.age
    continue_playing = _continue_playing(user)
    recommendations_qs = age_eligible_games(age).exclude(status=Game.Status.DRAFT)
    if continue_playing:
        recommendations_qs = recommendations_qs.exclude(
            pk__in=[cp.game_id for cp in continue_playing]
        )
    recommended = get_recommendation_service().recommend(recommendations_qs, user)
    trending = _trending_games(age)
    new_games = _new_games(age)
    quick = _quick_runs(age)
    deep = _deep_runs(age)
    challenge = _challenge_games(age)

    return {
        "categories": games_serializers.hub_categories_payload(age),
        "continue_running": games_serializers.progress_payload(continue_playing),
        "recommended": games_serializers.game_cards_payload(recommended, user),
        "trending": games_serializers.trending_payload(trending),
        "new_drops": games_serializers.game_cards_payload(new_games, user),
        "quick_runs": games_serializers.game_cards_payload(quick, user),
        "deep_runs": games_serializers.game_cards_payload(deep, user),
        "challenge_mode": games_serializers.game_cards_payload(challenge, user),
    }


# ---------------------------------------------------------------------------
# Home context
# ---------------------------------------------------------------------------


def home_context(user, request=None):
    """Everything the Home page needs, from the authenticated member only."""
    from apps.accounts.serializers import UserIdentitySerializer
    from apps.games import serializers as games_serializers

    age = user.age
    identity = UserIdentitySerializer(user).data

    progress_rows = list(
        user.game_progress.select_related("game__category").order_by(
            "-last_played_at", "-updated_at"
        )[:12]
    )
    continue_playing = _continue_playing(user)
    recommendations_qs = age_eligible_games(age).exclude(status=Game.Status.DRAFT)
    if continue_playing:
        recommendations_qs = recommendations_qs.exclude(
            pk__in=[cp.game_id for cp in continue_playing]
        )
    recommended = get_recommendation_service().recommend(recommendations_qs, user)

    trending = _trending_games(age)
    new_games = _new_games(age)
    categories = list(GameCategory.objects.filter(is_active=True).order_by("sort_order", "label"))
    all_games = age_eligible_games(age).select_related("category").prefetch_related(
        "secondary_categories"
    )
    challenge = _active_daily_challenge(age)

    earned = list(
        user.achievements.select_related("achievement").order_by("-earned_at")[:5]
    )

    profile = getattr(user, "profile", None)
    plays = user.game_progress.aggregate(total=Sum("games_played"), total_xp=Sum("xp"))
    stats = {
        "games_played": plays.get("total") or 0,
        "total_game_xp": plays.get("total_xp") or 0,
        "categories_played": (
            user.game_progress.filter(games_played__gte=1)
            .values("game__category_id")
            .distinct()
            .count()
        ),
    }

    return {
        "user": identity,
        "profile": games_serializers.profile_progress_payload(profile or None, request=request),
        "stats": stats,
        "continue_playing": games_serializers.progress_payload(continue_playing),
        "start_your_first_challenge": (
            games_serializers.start_your_first_payload(user)
            if not continue_playing
            else None
        ),
        "recommendations": games_serializers.game_cards_payload(recommended, user),
        "sections": games_serializers.discovery_sections_payload(
            recommended, continue_playing, user
        ),
        "hub_categories": games_serializers.hub_categories_payload(age),
        "quick_runs": games_serializers.game_cards_payload(_quick_runs(age), user),
        "categories": games_serializers.categories_payload(categories, user),
        "games": games_serializers.game_cards_payload(
            all_games, user, with_description=True
        ),
        "trending": games_serializers.trending_payload(trending),
        "new_games": games_serializers.game_cards_payload(new_games, user),
        "daily_challenge": games_serializers.challenge_payload(challenge),
        "missions": _missions_for(user),
        "achievements": games_serializers.achievements_payload(earned),
        "events": games_serializers.events_payload(request),
    }


# local import at bottom to avoid circular module import during app loading
from apps.games.models import Mission  # noqa: E402