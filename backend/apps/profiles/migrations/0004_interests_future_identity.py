"""Phase 9 — futuristic onboarding interest identity.

Interest slugs stay internal (stable identifiers used across registration and
recommendations) but the labels players see become the same futuristic
codenames used by the Game Hub categories, so the onboarding → discovery
loop is consistent and no academic subject names are shown anywhere.
"""

from django.db import migrations

# slug -> (codename, description)
INTEREST_REBRAND = [
    ("mathematics", "QUANTA", "Numbers, patterns and endless challenge"),
    ("science", "NEXUS", "Connected reasoning across every field"),
    ("physics", "VECTOR", "Motion, energy and the laws of the universe"),
    ("chemistry", "CIRCUIT", "Elements, reactions and engineered systems"),
    ("geography", "ORBIT", "Countries, worlds and the everyday terrain"),
    ("history", "STRATA", "Layers of how the world got here"),
    ("languages", "CIPHER", "Codes, symbols and new ways to communicate"),
    ("logic", "LOGIX", "Deduction, reasoning and clean thinking"),
    ("coding", "FORGE", "Build systems one command at a time"),
    ("strategy", "TACTIX", "Plan ahead and outmaneuver every rival"),
    ("racing", "PULSE", "Speed, reaction time and lean machines"),
    ("puzzles", "SYNAPSE", "Challenges that reward patience and cleverness"),
    ("memory", "CORE", "Recall, focus and sharp observation"),
    ("environment", "DOMINION", "Manage, plan and defend a living world"),
    ("money-finance", "MARKET", "Money skills, budgets and smart decisions"),
    ("space", "ORBIT", "Stars, planets and the final frontier"),
    ("creativity", "FORGE", "Imagine, draw, build and invent"),
    ("adventure", "ORBIT", "Quests, mystery and brave exploration"),
]


def seed(apps, schema_editor):
    Interest = apps.get_model("profiles", "Interest")
    for slug, codename, description in INTEREST_REBRAND:
        Interest.objects.update_or_create(
            slug=slug,
            defaults={"label": codename, "description": description},
        )


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("profiles", "0003_profile_avatar_profile_level_profile_rank_profile_xp"),
    ]

    operations = [
        migrations.RunPython(seed, reverse),
    ]