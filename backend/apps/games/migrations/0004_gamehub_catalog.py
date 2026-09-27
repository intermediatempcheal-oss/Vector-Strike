"""Phase 9 — futuristic category identity + expanded real game catalog.

Every rule from the Phase 9 spec is honored here:

* Academic subject names are never shown to members. Categories keep their
  internal slugs (so onboarding interests, recommendation links and existing
  tests keep stable identifiers) but their surface identity becomes a
  futuristic codename (LOGIX, QUANTA, VECTOR, ...).
* Every game is a genuine Vector Strike title with a real runtime
  (``play_kind``), honest difficulty/duration metadata and per-game rules.
* No member-facing numbers (plays, player counts, ratings) are fabricated.
* The catalog is intentionally large (~60 original games) so categories have
  real depth; the API drives discovery, pagination and empty states.
"""

from django.db import migrations
from django.utils import timezone

# slug -> (codename, tagline, accent, icon, sort_order)
CATEGORY_REBRAND = [
    ("mathematics", "QUANTA", "Calculation, number sense and probability.", "#38bdf8", "quanta", 30),
    ("science", "NEXUS", "Connected reasoning across every field.", "#6366f1", "nexus", 10),
    ("physics", "VECTOR", "Spatial thinking, movement and force.", "#22d3ee", "vector", 40),
    ("chemistry", "CIRCUIT", "Systems, molecules and engineered reactions.", "#34d399", "circuit", 50),
    ("geography", "ORBIT", "Navigation, maps and exploration.", "#06b6d4", "orbit", 90),
    ("history", "STRATA", "Layered knowledge of how the world got here.", "#f59e0b", "strata", 80),
    ("languages", "CIPHER", "Codes, symbols and the patterns of language.", "#f43f5e", "cipher", 70),
    ("logic", "LOGIX", "Pattern recognition, deduction and pure reasoning.", "#8b5cf6", "logix", 20),
    ("coding", "FORGE", "Build, optimize and shape systems.", "#a855f7", "forge", 100),
    ("strategy", "TACTIX", "Plans, risk and out-thinking the board.", "#7c3aed", "tactix", 120),
    ("racing", "PULSE", "Reaction, timing and split-second decisions.", "#fb7185", "pulse", 60),
    ("puzzles", "SYNAPSE", "Patterns that snap into focus.", "#10b981", "synapse", 150),
    ("memory", "CORE", "Quick foundational runs, memory and recall.", "#14b8a6", "core", 180),
    ("environment", "DOMINION", "Manage, plan and defend a living world.", "#65a30d", "dominion", 160),
    ("finance", "MARKET", "Trading, economy and resource allocation.", "#ca8a04", "market", 110),
    ("space", "ORBIT", "Chart the furthest frontiers.", "#06b6d4", "orbit", 95),
    ("creativity", "FORGE", "Create, combine and invent.", "#a855f7", "forge", 105),
    ("adventure", "ORBIT", "Every path hides a challenge.", "#06b6d4", "orbit", 100),
    ("classic", "CORE", "Timeless quick play, no setup.", "#14b8a6", "core", 185),
    ("arcade", "FLUX", "Relentless, adapting, arcade speed.", "#f472b6", "flux", 140),
    ("multiplayer", "APEX", "Competitive rounds against the field.", "#e879f9", "apex", 130),
    ("pulse-x", "PULSE-X", "Precision reaction at the edge of reflex.", "#f9a8d4", "pulse-x", 170),
]

