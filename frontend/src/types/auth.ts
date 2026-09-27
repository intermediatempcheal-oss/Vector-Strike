export interface ProfileInfo {
    display_name: string;
    language: string;
    country: string;
    skill_level: string;
}

export interface SessionUser {
    vector_id: string;
    username: string;
    email: string;
    phone: string | null;
    full_name: string;
    date_of_birth: string | null;
    age_group: string;
    age: number | null;
    age_verified: boolean;
    verification_status: string;
    account_status: string;
    onboarding_completed: boolean;
    region: string;
    profile?: ProfileInfo | null;
    interests: string[];
    play_styles: string[];
}

export interface SessionState {
    authenticated: boolean;
    onboarding_complete: boolean;
    user: SessionUser | null;
}

export interface RegisterResponse {
    created: boolean;
    onboarding_complete: boolean;
    user: SessionUser;
    interests: string[];
    play_styles: string[];
    recommendations: import('./onboarding').GameCard[];
    next: string;
}