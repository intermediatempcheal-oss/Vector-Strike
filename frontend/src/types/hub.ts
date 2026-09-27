import { GameCard, HubCategoryIdentity, TrendingBlock } from './home';

export interface GameSessionState {
    id: string;
    game_slug: string;
    status: 'started' | 'completed' | 'failed' | 'abandoned';
    started_at: string;
    completed_at: string | null;
    score: number;
    accuracy: number;
    level_reached: number;
    duration_seconds: number;
    xp_earned: number;
}

export interface GameDetail extends GameCard {
    description: string;
    instructions: string;
    controls: string;
    play_count: number;
    best_score: number;
    best_accuracy: number;
    best_level: number;
    best_completed_at: string | null;
    last_result: GameSessionState | null;
    related_games: GameCard[];
}

export interface HubFeed {
    categories: HubCategoryIdentity[];
    continue_running: GameCard[];
    recommended: GameCard[];
    trending: TrendingBlock;
    new_drops: GameCard[];
    quick_runs: GameCard[];
    deep_runs: GameCard[];
    challenge_mode: GameCard[];
}

export interface CategoryPage {
    category: HubCategoryIdentity & { slug: string; ident: string };
    featured: GameCard[];
    quick_runs: GameCard[];
    deep_runs: GameCard[];
    games: {
        results: GameCard[];
        has_more: boolean;
        total: number;
        page: number;
    };
}

export interface CatalogPage {
    results: GameCard[];
    has_more: boolean;
    total: number;
    page: number;
    page_size: number;
}

export interface HubSearchResult {
    query: string;
    games: GameCard[];
    categories: HubCategoryIdentity[];
    has_more: boolean;
}

export interface RunReport {
    score: number;
    accuracy: number;
    level_reached: number;
    duration_seconds: number;
    outcome: 'completed' | 'failed';
}

export interface StartSessionPayload {
    session: GameSessionState;
    game: GameCard;
}

export type HubLoadState = 'loading' | 'ready' | 'error';