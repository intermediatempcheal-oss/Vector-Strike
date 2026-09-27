export type OnboardingStepKey =
    | 'welcome'
    | 'age'
    | 'interests'
    | 'play-style'
    | 'profile'
    | 'guardian'
    | 'verification'
    | 'terms'
    | 'creating'
    | 'complete';

export const ONBOARDING_STEPS: OnboardingStepKey[] = [
    'welcome',
    'age',
    'interests',
    'play-style',
    'profile',
    'guardian',
    'verification',
    'terms',
    'creating',
    'complete',
];

/** Steps shown in the progress indicator (branch merges guardian/verification). */
export const PROGRESS_STEPS = [
    'welcome',
    'age',
    'interests',
    'play-style',
    'profile',
    'branch',
    'terms',
];

export const STEP_LABELS: Record<string, string> = {
    welcome: 'Welcome',
    age: 'Age',
    interests: 'Interests',
    'play-style': 'Play style',
    profile: 'Profile',
    guardian: 'Guardian',
    verification: 'Verification',
    terms: 'Terms',
    creating: 'Creating',
    complete: 'Complete',
};

export const GUARDIAN_STEP = 'guardian';
export const VERIFICATION_STEP = 'verification';

export function progressIndex(step: OnboardingStepKey): number {
    const effective = step === 'guardian' || step === 'verification' ? 'branch' : step;
    const idx = PROGRESS_STEPS.indexOf(effective);
    return idx === -1 ? PROGRESS_STEPS.indexOf('welcome') : idx;
}

export const TOTAL_PROGRESS_STEPS = PROGRESS_STEPS.length;