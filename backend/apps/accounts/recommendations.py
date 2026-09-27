"""First-experience game suggestions.

This is the *seed* of the Vector Recommendation Engine (Phase 9). It maps a
new member's onboarding interests to an initial set of original game cards so
the first experience is personalised. The interface is intentionally small so
the full engine can supersede it without touching the onboarding flow.
"""

# Interest slug -> original Vector Strike game card.
GAME_CATALOG = {
    "mathematics": {
        "slug": "math-master",
        "title": "Quanta Blitz",
        "tagline": "Solve fast, level faster.",
        "icon": "math",
        "reason": "Because you like QUANTA",
    },
    "science": {
        "slug": "science-lab",
        "title": "Nexus Lab",
        "tagline": "Experiment, discover, amaze.",
        "icon": "science",
        "reason": "Because you like NEXUS",
    },
    "physics": {
        "slug": "physics-drive",
        "title": "Vector Drive",
        "tagline": "Speed built on real physics.",
        "icon": "physics",
        "reason": "Because you like VECTOR",
    },
    "chemistry": {
        "slug": "chem-fusion",
        "title": "Circuit Fusion",
        "tagline": "Mix elements, craft reactions.",
        "icon": "chemistry",
        "reason": "Because you like CIRCUIT",
    },
    "geography": {
        "slug": "globe-runner",
        "title": "Orbit Runner",
        "tagline": "Rush across the whole world.",
        "icon": "geography",
        "reason": "Because you like ORBIT",
    },
    "history": {
        "slug": "time-voyagers",
        "title": "Strata Voyagers",
        "tagline": "Travel eras, change nothing, learn everything.",
        "icon": "history",
        "reason": "Because you like STRATA",
    },
    "languages": {
        "slug": "word-bloom",
        "title": "Cipher Bloom",
        "tagline": "Grow your language garden.",
        "icon": "languages",
        "reason": "Because you like CIPHER",
    },
    "logic": {
        "slug": "logic-arena",
        "title": "Logix Arena",
        "tagline": "Reason your way to victory.",
        "icon": "logic",
        "reason": "Because you like LOGIX",
    },
    "coding": {
        "slug": "code-forge",
        "title": "Forge Code",
        "tagline": "Forge programs from pure thought.",
        "icon": "coding",
        "reason": "Because you like FORGE",
    },
    "strategy": {
        "slug": "strategy-command",
        "title": "Tactix Command",
        "tagline": "Out-think every move.",
        "icon": "strategy",
        "reason": "Because you like TACTIX",
    },
    "racing": {
        "slug": "racing-vector",
        "title": "Pulse Racer",
        "tagline": "Outrace rivals across neon circuits.",
        "icon": "racing",
        "reason": "Because you like PULSE",
    },
    "puzzles": {
        "slug": "puzzle-vault",
        "title": "Synapse Vault",
        "tagline": "Crack the combination.",
        "icon": "puzzles",
        "reason": "Because you like SYNAPSE",
    },
    "memory": {
        "slug": "memory-matrix",
        "title": "Core Matrix",
        "tagline": "Remember more than anyone.",
        "icon": "memory",
        "reason": "Because you like CORE",
    },
    "environment": {
        "slug": "eco-guardian",
        "title": "Dominion Guardian",
        "tagline": "Protect a living planet.",
        "icon": "environment",
        "reason": "Because you like DOMINION",
    },
    "money-finance": {
        "slug": "finance-sim",
        "title": "Market Sim",
        "tagline": "Grow, save, invest, win.",
        "icon": "finance",
        "reason": "Because you like MARKET",
    },
    "space": {
        "slug": "space-quest",
        "title": "Orbit Quest",
        "tagline": "Chart the furthest frontiers.",
        "icon": "space",
        "reason": "Because you like ORBIT",
    },
    "creativity": {
        "slug": "idea-studio",
        "title": "Forge Studio",
        "tagline": "Build worlds from imagination.",
        "icon": "creativity",
        "reason": "Because you like FORGE",
    },
    "adventure": {
        "slug": "quest-frontier",
        "title": "Orbit Frontier",
        "tagline": "Every path hides a challenge.",
        "icon": "adventure",
        "reason": "Because you like ORBIT",
    },
}

# Play-style signals can re-order recommendations later.
PLAY_STYLE_SIGNALS = {
    "fast-competitive": 1.2,
    "puzzle-solver": 1.1,
    "strategy": 1.1,
    "explore": 1.0,
    "challenge-myself": 1.0,
    "social": 0.9,
    "story-adventure": 1.0,
}


def first_experience_recommendations(interest_slugs, play_style_slugs=None, limit=3):
    """Return curated game cards derived from a member's interests."""
    play_style_slugs = play_style_slugs or []
    cards = []
    for index, slug in enumerate(interest_slugs):
        entry = GAME_CATALOG.get(slug)
        if not entry:
            continue
        boost = max(
            (PLAY_STYLE_SIGNALS.get(ps, 1.0) for ps in play_style_slugs),
            default=1.0,
        )
        cards.append({**entry, "boost": round(boost, 2), "rank": index})

    cards.sort(key=lambda c: (c["boost"] * -1, c["rank"]))
    cards = cards[:limit]

    # Preserve a stable id per card for the response.
    for position, card in enumerate(cards):
        card["id"] = f"{card['slug']}-{position + 1}"
        card.pop("rank", None)
        card.pop("boost", None)
    return cards