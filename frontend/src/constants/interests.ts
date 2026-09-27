export interface InterestVisual {
    gradient: string;
    emojiGlyph: string;
}

/** Visual identity per interest category (overlay on top of backend catalog). */
export const INTEREST_VISUALS: Record<string, InterestVisual> = {
    mathematics: { gradient: 'linear-gradient(135deg,#6d28d9,#8b5cf6)', emojiGlyph: '∑' },
    science: { gradient: 'linear-gradient(135deg,#0369a1,#38bdf8)', emojiGlyph: '◬' },
    physics: { gradient: 'linear-gradient(135deg,#b45309,#f59e0b)', emojiGlyph: '∿' },
    chemistry: { gradient: 'linear-gradient(135deg,#047857,#34d399)', emojiGlyph: '◔' },
    geography: { gradient: 'linear-gradient(135deg,#15803d,#4ade80)', emojiGlyph: '◎' },
    history: { gradient: 'linear-gradient(135deg,#c2410c,#fb923c)', emojiGlyph: '⏳' },
    languages: { gradient: 'linear-gradient(135deg,#be123c,#fb7185)', emojiGlyph: 'Aa' },
    logic: { gradient: 'linear-gradient(135deg,#6d28d9,#c084fc)', emojiGlyph: '◈' },
    coding: { gradient: 'linear-gradient(135deg,#4f46e5,#818cf8)', emojiGlyph: '</>' },
    strategy: { gradient: 'linear-gradient(135deg,#7e22ce,#c084fc)', emojiGlyph: '♞' },
    racing: { gradient: 'linear-gradient(135deg,#0e7490,#22d3ee)', emojiGlyph: '⚑' },
    puzzles: { gradient: 'linear-gradient(135deg,#1d4ed8,#60a5fa)', emojiGlyph: '◫' },
    memory: { gradient: 'linear-gradient(135deg,#0f766e,#2dd4bf)', emojiGlyph: '✦' },
    environment: { gradient: 'linear-gradient(135deg,#4d7c0f,#84cc16)', emojiGlyph: '❧' },
    'money-finance': { gradient: 'linear-gradient(135deg,#a16207,#eab308)', emojiGlyph: '¤' },
    space: { gradient: 'linear-gradient(135deg,#4338ca,#22d3ee)', emojiGlyph: '✶' },
    creativity: { gradient: 'linear-gradient(135deg,#be185d,#f472b6)', emojiGlyph: '✺' },
    adventure: { gradient: 'linear-gradient(135deg,#be123c,#fb923c)', emojiGlyph: '✦' },
};

export const PLAY_STYLE_ICONS: Record<string, string> = {
    'fast-competitive': 'bolt',
    'puzzle-solver': 'puzzle',
    strategy: 'brain',
    explore: 'compass',
    'challenge-myself': 'target',
    social: 'users',
    'story-adventure': 'book',
};

export function getInterestVisual(slug: string): InterestVisual {
    return (
        INTEREST_VISUALS[slug] ?? {
            gradient: 'linear-gradient(135deg,#4f46e5,#22d3ee)',
            emojiGlyph: '✦',
        }
    );
}