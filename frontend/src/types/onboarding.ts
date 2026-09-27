export interface AgeRange {
    value: string;
    label: string;
}

export interface CatalogItem {
    slug: string;
    label: string;
    description: string;
    icon: string;
    accent: string;
    sort_order: number;
}

export interface RegionVerificationConfig {
    required: boolean;
    min_age: number;
    methods: string[];
}

export interface OnboardingConfig {
    age_ranges: AgeRange[];
    min_interests: number;
    min_age: number;
    guardian_age_threshold: number;
    verification_age_threshold: number;
    requires_age_verification: boolean;
    region_verification: Record<string, RegionVerificationConfig>;
    interests: CatalogItem[];
    play_styles: CatalogItem[];
}

export interface BranchInfo {
    age: number | null;
    branch: 'guardian' | 'verification' | 'none';
    guardian_threshold: number;
    verification_threshold: number;
    region?: string;
    region_config?: {
        required: boolean;
        min_age: number;
        methods: string[];
    };
    date_of_birth?: string;
}

export interface UsernameCheckResult {
    available: boolean;
    valid: boolean;
    message: string | null;
}

export interface OnboardingProgressResume {
    current_step: string;
    completed_steps: string[];
}

export type OnboardingBranch = 'guardian' | 'verification' | 'none';

export interface RegistrationPayload {
    full_name: string;
    username: string;
    email: string;
    phone: string;
    date_of_birth: string;
    password: string;
    region?: string;
    age_group?: string;
    interests: string[];
    play_styles: string[];
    terms_accepted: boolean;
    guardian_email?: string;
    guardian_name?: string;
    guardian_phone?: string;
    verification_token?: string;
}

export interface GameCard {
    id: string;
    slug: string;
    title: string;
    tagline: string;
    icon: string;
    reason: string;
}

export interface UploadDocumentResult {
    uploaded: boolean;
    verification_token: string;
    document_type: string;
    status: string;
    expires_in_hours: number;
}