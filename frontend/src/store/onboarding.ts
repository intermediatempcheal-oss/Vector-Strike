import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import {
    ONBOARDING_STEPS,
    OnboardingStepKey,
} from '../constants/onboarding';
import { BranchInfo } from '../types/onboarding';
import { RegisterResponse, SessionUser } from '../types/auth';

interface OnboardingState {
    step: OnboardingStepKey;
    maxUnlockedStep: number;

    ageRange: string | null;
    interests: string[];
    playStyles: string[];

    fullName: string;
    dob: string;
    email: string;
    phone: string;
    username: string;
    region: string;

    guardianEmail: string;
    guardianName: string;
    guardianPhone: string;

    /** In-memory only, never persisted. */
    password: string;
    /** In-memory only, never persisted. */
    verificationToken: string;

    branchInfo: BranchInfo | null;
    termsAccepted: boolean;

    registerResult: {
        vector_id: string;
        username: string;
        full_name: string;
        interests: string[];
        play_styles: string[];
        recommendations: RegisterResponse['recommendations'];
    } | null;

    registeredUser: SessionUser | null;

    completeStep: (step: OnboardingStepKey) => void;
    unlock: (step: OnboardingStepKey) => void;
    goto: (step: OnboardingStepKey) => void;
    set: (patch: Partial<Omit<OnboardingState, keyof Actions>>) => void;
    setBranchInfo: (info: BranchInfo) => void;
    acceptTerms: () => void;
    setRegisterResult: (res: RegisterResponse) => void;
    reset: () => void;
}

type Actions = Pick<
    OnboardingState,
    | 'completeStep'
    | 'unlock'
    | 'goto'
    | 'set'
    | 'setBranchInfo'
    | 'acceptTerms'
    | 'setRegisterResult'
    | 'reset'
>;

function indexOf(step: OnboardingStepKey): number {
    return Math.max(0, ONBOARDING_STEPS.indexOf(step));
}

const partialize = (s: OnboardingState) => ({
    step: s.step,
    maxUnlockedStep: s.maxUnlockedStep,
    ageRange: s.ageRange,
    interests: s.interests,
    playStyles: s.playStyles,
    fullName: s.fullName,
    dob: s.dob,
    email: s.email,
    phone: s.phone,
    username: s.username,
    region: s.region,
    guardianEmail: s.guardianEmail,
    guardianName: s.guardianName,
    guardianPhone: s.guardianPhone,
    branchInfo: s.branchInfo,
    termsAccepted: s.termsAccepted,
    // Sensitive or transient data (password, upload tokens, file handles)
    // are intentionally excluded from storage.
    registerResult: s.registerResult,
});

export const useOnboardingStore = create<OnboardingState>()(
    persist(
        (set, get) => ({
            step: 'welcome',
            maxUnlockedStep: 0,
            ageRange: null,
            interests: [],
            playStyles: [],
            fullName: '',
            dob: '',
            email: '',
            phone: '',
            username: '',
            region: '',
            guardianEmail: '',
            guardianName: '',
            guardianPhone: '',
            branchInfo: null,
            termsAccepted: false,
            registerResult: null,
            registeredUser: null,

            password: '',
            verificationToken: '',

            goto: (step) =>
                set({ step, maxUnlockedStep: Math.max(get().maxUnlockedStep, indexOf(step)) }),
            completeStep: (step) => {
                const nextIdx = indexOf(step) + 1;
                const next = ONBOARDING_STEPS[Math.min(nextIdx, ONBOARDING_STEPS.length - 1)];
                set({
                    step: next,
                    maxUnlockedStep: Math.max(get().maxUnlockedStep, nextIdx),
                });
            },
            unlock: (step) =>
                set((s) => ({ maxUnlockedStep: Math.max(s.maxUnlockedStep, indexOf(step)) })),
            set: (patch) => set(patch),
            setBranchInfo: (info) => set({ branchInfo: info }),
            acceptTerms: () => set({ termsAccepted: true }),
            setRegisterResult: (res) =>
                set({
                    registerResult: {
                        vector_id: res.user.vector_id,
                        username: res.user.username,
                        full_name: res.user.full_name,
                        interests: res.interests,
                        play_styles: res.play_styles,
                        recommendations: res.recommendations,
                    },
                    registeredUser: res.user,
                }),
            reset: () =>
                set({
                    step: 'welcome',
                    maxUnlockedStep: 0,
                    ageRange: null,
                    interests: [],
                    playStyles: [],
                    fullName: '',
                    dob: '',
                    email: '',
                    phone: '',
                    username: '',
                    region: '',
                    guardianEmail: '',
                    guardianName: '',
                    guardianPhone: '',
                    branchInfo: null,
                    termsAccepted: false,
                    registerResult: null,
                    registeredUser: null,
                    password: '',
                    verificationToken: '',
                }),
        }),
        {
            name: 'vs-onboarding-progress',
            storage: createJSONSessionStorage(),
            partialize,
        }
    )
);

export function isStepReachable(step: OnboardingStepKey, maxUnlocked: number): boolean {
    return indexOf(step) <= maxUnlocked;
}

function createJSONSessionStorage() {
    return {
        getItem: (name: string) => {
            try {
                const raw = sessionStorage.getItem(name);
                return raw ? JSON.parse(raw) : null;
            } catch {
                return null;
            }
        },
        setItem: (name: string, value: unknown) => {
            sessionStorage.setItem(name, JSON.stringify(value));
        },
        removeItem: (name: string) => {
            sessionStorage.removeItem(name);
        },
    };
}

export function useLastRegisteredUser(): SessionUser | null {
    return null;
}