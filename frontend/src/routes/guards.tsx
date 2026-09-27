import { ReactNode } from 'react';
import { Navigate, useParams } from 'react-router-dom';
import { useOnboardingStore } from '../store/onboarding';
import { ONBOARDING_STEPS, OnboardingStepKey } from '../constants/onboarding';
import { useAuthStore } from '../store/auth';

function requiredDataFor(step: OnboardingStepKey): boolean {
    const s = useOnboardingStore.getState();
    switch (step) {
        case 'welcome':
            return true;
        case 'age':
            return true;
        case 'interests':
            return Boolean(s.ageRange);
        case 'play-style':
            return s.interests.length > 0;
        case 'profile':
            return s.playStyles.length > 0;
        case 'guardian':
            return (
                s.branchInfo?.branch === 'guardian' &&
                Boolean(s.dob) &&
                Boolean(s.username)
            );
        case 'verification':
            return (
                s.branchInfo?.branch === 'verification' &&
                Boolean(s.dob) &&
                Boolean(s.username)
            );
        case 'terms':
            return (
                Boolean(s.dob) &&
                Boolean(s.branchInfo) &&
                (s.branchInfo!.branch === 'none' ||
                    s.branchInfo!.branch === 'guardian' ||
                    s.branchInfo!.branch === 'verification') &&
                (s.branchInfo!.branch !== 'guardian' || Boolean(s.guardianEmail)) &&
                (s.branchInfo!.branch !== 'verification' || Boolean(s.verificationToken))
            );
        case 'creating':
            return s.termsAccepted && Boolean(s.registerResult);
        case 'complete':
            return Boolean(s.registerResult);
        default:
            return false;
    }
}

export function OnboardingGuard({ children }: { children: ReactNode }) {
    const { step } = useParams<{ step: string }>();

    if (!step || !(ONBOARDING_STEPS as string[]).includes(step)) {
        return <Navigate to="/onboarding/welcome" replace />;
    }

    const target = step as OnboardingStepKey;
    const targetIdx = ONBOARDING_STEPS.indexOf(target);
    const firstInvalidIdx = ONBOARDING_STEPS.slice(0, targetIdx + 1).findIndex(
        (s) => !requiredDataFor(s)
    );

    if (firstInvalidIdx !== -1 && firstInvalidIdx < targetIdx) {
        return <Navigate to={`/onboarding/${ONBOARDING_STEPS[firstInvalidIdx]}`} replace />;
    }

    if (!requiredDataFor(target)) {
        return <Navigate to="/onboarding/welcome" replace />;
    }

    return <>{children}</>;
}

export function RequireAuth({ children }: { children: ReactNode }) {
    const { authenticated, onboarding_complete, initialized } = useAuthStore();
    if (!initialized) {
        return (
            <div className="vs-booting">
                <div className="vs-booting__spinner" />
                <span>Loading your session…</span>
            </div>
        );
    }
    if (!authenticated) return <Navigate to="/login" replace />;
    if (!onboarding_complete) return <Navigate to="/onboarding/welcome" replace />;
    return <>{children}</>;
}