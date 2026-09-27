import { SessionUser } from './auth';

export type Difficulty = 'relaxed' | 'easy' | 'moderate' | 'challenging' | 'expert';

export interface GameCategoryRef {
    slug: string;
    label: string;
    codename?: string;
    accent?: string;
    icon?: string;
    tagline?: string;
}

export interface GameProgress {
    current_level: number;
    completion_percentage: number;
    xp: number;
    score: number;
    games_played: number;
    playtime_seconds?: number;
    last_played_at: string | null;
}

export interface GameCard {
    id: string;
    slug: string;
    title: string;
    tagline: string;
    category: GameCategoryRef;
    categories: string[];
    difficulty: string;
    difficulty_label: string;
    difficulty_stars: boolean[];
    game_type: string;
    play_kind?: string;
    mechanics?: string;
    duration_minutes?: number;
    content_rating?: string;
    thumbnail: string;
    banner: string;
    icon: string;
    minimum_age: number;
    maximum_age: number;
    release_date: string | null;
    is_new: boolean;
    is_featured: boolean;
    status: string;
    description?: string;
    progress?: GameProgress;
}

export interface TrendingGame extends GameCard {
    active_members: number;
    total_plays: number;
    last_play: string | null;
}

export interface ProfileProgress {
    display_name: string;
    level: number;
    xp: number;
    xp_for_next: number;
    xp_progress: number;
    rank: string;
    skill_level: string;
    avatar: string;
    avatar_url: string;
}

export interface HomeStats {
    games_played: number;
    total_game_xp: number;
    categories_played: number;
}

export interface StartYourFirst {
    interests: Array<{ slug: string; label: string }>;
}

export interface DiscoverySection {
    key: string;
    title: string;
    games: GameCard[];
}

export interface HubCategoryIdentity {
    ident: string;
    label: string;
    slug: string;
    tagline: string;
    accent: string;
    icon: string;
    games_count: number;
    categories: string[];
    link: string;
}

export interface CategorySummary {
    slug: string;
    label: string;
    codename?: string;
    tagline?: string;
    accent?: string;
    icon?: string;
    games_count: number;
}

export interface TrendingBlock {
    available: boolean;
    games: TrendingGame[];
}

export interface DailyChallenge {
    active: boolean;
    title: string;
    description: string;
    goal: string;
    reward_xp: number;
    expires_at: string | null;
    game: GameCard;
}

export interface Mission {
    slug: string;
    title: string;
    description: string;
    target: number;
    progress: number;
    completed: boolean;
    xp_reward: number;
}

export interface Achievement {
    slug: string;
    title: string;
    description: string;
    icon: string;
    earned_at: string;
}

export interface HomeEvent {
    slug: string;
    title: string;
    description: string;
    banner: string;
    status: string;
    starts_at: string;
    ends_at: string | null;
}

export interface HomeFeed {
    user: SessionUser;
    profile: ProfileProgress | null;
    stats: HomeStats;
    continue_playing: GameCard[];
    start_your_first_challenge: StartYourFirst | null;
    recommendations: GameCard[];
    sections: DiscoverySection[];
    hub_categories: HubCategoryIdentity[];
    quick_runs: GameCard[];
    categories: CategorySummary[];
    games: GameCard[];
    trending: TrendingBlock;
    new_games: GameCard[];
    daily_challenge: DailyChallenge | null;
    missions: Mission[];
    achievements: Achievement[];
    events: HomeEvent[];
}