# slug, category, secondary cats, difficulty, game_type, min_age, play_kind,
# duration_minutes, mechanics, tagline
NEW_GAMES = [
    ("decimal-dash", "mathematics", ("arcade",), 2, "solo", 8, "quanta-calc", 8, "Speed · Calculation", "Be the fastest to the decimal point."),
    ("prime-sweeper", "mathematics", ("logic",), 3, "solo", 10, "quanta-calc", 10, "Logic · Numbers", "Flag the primes before the timer melts."),
    ("atom-blitz", "science", ("puzzles",), 2, "solo", 8, "synapse-match", 8, "Fast · Classification", "Classify states of matter at lightning speed."),
    ("nature-code", "science", ("environment",), 2, "solo", 6, "cipher-sort", 8, "Relations · Decode", "Link organisms to their ecosystems fast."),
    ("gravity-run", "physics", ("arcade",), 2, "solo", 6, "vector-dodge", 6, "Movement · Timing", "Shift lanes to land with zero impact."),
    ("blueprint-flip", "physics", ("puzzles",), 3, "solo", 8, "logix-seq", 8, "Spatial · Patterns", "Rotate grids to match the schematic."),
    ("reaction-chain", "chemistry", ("science",), 3, "solo", 10, "cipher-sort", 9, "Systems · Sequence", "Link reagents in the right order."),
    ("volt-forge", "chemistry", ("physics",), 3, "solo", 10, "pulse-timing", 7, "Systems · Timing", "Charge circuits before the surge hits."),
    ("signal-finder", "geography", ("arcade",), 1, "solo", 6, "orbit-gather", 6, "Explore · Navigate", "Hunt the beacon across the terrain."),
    ("route-collect", "geography", ("classic",), 2, "solo", 8, "orbit-gather", 8, "Navigate · Collect", "Colour checkpoints before the storm."),
    ("deep-orbit", "space", ("adventure",), 3, "solo", 10, "orbit-gather", 9, "Explore · Gather", "Chart the far ring and grab what it hides."),
    ("warp-lanes", "space", ("racing",), 2, "solo", 8, "vector-dodge", 7, "Navigate · Timing", "Pick the safest lane through the field."),
    ("relic-run", "adventure", ("history",), 2, "solo", 6, "orbit-gather", 7, "Explore · Collect", "Recover relics across shifting terrain."),
    ("epoch-archives", "history", ("memory",), 2, "solo", 8, "cipher-sort", 8, "Layers · Sequence", "File discoveries into the right era."),
    ("chrono-sort", "history", ("memory",), 2, "solo", 8, "cipher-sort", 7, "Layers · Order", "Line up events from past to future."),
    ("glyph-breaker", "languages", ("logic",), 3, "solo", 8, "cipher-sort", 9, "Decode · Symbols", "Decode symbols before the pattern shifts."),
    ("echo-run", "languages", ("puzzles",), 2, "solo", 6, "synapse-match", 6, "Memory · Sequence", "Echo back the pattern in perfect order."),
    ("pulse-lattice", "logic", ("puzzles",), 3, "solo", 10, "logix-seq", 8, "Pattern · Logic", "Complete the grid pattern on the beat."),
    ("signal-ladder", "logic", ("coding",), 4, "solo", 10, "logix-seq", 9, "Deduction · Logic", "Climb the chain of reasoning before it breaks."),
    ("stack-builder", "coding", ("logic",), 3, "solo", 10, "forge-order", 9, "Build · Sequence", "Arrange commands into a working build."),
    ("deploy-run", "coding", ("strategy",), 3, "solo", 10, "forge-order", 8, "Build · Optimization", "Ship the pipeline in the correct order."),
    ("spark-deck", "creativity", ("classic",), 2, "solo", 8, "forge-order", 8, "Create · Combine", "Assemble the parts into something new."),
    ("parts-vault", "creativity", ("puzzles",), 3, "solo", 10, "forge-order", 9, "Create · Construct", "Slot the parts into a working whole."),
    ("tactics-map", "strategy", ("multiplayer",), 3, "solo", 10, "logix-seq", 9, "Plan · Position", "Position your units, counter the push."),
    ("king-move", "strategy", ("logic",), 4, "solo", 12, "logix-seq", 9, "Tactics · Risk", "One clever move keeps you in control."),
    ("zero-gap", "racing", ("arcade",), 2, "solo", 6, "pulse-timing", 5, "Reaction · Timing", "Burst on the green light, nothing else."),
    ("overclock", "racing", ("multiplayer",), 4, "solo", 12, "pulse-timing", 7, "Reflex · Rhythm", "Stay in the zone as the tempo climbs."),
    ("glyph-pairs", "puzzles", ("memory",), 1, "solo", 6, "synapse-match", 5, "Memory · Match", "Flip and match the hidden glyphs."),
    ("lattice-crack", "puzzles", ("languages",), 3, "solo", 10, "logix-seq", 9, "Pattern · Cipher", "Break the repeating key before time runs out."),
    ("quick-blitz", "memory", ("arcade",), 1, "solo", 6, "pulse-timing", 4, "Speed · Mix", "A fast hit of rapid-fire challenges."),
    ("echo-grid", "memory", ("puzzles",), 2, "solo", 8, "synapse-match", 6, "Memory · Sequence", "Recall the flashing grid sequence."),
    ("classic-gauntlet", "classic", ("memory",), 2, "solo", 6, "orbit-gather", 5, "Classic · Mix", "The timeless mixed run, pure and fast."),
    ("balance-eco", "environment", ("science",), 2, "solo", 8, "forge-order", 8, "Manage · Optimize", "Keep the ecosystem in equilibrium."),
    ("terra-plan", "environment", ("strategy",), 4, "solo", 12, "forge-order", 10, "Manage · Long-term", "Plan the build order that saves the biome."),
    ("market-flux", "finance", ("strategy",), 3, "solo", 12, "pulse-timing", 9, "Economy · Timing", "Buy, hold or fold before the swing."),
    ("trade-hedge", "finance", ("logic",), 4, "solo", 12, "logix-seq", 10, "Economy · Risk", "Cover positions as momentum shifts."),
    ("flux-dash", "arcade", ("racing",), 3, "solo", 8, "vector-dodge", 6, "Adapt · Speed", "Adapt to the changing course on the fly."),
    ("tempo-surge", "arcade", ("puzzles",), 2, "solo", 6, "pulse-timing", 5, "Rhythm · Timing", "Match the surge or fall off the rhythm."),
    ("crown-hunt", "multiplayer", ("strategy",), 4, "solo", 12, "logix-seq", 10, "Competitive · Strategy", "Outplay the field for the crown."),
    ("duel-circuit", "multiplayer", ("racing",), 4, "solo", 10, "pulse-timing", 6, "Versus · Reflex", "Head-to-head rounds, only reflexes decide."),
    ("zero-lag", "pulse-x", ("arcade",), 3, "solo", 10, "pulse-timing", 5, "Reaction · Precision", "React in the smallest possible window."),
    ("echo-sprint", "pulse-x", ("memory",), 4, "solo", 12, "synapse-match", 6, "Reflex · Memory", "Keep the chain alive as speed doubles."),
]

