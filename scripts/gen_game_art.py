"""Generate original, on-brand game artwork (SVG) for the Game Hub.

Each card gets a deterministic gradient, glyph and grid pattern derived from
its slug — a consistent visual language with zero copyright/placeholder risk.
Run: python scripts/gen_game_art.py
"""

import hashlib
import os
import random

ROOT = r"D:\vector-strike"
OUT = os.path.join(ROOT, "frontend", "public", "assets", "games")

GAMES = [
    "math-master", "science-lab", "physics-drive", "chem-fusion", "globe-runner",
    "time-voyagers", "word-bloom", "logic-arena", "code-forge", "strategy-command",
    "racing-vector", "puzzle-vault", "memory-matrix", "eco-guardian", "finance-sim",
    "space-quest", "idea-studio", "quest-frontier",
    "decimal-dash", "prime-sweeper", "atom-blitz", "nature-code", "gravity-run",
    "blueprint-flip", "reaction-chain", "volt-forge", "signal-finder", "route-collect",
    "deep-orbit", "warp-lanes", "relic-run", "epoch-archives", "chrono-sort",
    "glyph-breaker", "echo-run", "pulse-lattice", "signal-ladder", "stack-builder",
    "deploy-run", "spark-deck", "parts-vault", "tactics-map", "king-move",
    "zero-gap", "overclock", "glyph-pairs", "lattice-crack", "quick-blitz",
    "echo-grid", "classic-gauntlet", "balance-eco", "terra-plan", "market-flux",
    "trade-hedge", "flux-dash", "tempo-surge", "crown-hunt", "duel-circuit",
    "zero-lag", "echo-sprint",
]

PALETTES = [
    ("#0e7dd1", "#34d399"),
    ("#7c3aed", "#38bdf8"),
    ("#e11d48", "#fb923c"),
    ("#0d9488", "#a3e635"),
    ("#d97706", "#f43f5e"),
    ("#4338ca", "#22d3ee"),
]

GLYPHS = {
    "math-master": "∑", "science-lab": "⚗", "physics-drive": "⚡", "chem-fusion": "⚛",
    "globe-runner": "◎", "time-voyagers": "⌛", "word-bloom": "✿", "logic-arena": "◆",
    "code-forge": "{}<", "strategy-command": "♞", "racing-vector": "➤", "puzzle-vault": "▣",
    "memory-matrix": "◈", "eco-guardian": "♻", "finance-sim": "¤", "space-quest": "✦",
    "idea-studio": "✎", "quest-frontier": "⌘",
    "decimal-dash": "·.", "prime-sweeper": "ℙ", "atom-blitz": "◉", "nature-code": "❦",
    "gravity-run": "↓", "blueprint-flip": "⬒", "reaction-chain": "→", "volt-forge": "⚡",
    "signal-finder": "⌖", "route-collect": "◍", "deep-orbit": "☄", "warp-lanes": "⟁",
    "relic-run": "⚿", "epoch-archives": "▤", "chrono-sort": "⏳", "glyph-breaker": "⌬",
    "echo-run": "≋", "pulse-lattice": "▦", "signal-ladder": "⯅", "stack-builder": "▥",
    "deploy-run": "⇪", "spark-deck": "✺", "parts-vault": "▧", "tactics-map": "♝",
    "king-move": "♚", "zero-gap": "◼", "overclock": "⌁", "glyph-pairs": "◈",
    "lattice-crack": "⌗", "quick-blitz": "⚡", "echo-grid": "▤", "classic-gauntlet": "▣",
    "balance-eco": "♊", "terra-plan": "♃", "market-flux": "⇅", "trade-hedge": "∿",
    "flux-dash": "≫", "tempo-surge": "♩", "crown-hunt": "♛", "duel-circuit": "⚔",
    "zero-lag": "⊘", "echo-sprint": "≊",
}


def rand(seed, lo, hi):
    rng = random.Random(seed)
    return rng.randint(lo, hi)


def art(slug):
    seed = slug.encode("utf-8")
    digest = int(hashlib.sha256(seed).hexdigest(), 16)
    a, b = PALETTES[digest % len(PALETTES)]
    glyph = GLYPHS.get(slug, slug[:2].upper())
    tilt = digest % 360
    x1, y1, x2, y2 = rand(seed, 0, 30), rand(seed, 0, 30), rand(seed, 70, 100), rand(seed, 70, 100)
    rings = rand(seed, 2, 4)
    ps = []
    for i in range(rings):
        r = 26 + i * 16
        ps.append(f'<circle cx="50" cy="50" r="{r}" fill="none" stroke="rgba(255,255,255,0.10)" stroke-width="1.5"/>')
    dots = "".join(
        '<circle cx="%s" cy="%s" r="1.6" fill="rgba(255,255,255,0.28)"/>' % (x, y)
        for x, y in [(10, 12), (88, 14), (14, 86), (86, 88), (50, 8), (8, 50), (92, 48), (50, 92)]
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" role="img" aria-label="{slug}">'
        f'<defs><linearGradient id="g" x1="{x1/100:.2f}" y1="{y1/100:.2f}" x2="{x2/100:.2f}" y2="{y2/100:.2f}">'
        f'<stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient></defs>'
        f'<rect width="100" height="100" fill="url(#g)"/>'
        f'<g transform="rotate({tilt} 50 50)">{"".join(ps)}</g>'
        f'{dots}'
        f'<circle cx="50" cy="50" r="34" fill="rgba(255,255,255,0.14)"/>'
        f'<text x="50" y="52" text-anchor="middle" dominant-baseline="central" '
        f'font-family="Segoe UI, system-ui, sans-serif" font-size="22" font-weight="700" '
        f'fill="#fff">{glyph}</text></svg>'
    )


def main():
    os.makedirs(OUT, exist_ok=True)
    for slug in GAMES:
        with open(os.path.join(OUT, f"{slug}.svg"), "w", encoding="utf-8") as fh:
            fh.write(art(slug))
    print(f"wrote {len(GAMES)} game artworks -> {OUT}")


if __name__ == "__main__":
    main()