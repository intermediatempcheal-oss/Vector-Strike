import { cn } from '../utils/cn';
import { progressIndex, STEP_LABELS, TOTAL_PROGRESS_STEPS, OnboardingStepKey } from '../constants/onboarding';

interface ProgressBarProps {
    step: OnboardingStepKey;
    className?: string;
}

export default function ProgressBar({ step, className }: ProgressBarProps) {
    const current = progressIndex(step);
    const pct = TOTAL_PROGRESS_STEPS === 1 ? 100 : (current / (TOTAL_PROGRESS_STEPS - 1)) * 100;

    return (
        <div className={cn('vs-progress', className)} aria-label="Onboarding progress">
            <div className="vs-progress__label">
                <span className="vs-progress__step">
                    Step {current + 1} of {TOTAL_PROGRESS_STEPS}
                </span>
                <span className="vs-progress__name">{STEP_LABELS[step] ?? ''}</span>
            </div>
            <div className="vs-progress__track">
                <div className="vs-progress__fill" style={{ width: `${Math.max(4, pct)}%` }} />
            </div>
        </div>
    );
}