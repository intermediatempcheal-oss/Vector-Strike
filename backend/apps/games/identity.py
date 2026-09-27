"""Universal gameplay foundation: mechanic identity + game mode system.

CATEGORY = what the player learns. MECHANIC (``play_kind``) = how they play.
Every play runtime declares its genre, the modes that genuinely make sense
for it, orientation, camera, controls and visual style. Individual games may
override modes/orientation on their own row; otherwise the mechanic defaults
below apply. Future categories plug into the same registry.
"""

GAME_MODES = {
    "quick": {
        "label": "Quick Play",
        "summary": "Short 1–3 minute session.",
        "rounds": 3,
    },
    "campaign": {
        "label": "Campaign",
        "summary": "Progressive levels ending in a boss stage.",
        "rounds": 5,
    },
    "survival": {
        "label": "Survival",
        "summary": "Runs until you fail. Difficulty keeps climbing.",
        "rounds": 8,
    },
    "time_attack": {
        "label": "Time Attack",
        "summary": "Clear every stage as fast as possible.",
        "rounds": 4,
    },
    "endless": {
        "label": "Endless",
        "summary": "Generated stages keep coming until you stop.",
        "rounds": 8,
    },
    "challenge": {
        "label": "Challenge",
        "summary": "A hard mission with a strict accuracy target.",
        "rounds": 3,
    },
    "boss": {
        "label": "Boss",
        "summary": "A multi-stage system that represents the concept.",
        "rounds": 3,
    },
}

DEFAULT_MODE = "quick"

ORIENTATIONS = {"landscape", "portrait", "adaptive"}

MECHANICS = {
    "quanta-calc": {
        "genre": "Calculation Runner",
        "verbs": ["Calculate", "Charge", "Survive"],
        "modes": ["quick", "survival", "endless", "challenge"],
        "orientation": "adaptive",
        "camera": "fixed",
        "visual_style": "futuristic sci-fi",
        "controls": {
            "movement": "None — stay locked on the reactor",
            "primary": "Type the answer, Enter to fire",
            "mobile": "Numeric keypad, tap Lock",
            "desktop": "Number keys + Enter",
        },
        "tutorial": "Solve the charge to power the reactor",
        "mastery_titles": ["Bronze Calculator", "Silver Calculator", "Gold Calculator", "Master Calculator"],
    },
    "logix-seq": {
        "genre": "Pattern Investigation",
        "verbs": ["Observe", "Deduce", "Unlock"],
        "modes": ["quick", "campaign", "time_attack", "challenge"],
        "orientation": "portrait",
        "camera": "fixed",
        "visual_style": "minimalist",
        "controls": {
            "movement": "None",
            "primary": "Pick the next term to open the gate",
            "mobile": "Tap an option",
            "desktop": "Click or keys 1–5",
        },
        "tutorial": "Find the rule, open the gate",
        "mastery_titles": ["Bronze Analyst", "Silver Analyst", "Gold Analyst", "Master Analyst"],
    },
    "pulse-timing": {
        "genre": "Rhythm Reaction",
        "verbs": ["Watch", "Time", "Strike"],
        "modes": ["quick", "survival", "endless", "challenge"],
        "orientation": "adaptive",
        "camera": "side-scrolling",
        "visual_style": "cyberpunk",
        "controls": {
            "movement": "None — the marker moves for you",
            "primary": "Fire when the marker crosses the zone",
            "mobile": "Tap Fire",
            "desktop": "Space",
        },
        "tutorial": "Press SPACE when the marker hits the zone",
        "mastery_titles": ["Bronze Pulse", "Silver Pulse", "Gold Pulse", "Master Pulse"],
    },
    "vector-dodge": {
        "genre": "Lane Runner",
        "verbs": ["Run", "Dodge", "Survive"],
        "modes": ["quick", "survival", "endless", "boss"],
        "orientation": "landscape",
        "camera": "top-down",
        "visual_style": "space",
        "controls": {
            "movement": "Switch lanes",
            "primary": "Dodge incoming blocks",
            "mobile": "Swipe or tap the lane arrows",
            "desktop": "A/D or Arrow keys",
        },
        "tutorial": "Move with ← → to dodge the blocks",
        "mastery_titles": ["Bronze Runner", "Silver Runner", "Gold Runner", "Master Runner"],
    },
    "cipher-sort": {
        "genre": "Decode Puzzle",
        "verbs": ["Swap", "Decode", "Solve"],
        "modes": ["quick", "campaign", "time_attack", "challenge"],
        "orientation": "portrait",
        "camera": "fixed",
        "visual_style": "mystery",
        "controls": {
            "movement": "None",
            "primary": "Tap two tiles to swap them",
            "mobile": "Tap tiles",
            "desktop": "Click tiles",
        },
        "tutorial": "Swap tiles into ascending order to decode",
        "mastery_titles": ["Bronze Decoder", "Silver Decoder", "Gold Decoder", "Master Decoder"],
    },
    "synapse-match": {
        "genre": "Memory Match",
        "verbs": ["Memorize", "Flip", "Match"],
        "modes": ["quick", "campaign", "time_attack", "challenge"],
        "orientation": "portrait",
        "camera": "fixed",
        "visual_style": "laboratory",
        "controls": {
            "movement": "None",
            "primary": "Flip two cards to match",
            "mobile": "Tap cards",
            "desktop": "Click cards",
        },
        "tutorial": "Memorize, then match the pairs",
        "mastery_titles": ["Bronze Synapse", "Silver Synapse", "Gold Synapse", "Master Synapse"],
    },
    "forge-order": {
        "genre": "Build & Assemble",
        "verbs": ["Plan", "Assemble", "Launch"],
        "modes": ["quick", "campaign", "challenge", "boss"],
        "orientation": "landscape",
        "camera": "isometric",
        "visual_style": "city simulation",
        "controls": {
            "movement": "None",
            "primary": "Place steps in the correct build order",
            "mobile": "Tap parts",
            "desktop": "Click parts or keys 1–5",
        },
        "tutorial": "Place each part in the order shown by the blueprint",
        "mastery_titles": ["Bronze Builder", "Silver Builder", "Gold Builder", "Master Builder"],
    },
    "orbit-gather": {
        "genre": "Exploration Collector",
        "verbs": ["Scan", "Navigate", "Collect"],
        "modes": ["quick", "survival", "endless", "time_attack"],
        "orientation": "landscape",
        "camera": "top-down",
        "visual_style": "space",
        "controls": {
            "movement": "Jump between sectors",
            "primary": "Collect the beacon before it fades",
            "mobile": "Tap a sector",
            "desktop": "Click or keys 1–9",
        },
        "tutorial": "Tap the glowing beacon before it fades",
        "mastery_titles": ["Bronze Explorer", "Silver Explorer", "Gold Explorer", "Master Explorer"],
    },
}

