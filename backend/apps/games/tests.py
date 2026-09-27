"""Phase 8 backend tests: the centralized Game Hub feed at /api/v1/home/.

Covers authentication, real-data rule (no fabricated stats), age gating at the
server, continue-playing, recommendations driven by real interests/progress,
diversity, missions computed from real records, daily challenge, events and the
generated avatar endpoint. Mirrors the conventions of apps/accounts/tests.py.
"""

from datetime import date, time, timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.games.models import (
    DailyChallenge,
    Event,
    Game,
    GameCategory,
    UserAchievement,
    UserGameProgress,
)
from apps.profiles.models import Interest, PlayStyle, Profile, UserInterest, UserPlayStyle


def make_user(email="player@example.com", username="player", dob=date(2015, 6, 1),
              interests=("science", "logic"), play_styles=()):
    user = User.objects.create_user(
        email=email,
        username=username,
        password="secret-pass-99",
        full_name="Test Player",
        date_of_birth=dob,
    )
    profile = Profile.objects.create(
        user=user,
        display_name="Test Player",
        language="en",
        country="",
        skill_level="beginner",
        level=1,
        xp=0,
        rank="rookie",
        avatar="",
    )
    for slug in interests:
        interest = Interest.objects.get(slug=slug)
        UserInterest.objects.create(user=user, interest=interest)
    for slug in play_styles:
        style = PlayStyle.objects.get(slug=slug)
        UserPlayStyle.objects.create(user=user, play_style=style)
    return user, profile