FEATURED_NEW = {
    "prime-sweeper",
    "deep-orbit",
    "stack-builder",
    "terra-plan",
    "crown-hunt",
}

# slug: play_kind, duration, mechanics, tagline for catalog builds
LEGACY_SETUP = {
    "math-master": ("quanta-calc", 8, "Speed · Calculation"),
    "science-lab": ("synapse-match", 8, "Fast · Classification"),
    "physics-drive": ("vector-dodge", 6, "Speed · Movement"),
    "chem-fusion": ("cipher-sort", 9, "Combine · Sequence"),
    "globe-runner": ("orbit-gather", 8, "Explore · Navigate"),
    "time-voyagers": ("cipher-sort", 8, "Layers · Sequence"),
    "word-bloom": ("cipher-sort", 7, "Words · Decode"),
    "logic-arena": ("logix-seq", 8, "Pattern · Logic"),
    "code-forge": ("forge-order", 9, "Build · Sequence"),
    "strategy-command": ("logix-seq", 10, "Plan · Position"),
    "racing-vector": ("pulse-timing", 6, "Speed · Reaction"),
    "puzzle-vault": ("logix-seq", 8, "Pattern · Logic"),
    "memory-matrix": ("synapse-match", 6, "Memory · Match"),
    "eco-guardian": ("forge-order", 9, "Manage · Optimize"),
    "finance-sim": ("pulse-timing", 9, "Economy · Timing"),
    "space-quest": ("orbit-gather", 9, "Explore · Gather"),
    "idea-studio": ("forge-order", 8, "Create · Combine"),
    "quest-frontier": ("orbit-gather", 7, "Explore · Collect"),
}

