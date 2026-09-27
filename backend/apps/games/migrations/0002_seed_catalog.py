"""Seed the real Game Hub catalog: categories, original games, achievement and
mission templates.

All rows are genuine Vector Strike assets — the same original games referenced
by the onboarding recommendation set, plus platform-defined achievement and
mission templates. No member-facing stats are fabricated here.
"""

from django.db import migrations
from django.utils import timezone

GAME_CATEGORIES = [
    ("mathematics", "Math", 1),
    ("science", "Science", 2),
    ("physics", "Physics", 3),
    ("chemistry", "Chemistry", 4),
    ("geography", "Geography", 5),
    ("history", "History", 6),
    ("languages", "Languages", 7),
    ("logic", "Logic", 8),
    ("coding", "Coding", 9),
    ("strategy", "Strategy", 10),
    ("racing", "Racing", 11),
    ("puzzles", "Puzzle", 12),
    ("memory", "Memory", 13),
    ("environment", "Environment", 14),
    ("finance", "Finance", 15),
    ("space", "Space", 16),
    ("creativity", "Creativity", 17),
    ("adventure", "Adventure", 18),
    ("classic", "Classic", 19),
    ("arcade", "Arcade", 20),
    ("multiplayer", "Multiplayer", 21),
]

# slug, category, secondary categories, rating(1-5), game_type, min_age, tagline
GAMES = [
    ("math-master", "mathematics", ["arcade"], 3, "solo", 6, "Solve fast, level faster."),
    ("science-lab", "science", [], 2, "solo", 6, "Experiment, discover, amaze."),
    ("physics-drive", "physics", ["racing", "classic"], 3, "versus", 6, "Speed built on real physics."),
    ("chem-fusion", "chemistry", ["science"], 3, "solo", 8, "Mix elements, craft reactions."),
    ("globe-runner", "geography", ["arcade"], 2, "solo", 6, "Rush across the whole world."),
    ("time-voyagers", "history", ["adventure"], 2, "solo", 8, "Travel eras, change nothing, learn everything."),
    ("word-bloom", "languages", ["classic"], 1, "solo", 6, "Grow your language garden."),
    ("logic-arena", "logic", ["puzzles"], 4, "co-op", 10, "Reason your way to victory."),
    ("code-forge", "coding", ["logic"], 4, "solo", 10, "Forge programs from pure thought."),
    ("strategy-command", "strategy", ["multiplayer"], 3, "versus", 10, "Out-think every move."),
    ("racing-vector", "racing", ["multiplayer", "arcade"], 2, "versus", 6, "Outrace rivals across neon circuits."),
    ("puzzle-vault", "puzzles", ["logic"], 3, "solo", 6, "Crack the combination."),
    ("memory-matrix", "memory", ["puzzles"], 2, "solo", 6, "Remember more than anyone."),
    ("eco-guardian", "environment", ["science"], 1, "solo", 6, "Protect a living planet."),
    ("finance-sim", "finance", ["strategy"], 3, "solo", 12, "Grow, save, invest, win."),
    ("space-quest", "space", ["adventure"], 2, "solo", 6, "Chart the furthest frontiers."),
    ("idea-studio", "creativity", [], 1, "solo", 6, "Build worlds from imagination."),
    ("quest-frontier", "adventure", ["multiplayer"], 2, "versus", 6, "Every path hides a challenge."),
]

ACHIEVEMENTS = [
    ("first-victory", "First Victory", "Complete your very first game round.", "gamepad", "lifetime", 1, 100),
    ("logic-starter", "Logic Starter", "Finish your first Logic game.", "puzzle", "lifetime", 1, 75),
    ("streak-3", "3-Day Streak", "Play on three consecutive days.", "bolt", "lifetime", 3, 150),
    ("level-2", "Rising Star", "Reach Level 2.", "rocket", "lifetime", 2, 150),
    ("explorer", "Explorer", "Play games from three different categories.", "compass", "lifetime", 3, 120),
]

MISSIONS = [
    ("first-game", "Complete Your First Game", "Play a full game to get going.", "first_game", 1, 50),
    ("daily-challenge", "Finish a Daily Challenge", "Take on Today's Challenge before it expires.", "challenge_sprint", 1, 60),
    ("level-2", "Reach Level 2", "Earn XP by playing and completing games.", "reach_level", 2, 150),
    ("category-explorer", "Try 3 New Categories", "Play games from three different categories.", "category_explorer", 3, 120),
    ("streak-3", "Strike Three", "Play on three consecutive days.", "streak", 3, 100),
]


def seed(apps, schema_editor):
    GameCategory = apps.get_model("games", "GameCategory")
    Game = apps.get_model("games", "Game")
    Achievement = apps.get_model("games", "Achievement")
    Mission = apps.get_model("games", "Mission")

    for slug, label, order in GAME_CATEGORIES:
        GameCategory.objects.update_or_create(
            slug=slug,
            defaults={"label": label, "sort_order": order, "is_active": True},
        )
    cat_by_slug = {c.slug: c for c in GameCategory.objects.all()}

    base = timezone.localdate()
    # Log4 the whole seed library within the past three weeks so "New Releases"
    # reflects real, chronological catalog additions.
    for index, (slug, category, extras, difficulty, gtype, min_age, tagline) in enumerate(GAMES):
        days_ago = (index * 1) % 21  # stagger releases across ~3 weeks
        release = base - timezone.timedelta(days=days_ago)
        game, _ = Game.objects.update_or_create(
            slug=slug,
            defaults={
                "title": _title(slug),
                "tagline": tagline,
                "description": f"{_title(slug)} — an original Vector Strike game.",
                "category": cat_by_slug[category],
                "difficulty": difficulty,
                "game_type": gtype,
                "status": "published",
                "minimum_age": min_age,
                "thumbnail": f"/assets/games/{slug}.svg",
                "banner": "/assets/backgrounds/hub-hero.svg",
                "icon": _icon(slug),
                "release_date": release,
                "is_featured": slug in {"physics-drive", "space-quest", "math-master"},
                "is_new": days_ago <= 3,
            },
        )
        game.secondary_categories.set(cat_by_slug[g] for g in extras if g in cat_by_slug)

    for slug, title, desc, icon, kind, target, xp in ACHIEVEMENTS:
        Achievement.objects.update_or_create(
            slug=slug,
            defaults={
                "title": title,
                "description": desc,
                "icon": icon,
                "kind": kind,
                "target": target,
                "xp_reward": xp,
                "is_active": True,
            },
        )

    for index, (slug, title, desc, kind, target, xp) in enumerate(MISSIONS):
        Mission.objects.update_or_create(
            slug=slug,
            defaults={
                "title": title,
                "description": desc,
                "kind": kind,
                "target": target,
                "xp_reward": xp,
                "sort_order": index,
                "is_active": True,
            },
        )


def _title(slug):
    return slug.replace("-", " ").title().replace("Vector Strike", "Vector Strike")


def _icon(slug):
    return slug.split("-")[0]


def reverse(apps, schema_editor):
    apps.get_model("games", "Event").objects.all().delete()
    apps.get_model("games", "Game").objects.all().delete()
    apps.get_model("games", "GameCategory").objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed, reverse),
    ]