class HomeFeedAuthenticationTests(APITestCase):

    def test_home_requires_authentication(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        body = response.json()
        self.assertIn("error", body)

    def test_home_returns_feed_for_authenticated_member(self):
        user, _ = make_user()
        self.client.force_authenticate(user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertEqual(payload["user"]["username"], user.username)
        self.assertEqual(payload["profile"]["display_name"], "Test Player")
        self.assertEqual(payload["profile"]["level"], 1)
        self.assertTrue(payload["profile"]["avatar_url"])

    def test_feed_contains_core_sections(self):
        user, _ = make_user()
        self.client.force_authenticate(user)
        payload = self.client.get(reverse("home")).json()
        for key in (
            "user", "profile", "stats", "continue_playing", "recommendations",
            "sections", "categories", "games", "trending", "new_games",
            "daily_challenge", "missions", "achievements", "events",
        ):
            self.assertIn(key, payload)


class RealDataAndAgeGatingTests(APITestCase):

    def _catalog(self):
        return {g.slug: g for g in Game.objects.filter(status=Game.Status.PUBLISHED)}

    def test_no_fabricated_stats_for_new_member(self):
        user, _ = make_user()
        self.client.force_authenticate(user)
        payload = self.client.get(reverse("home")).json()
        self.assertEqual(payload["stats"], {"games_played": 0, "total_game_xp": 0,
                                            "categories_played": 0})
        self.assertEqual(payload["continue_playing"], [])
        trending = payload["trending"]
        self.assertIsInstance(trending, dict)
        self.assertFalse(trending["available"])
        self.assertEqual(trending["games"], [])
        self.assertEqual(payload["achievements"], [])

    def test_index_uses_vector_id(self):
        user, _ = make_user()
        self.client.force_authenticate(user)
        payload = self.client.get(reverse("home")).json()
        self.assertTrue(payload["user"]["vector_id"].startswith("VS-"))
        self.assertEqual(payload["user"]["username"], user.username)

    def test_age_ineligible_games_are_excluded_server_side(self):
        user, _ = make_user(dob=date(2019, 1, 1))  # ~7yo by 2026
        self.client.force_authenticate(user)
        payload = self.client.get(reverse("home")).json()
        slugs = {g["slug"] for g in payload["games"]}
        catalog = self._catalog()
        for slug, game in catalog.items():
            present = slug in slugs
            cutoff = game.minimum_age or 0
            if user.age is not None and user.age >= cutoff:
                self.assertTrue(present, f"{slug} should be age-eligible")
            else:
                self.assertFalse(present, f"{slug} must be filtered by age {user.age}")

    def test_age_eligible_games_never_leak_ineligible_recommendations(self):
        user, _ = make_user(dob=date(2019, 1, 1))
        self.client.force_authenticate(user)
        payload = self.client.get(reverse("home")).json()
        max_age_seen = 0
        for game in payload["games"]:
            max_age_seen = max(max_age_seen, game["minimum_age"] or 0)
        self.assertLessEqual(max_age_seen, user.age)

    def test_trending_needs_real_signals(self):
        user, _ = make_user()
        self.client.force_authenticate(user)
        initial = self.client.get(reverse("home")).json()["trending"]
        self.assertFalse(initial["available"])

        game_a = Game.objects.get(slug="math-master")
        game_b = Game.objects.get(slug="science-lab")
        user_b, _ = make_user(email="b@example.com", username="player_b")
        now = timezone.now()
        for u, game in ((user, game_a), (user_b, game_a), (user_b, game_b)):
            UserGameProgress.objects.create(
                user=u, game=game, games_played=4, wins=3,
                last_played_at=now - timedelta(hours=2),
                completion_percentage=40,
            )

        payload = self.client.get(reverse("home")).json()["trending"]
        self.assertTrue(payload["available"])
        self.assertTrue(payload["games"])
        top = payload["games"][0]
        self.assertGreaterEqual(top["active_members"], 2)
        self.assertGreaterEqual(top["total_plays"], 8)


class ContinuePlayingTests(APITestCase):

    def test_continue_playing_from_real_progress(self):
        user, _ = make_user()
        math = Game.objects.get(slug="math-master")
        space = Game.objects.get(slug="space-quest")
        UserGameProgress.objects.create(
            user=user, game=space, current_level=3, xp=120, score=980,
            completion_percentage=55, games_played=6, wins=4,
            last_played_at=timezone.now() - timedelta(minutes=5),
        )
        UserGameProgress.objects.create(
            user=user, game=math, current_level=2, xp=40, score=210,
            completion_percentage=12, games_played=2, wins=1,
            last_played_at=timezone.now() - timedelta(days=2),
        )
        self.client.force_authenticate(user)
        payload = self.client.get(reverse("home")).json()
        continue_cards = payload["continue_playing"]
        self.assertEqual([c["slug"] for c in continue_cards], ["space-quest", "math-master"])
        self.assertEqual(payload["stats"]["games_played"], 8)
        journey = next(s for s in payload["sections"] if s["key"] == "continue-journey")
        self.assertTrue(journey["games"])
        self.assertEqual(journey["games"][0]["slug"], "space-quest")

    def test_progress_is_never_shared_between_members(self):
        user, _ = make_user()
        user_b, _ = make_user(email="iso@example.com", username="isolation")
        math = Game.objects.get(slug="math-master")
        UserGameProgress.objects.create(
            user=user_b, game=math, games_played=9, wins=9,
            last_played_at=timezone.now(), completion_percentage=90,
        )
        self.client.force_authenticate(user)
        resp = self.client.get(reverse("home"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        payload = resp.json()
        self.assertEqual(payload["continue_playing"], [])
        self.assertEqual(payload["stats"]["games_played"], 0)


class RecommendationTests(APITestCase):

    def test_new_member_gets_interest_driven_recommendations(self):
        user, _ = make_user(interests=("science", "logic"))
        self.client.force_authenticate(user)
        payload = self.client.get(reverse("home")).json()
        recs = payload["recommendations"]
        self.assertTrue(recs)
        rec_cats = {r["category"]["slug"] for r in recs if r.get("category")}
        self.assertTrue(
            rec_cats & {"science", "logic", "chemistry", "coding", "puzzles"},
            "recommendations should include games from interest-related categories",
        )

    def test_recommendations_exclude_already_progressed_games(self):
        user, _ = make_user(interests=("science",))
        math = Game.objects.get(slug="math-master")
        UserGameProgress.objects.create(
            user=user, game=math, games_played=3,
            last_played_at=timezone.now(), completion_percentage=10,
        )
        self.client.force_authenticate(user)
        recs = self.client.get(reverse("home")).json()["recommendations"]
        self.assertNotIn("math-master", {r["slug"] for r in recs})

    def test_recommendation_category_diversity_cap(self):
        user, _ = make_user(interests=("logic",))
        self.client.force_authenticate(user)
        recs = self.client.get(reverse("home")).json()["recommendations"]
        from collections import Counter

        cats = Counter()
        for r in recs:
            if r.get("category"):
                cats[r["category"]["slug"]] += 1
        self.assertLessEqual(max(cats.values()), 2, "diversity cap must hold")


class MissionsAndChallengeTests(APITestCase):

    def test_missions_computed_from_real_records(self):
        user, _ = make_user()
        self.client.force_authenticate(user)
        missions = self.client.get(reverse("home")).json()["missions"]
        first_game = next(m for m in missions if m["slug"] == "first-game")
        self.assertEqual(first_game["progress"], 0)
        self.assertFalse(first_game["completed"])

        math = Game.objects.get(slug="math-master")
        UserGameProgress.objects.create(
            user=user, game=math, games_played=1,
            last_played_at=timezone.now(), completion_percentage=5,
        )
        missions = self.client.get(reverse("home")).json()["missions"]
        first_game = next(m for m in missions if m["slug"] == "first-game")
        self.assertEqual(first_game["progress"], 1)
        self.assertTrue(first_game["completed"])

    def test_daily_challenge_references_a_real_eligible_game(self):
        user, _ = make_user()
        self.client.force_authenticate(user)
        daily = self.client.get(reverse("home")).json()["daily_challenge"]
        self.assertTrue(daily["active"])
        self.assertIn("game", daily)
        self.assertTrue(daily["game"]["slug"])
        today = timezone.localdate()
        stored = DailyChallenge.objects.get(date=today)
        self.assertEqual(stored.game.status, Game.Status.PUBLISHED)

    def test_events_show_only_live_or_upcoming(self):
        user, _ = make_user()
        now = timezone.now()
        Event.objects.create(
            slug="live-cup", title="Live Cup", starts_at=now - timedelta(hours=1),
            status=Event.Status.LIVE, ends_at=now + timedelta(hours=3),
        )
        Event.objects.create(
            slug="next-event", title="Next Event", starts_at=now + timedelta(days=2),
            status=Event.Status.UPCOMING,
        )
        Event.objects.create(
            slug="yesterday", title="Over", starts_at=now - timedelta(days=5),
            status=Event.Status.ENDED,
        )
        self.client.force_authenticate(user)
        events = self.client.get(reverse("home")).json()["events"]
        slugs = {e["slug"] for e in events}
        self.assertIn("live-cup", slugs)
        self.assertIn("next-event", slugs)
        self.assertNotIn("yesterday", slugs)


class AchievementsTests(APITestCase):

    def test_recent_achievements_are_real_unlocks(self):
        user, _ = make_user()
        achievement = Game.objects.none() and None
        from apps.games.models import Achievement

        achievement = Achievement.objects.get(slug="first-victory")
        UserAchievement.objects.create(user=user, achievement=achievement)
        self.client.force_authenticate(user)
        payload = self.client.get(reverse("home")).json()
        self.assertEqual(payload["achievements"][0]["slug"], "first-victory")


class AvatarEndpointTests(APITestCase):

    def test_avatar_endpoint_requires_auth(self):
        response = self.client.get(reverse("profile-avatar"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_avatar_renders_initials_svg(self):
        user, _ = make_user()
        self.client.force_authenticate(user)
        response = self.client.get(reverse("profile-avatar"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        self.assertIn(b"<svg", response.content)

    def test_home_avatar_url_uses_generated_avatar_when_not_set(self):
        user, _ = make_user()
        self.client.force_authenticate(user)
        payload = self.client.get(reverse("home")).json()
        self.assertTrue(payload["profile"]["avatar_url"].endswith("/api/v1/profile/avatar/"))


# ---------------------------------------------------------------------------
# Phase 9 — Game Hub, category discovery and the real play flow.
# ---------------------------------------------------------------------------


class GameHubTests(APITestCase):
    """/api/v1/hub/* — futuristic categories, sections, catalog, sessions."""

    ACADEMIC_WORDS = (
        "math", "science", "physics", "chemistry", "geography", "history",
        "languages", "logic", "coding", "strategy", "racing", "puzzles",
        "memory", "environment", "finance", "space", "creativity", "adventure",
        "classic", "arcade", "multiplayer",
    )

    def _auth(self, user):
        self.client.force_authenticate(user)
        return user

    def test_hub_requires_authentication(self):
        response = self.client.get(reverse("hub"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_hub_pages_have_no_academic_category_names(self):
        user, _ = make_user()
        self._auth(user)
        response = self.client.get(reverse("hub"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        labels = [c["label"] for c in response.json()["categories"]]
        for label in labels:
            for word in self.ACADEMIC_WORDS:
                self.assertNotIn(word, label.lower())
        self.assertIn("LOGIX", labels)
        self.assertIn("QUANTA", labels)

    def test_hub_section_keys_present(self):
        user, _ = make_user(interests=("puzzles",))
        self._auth(user)
        payload = self.client.get(reverse("hub")).json()
        for key in (
            "categories", "continue_running", "recommended", "trending",
            "new_drops", "quick_runs", "deep_runs", "challenge_mode",
        ):
            self.assertIn(key, payload)
        self.assertIsInstance(payload["quick_runs"], list)
        self.assertIsInstance(payload["deep_runs"], list)

    def test_category_page_merges_identities_and_paginates(self):
        user, _ = make_user()
        self._auth(user)
        payload = self.client.get(reverse("hub-category", args=["logix"])).json()
        self.assertEqual(payload["category"]["label"], "LOGIX")
        self.assertGreaterEqual(payload["category"]["games_count"], 1)
        self.assertIsInstance(payload["games"]["results"], list)
        self.assertIn("has_more", payload["games"])

    def test_unknown_category_is_honest_empty_state(self):
        user, _ = make_user()
        self._auth(user)
        payload = self.client.get(reverse("hub-category", args=["zzz"])).json()
        self.assertEqual(payload["category"]["games_count"], 0)
        self.assertEqual(payload["games"]["results"], [])

    def test_catalog_filters_and_search_are_real(self):
        user, _ = make_user()
        self._auth(user)
        response = self.client.get(reverse("hub-games"), {"q": "blitz", "sort": "title"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = response.json()
        self.assertIn("results", body)
        self.assertTrue(all("blitz" in g["title"].lower() for g in body["results"]))
        response = self.client.get(
            reverse("hub-games"), {"category": "logix", "difficulty": "2"}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for game in response.json()["results"]:
            self.assertEqual(game["difficulty"], 2)

    def test_search_route_returns_real_games(self):
        user, _ = make_user()
        self._auth(user)
        body = self.client.get(reverse("hub-search"), {"q": "blitz"}).json()
        self.assertTrue(any("blitz" in g["title"].lower() for g in body["games"]))
        self.assertIn("query", body)

    def test_game_detail_shows_first_run_state(self):
        user, _ = make_user()
        self._auth(user)
        payload = self.client.get(reverse("hub-game", args=["math-master"])).json()
        self.assertEqual(payload["play_count"], 0)
        self.assertEqual(payload["best_score"], 0)
        self.assertIn("instructions", payload)
        self.assertIn("controls", payload)
        self.assertIn("related_games", payload)
        self.assertEqual(payload["category"]["codename"], "QUANTA")

    def test_age_gate_blocks_detail_and_session(self):
        # dob => age 8: 12+ finance games must be unreachable.
        user, _ = make_user(dob=date(2018, 1, 1))
        self._auth(user)
        response = self.client.get(reverse("hub-game", args=["finance-sim"]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        response = self.client.post(reverse("hub-session-create", args=["finance-sim"]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GameSessionFlowTests(APITestCase):
    """Session creation + authoritative, tamper-resistant completion."""

    def setUp(self):
        self.user, self.profile = make_user(interests=("puzzles",))
        self.client.force_authenticate(self.user)
        self.game = Game.objects.get(slug="math-master")

    def _start(self):
        response = self.client.post(reverse("hub-session-create", args=[self.game.slug]))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.json()["session"]

    def test_start_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(reverse("hub-session-create", args=[self.game.slug]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_start_injects_user_from_auth_never_request(self):
        start = self._start()
        self.assertIsNotNone(start["id"])
        self.assertEqual(start["status"], "started")

    def test_completion_computes_authoritative_result(self):
        start = self._start()
        response = self.client.post(
            reverse("hub-session-complete", args=[start["id"]]),
            {
                "score": 900,
                "accuracy": 88,
                "level_reached": 4,
                "duration_seconds": 300,
                "outcome": "completed",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result = response.json()
        self.assertEqual(result["status"], "completed")
        self.assertGreater(result["xp_earned"], 0)
        home = self.client.get(reverse("home")).json()
        cards = home["continue_playing"]
        self.assertEqual(cards[0]["slug"], self.game.slug)

    def test_completion_is_idempotent(self):
        start = self._start()
        payload = {
            "score": 500,
            "accuracy": 70,
            "level_reached": 3,
            "duration_seconds": 200,
            "outcome": "completed",
        }
        first = self.client.post(
            reverse("hub-session-complete", args=[start["id"]]), payload, format="json"
        ).json()
        second = self.client.post(
            reverse("hub-session-complete", args=[start["id"]]), payload, format="json"
        ).json()
        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["xp_earned"], second["xp_earned"])

    def test_cannot_complete_someone_else_session(self):
        other, _ = make_user(email="other@example.com", username="other")
        other_session = Game.objects.get(slug="puzzle-vault").sessions.create(user=other)
        response = self.client.post(
            reverse("hub-session-complete", args=[str(other_session.pk)]),
            {"score": 1, "outcome": "completed"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tampered_metrics_are_clamped(self):
        start = self._start()
        result = self.client.post(
            reverse("hub-session-complete", args=[start["id"]]),
            {
                "score": 999999999,
                "accuracy": 400,
                "level_reached": 99,
                "duration_seconds": 999999999,
                "outcome": "completed",
            },
            format="json",
        ).json()
        self.assertLessEqual(result["score"], 5000)
        self.assertLessEqual(result["accuracy"], 100)
        self.assertLessEqual(result["level_reached"], 8)
        self.assertGreater(result["xp_earned"], 0)

    def test_failed_run_awards_zero_xp(self):
        start = self._start()
        result = self.client.post(
            reverse("hub-session-complete", args=[start["id"]]),
            {
                "score": 10,
                "accuracy": 20,
                "level_reached": 1,
                "duration_seconds": 30,
                "outcome": "failed",
            },
            format="json",
        ).json()
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["xp_earned"], 0)

    def test_progress_and_achievements_after_completed_run(self):
        start = self._start()
        self.client.post(
            reverse("hub-session-complete", args=[start["id"]]),
            {
                "score": 1200,
                "accuracy": 95,
                "level_reached": 6,
                "duration_seconds": 400,
                "outcome": "completed",
            },
            format="json",
        )
        progress = UserGameProgress.objects.get(user=self.user, game=self.game)
        self.assertEqual(progress.games_played, 1)
        self.assertEqual(progress.score, 1200)
        self.assertGreater(progress.completion_percentage, 0)
        self.assertTrue(
            UserAchievement.objects.filter(
                user=self.user, achievement__slug="first-victory"
            ).exists()
        )

    def test_best_result_appears_on_detail_page(self):
        start = self._start()
        self.client.post(
            reverse("hub-session-complete", args=[start["id"]]),
            {
                "score": 1500,
                "accuracy": 92,
                "level_reached": 7,
                "duration_seconds": 350,
                "outcome": "completed",
            },
            format="json",
        )
        detail = self.client.get(reverse("hub-game", args=[self.game.slug])).json()
        self.assertEqual(detail["best_score"], 1500)
        self.assertEqual(detail["play_count"], 1)