RUN_SETUP = {
    "quanta-calc": (
        "Solve each calculation before the timer empties. Every correct answer raises your score multiplier.",
        "Type the answer and press Enter to lock it in.",
    ),
    "logix-seq": (
        "Spot the pattern and pick what comes next. Patterns grow faster and trickier each round.",
        "Tap the tile you believe is next.",
    ),
    "pulse-timing": (
        "Time your action to land inside the glowing zone. The window shrinks as levels climb.",
        "Tap the field or press Space at the right moment.",
    ),
    "vector-dodge": (
        "Keep your craft in the safe lane. Obstacles close in from all angles as you level up.",
        "Use the arrow keys (or A/D) to move and dodge.",
    ),
    "cipher-sort": (
        "Rearrange the scrambled tiles into the correct sequence before the round ends.",
        "Tap a tile to cycle it, or drag tiles into position.",
    ),
    "synapse-match": (
        "Flip tiles to reveal hidden pairs and match them fast for a streak bonus.",
        "Tap two tiles to attempt a match.",
    ),
    "forge-order": (
        "Assemble the correct build order. Wrong picks cost build time.",
        "Tap the options in the correct sequence.",
    ),
    "orbit-gather": (
        "Navigate your probe to collect targets while the field shifts.",
        "Recommended target tiles light up; tap them in time.",
    ),
}


def _title(slug):
    return slug.replace("-", " ").title()


def seed(apps, schema_editor):
    GameCategory = apps.get_model("games", "GameCategory")
    Game = apps.get_model("games", "Game")

    for slug, codename, tagline, accent, icon, order in CATEGORY_REBRAND:
        GameCategory.objects.update_or_create(
            slug=slug,
            defaults={
                "label": codename,
                "codename": codename,
                "tagline": tagline,
                "accent": accent,
                "icon": icon,
                "sort_order": order,
                "is_active": True,
            },
        )
    cats = {c.slug: c for c in GameCategory.objects.all()}

    base = timezone.localdate()

    def apply_setup(game, play_kind, duration, mechanics):
        instructions, controls = RUN_SETUP.get(
            play_kind, ("Follow the on-screen goals each round.", "Use the on-screen controls to play.")
        )
        game.play_kind = play_kind
        game.duration_minutes = duration
        game.mechanics = mechanics
        game.instructions = instructions
        game.controls = controls
        game.save(update_fields=[
            "play_kind", "duration_minutes", "mechanics", "instructions", "controls"
        ])

    for game in Game.objects.all():
        setup = LEGACY_SETUP.get(game.slug)
        if setup:
            apply_setup(game, *setup)

    for index, (slug, category, extras, difficulty, gtype, min_age, play_kind, duration, mechanics, tagline) in enumerate(NEW_GAMES):
        days_ago = (index * 1) % 21
        release = base - timezone.timedelta(days=days_ago)
        title = _title(slug)
        game, _ = Game.objects.update_or_create(
            slug=slug,
            defaults={
                "title": title,
                "tagline": tagline,
                "description": f"{title} — an original Vector Strike game.",
                "category": cats[category],
                "difficulty": difficulty,
                "game_type": gtype,
                "status": "published",
                "minimum_age": min_age,
                "thumbnail": f"/assets/games/{slug}.svg",
                "banner": "/assets/backgrounds/hub-hero.svg",
                "icon": slug.split("-")[0],
                "release_date": release,
                "is_featured": slug in FEATURED_NEW,
                "is_new": days_ago <= 3,
            },
        )
        game.secondary_categories.set(cats[s] for s in extras if s in cats)
        apply_setup(game, play_kind, duration, mechanics)


def reverse(apps, schema_editor):
    Game = apps.get_model("games", "Game")
    Game.objects.filter(slug__in=[row[0] for row in NEW_GAMES]).delete()
    apps.get_model("games", "GameCategory").objects.filter(slug="pulse-x").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0003_gamesession_alter_gamecategory_options_game_controls_and_more"),
    ]

    operations = [
        migrations.RunPython(seed, reverse),
    ]