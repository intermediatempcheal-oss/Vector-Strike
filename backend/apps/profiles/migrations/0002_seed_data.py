"""Seed canonical onboarding interests and play styles.

These rows are the source of truth for the onboarding config endpoint and the
relational UserInterest / UserPlayStyle join tables.
"""

from django.db import migrations

INTERESTS = [
    ("mathematics", "Mathematics", "Numbers, patterns and endless challenge", "math", "#7C3AED", 10),
    ("science", "Science", "Experiment, observe and understand the world", "science", "#0EA5E9", 20),
    ("physics", "Physics", "Motion, energy and the laws of the universe", "physics", "#F59E0B", 30),
    ("chemistry", "Chemistry", "Elements, reactions and amazing transformations", "chemistry", "#10B981", 40),
    ("geography", "Geography", "Countries, cultures and the planet we share", "geography", "#22C55E", 50),
    ("history", "History", "Stories of people and eras that shaped today", "history", "#F97316", 60),
    ("languages", "Languages", "Words, grammar and new ways to communicate", "languages", "#EF4444", 70),
    ("logic", "Logic", "Deduction, reasoning and clean thinking", "logic", "#8B5CF6", 80),
    ("coding", "Coding", "Build software one command at a time", "coding", "#6366F1", 90),
    ("strategy", "Strategy", "Plan ahead and outmaneuver every rival", "strategy", "#A855F7", 100),
    ("racing", "Racing", "Speed, reaction time and lean machines", "racing", "#06B6D4", 110),
    ("puzzles", "Puzzles", "Challenges that reward patience and cleverness", "puzzles", "#3B82F6", 120),
    ("memory", "Memory", "Train recall, focus and sharp observation", "memory", "#14B8A6", 130),
    ("environment", "Environment", "Nature, climate and protecting our future", "environment", "#65A30D", 140),
    ("money-finance", "Money & Finance", "Money skills, budgets and smart decisions", "finance", "#CA8A04", 150),
    ("space", "Space", "Stars, planets and the final frontier", "space", "#4F46E5", 160),
    ("creativity", "Creativity", "Imagine, draw, build and invent", "creativity", "#EC4899", 170),
    ("adventure", "Adventure", "Quests, mystery and brave exploration", "adventure", "#F43F5E", 180),
]

PLAY_STYLES = [
    ("fast-competitive", "Fast & Competitive", "Quick matches, sharp reflexes, leaderboard glory", "bolt", "#F59E0B", 10),
    ("puzzle-solver", "Puzzle Solver", "Untangle challenges one step at a time", "puzzle", "#8B5CF6", 20),
    ("strategy", "Think & Strategize", "Think long-term and plan every move", "brain", "#6366F1", 30),
    ("explore", "Explore & Discover", "Wander worlds and uncover hidden secrets", "compass", "#06B6D4", 40),
    ("challenge-myself", "Challenge Myself", "Beat personal records and climb difficulty", "target", "#EF4444", 50),
    ("social", "Play With Others", "Team up, compete and share wins with friends", "users", "#10B981", 60),
    ("story-adventure", "Story & Adventure", "Live inside stories with characters and plot", "book", "#EC4899", 70),
]


def seed_interest(apps, schema_editor):
    Interest = apps.get_model("profiles", "Interest")
    for slug, label, description, icon, accent, sort_order in INTERESTS:
        Interest.objects.update_or_create(
            slug=slug,
            defaults={
                "label": label,
                "description": description,
                "icon": icon,
                "accent": accent,
                "category": "learning",
                "sort_order": sort_order,
                "is_active": True,
            },
        )


def seed_play_styles(apps, schema_editor):
    PlayStyle = apps.get_model("profiles", "PlayStyle")
    for slug, label, description, icon, accent, sort_order in PLAY_STYLES:
        PlayStyle.objects.update_or_create(
            slug=slug,
            defaults={
                "label": label,
                "description": description,
                "icon": icon,
                "accent": accent,
                "sort_order": sort_order,
                "is_active": True,
            },
        )


def remove_seed(apps, schema_editor):
    Interest = apps.get_model("profiles", "Interest")
    PlayStyle = apps.get_model("profiles", "PlayStyle")
    Interest.objects.filter(slug__in=[i[0] for i in INTERESTS]).delete()
    PlayStyle.objects.filter(slug__in=[p[0] for p in PLAY_STYLES]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_interest, remove_seed),
        migrations.RunPython(seed_play_styles, remove_seed),
    ]