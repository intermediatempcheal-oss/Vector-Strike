"""Phase 9 — drop academic subject names from game titles.

Slugs are untouched (stable identifiers) but every original game whose title
contained a subject name now carries a futuristic title matching its category
identity (e.g. math-master -> "Quanta Blitz").
"""

from django.db import migrations

RENAMES = {
    "math-master": "Quanta Blitz",
    "science-lab": "Nexus Lab",
    "physics-drive": "Vector Drive",
    "chem-fusion": "Circuit Fusion",
    "globe-runner": "Orbit Runner",
    "time-voyagers": "Strata Voyagers",
    "word-bloom": "Cipher Bloom",
    "logic-arena": "Logix Arena",
    "code-forge": "Forge Code",
    "strategy-command": "Tactix Command",
    "racing-vector": "Pulse Racer",
    "puzzle-vault": "Synapse Vault",
    "memory-matrix": "Core Matrix",
    "eco-guardian": "Dominion Guardian",
    "finance-sim": "Market Sim",
    "space-quest": "Orbit Quest",
    "idea-studio": "Forge Studio",
    "quest-frontier": "Orbit Frontier",
}


def seed(apps, schema_editor):
    Game = apps.get_model("games", "Game")
    for slug, title in RENAMES.items():
        Game.objects.filter(slug=slug).update(
            title=title, description=f"{title} — an original Vector Strike game."
        )


def reverse(apps, schema_editor):
    Game = apps.get_model("games", "Game")
    for slug, title in RENAMES.items():
        old = slug.replace("-", " ").title()
        Game.objects.filter(slug=slug).update(
            title=old, description=f"{old} — an original Vector Strike game."
        )


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0004_gamehub_catalog"),
    ]

    operations = [
        migrations.RunPython(seed, reverse),
    ]