FALLBACK_KIND = "logix-seq"


def mechanic_for(play_kind):
    return MECHANICS.get(play_kind or "", MECHANICS[FALLBACK_KIND])


def modes_for(game):
    """Only the modes that make sense for this game, in display order."""
    override = [m for m in (game.game_modes or []) if m in GAME_MODES]
    return override or list(mechanic_for(game.play_kind)["modes"])


def orientation_for(game):
    if game.orientation in ORIENTATIONS:
        return game.orientation
    return mechanic_for(game.play_kind)["orientation"]


def identity_payload(game):
    mech = mechanic_for(game.play_kind)
    return {
        "genre": mech["genre"],
        "verbs": mech["verbs"],
        "orientation": orientation_for(game),
        "camera": mech["camera"],
        "visual_style": game.visual_style or mech["visual_style"],
        "modes": [
            {"slug": slug, "label": GAME_MODES[slug]["label"], "summary": GAME_MODES[slug]["summary"]}
            for slug in modes_for(game)
        ],
    }


def detail_identity_payload(game):
    mech = mechanic_for(game.play_kind)
    data = identity_payload(game)
    data["control_scheme"] = mech["controls"]
    data["tutorial"] = mech["tutorial"]
    return data


# ---------------------------------------------------------------------------
# Mastery — derived from genuine performance, never a free badge.
# ---------------------------------------------------------------------------

MASTERY_THRESHOLDS = [(85, 3), (65, 2), (40, 1), (0, 0)]


def mastery_score(best_accuracy, completion_percentage, runs):
    """0–100 blend of best accuracy, stage completion and practice volume."""
    if runs <= 0:
        return 0
    practice = min(100, runs * 10)
    score = best_accuracy * 0.5 + completion_percentage * 0.35 + practice * 0.15
    return max(0, min(100, int(round(score))))


def mastery_payload(game, best_accuracy, completion_percentage, runs):
    score = mastery_score(best_accuracy, completion_percentage, runs)
    titles = mechanic_for(game.play_kind)["mastery_titles"]
    tier = next(t for threshold, t in MASTERY_THRESHOLDS if score >= threshold)
    next_threshold = next(
        (threshold for threshold, t in reversed(MASTERY_THRESHOLDS) if t == tier + 1),
        None,
    )
    return {
        "score": score,
        "tier": tier,
        "title": titles[tier] if runs > 0 else "Unranked",
        "next_title": titles[tier + 1] if tier + 1 < len(titles) else None,
        "next_at": next_threshold,
    }
