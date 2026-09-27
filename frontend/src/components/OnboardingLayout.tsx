import { ReactNode } from 'react';
import Icon from './Icon';
import Logo from './Logo';
import ProgressBar from './ProgressBar';
import { OnboardingStepKey } from '../constants/onboarding';

interface OnboardingLayoutProps {
    step: OnboardingStepKey;
    children: ReactNode;
    footer?: ReactNode;
    showProgress?: boolean;
    leftWeight?: number;
    onBack?: () => void;
    backLabel?: string;
}

export default function OnboardingLayout({
    step,
    children,
    footer,
    showProgress = true,
    onBack,
    backLabel = 'Back',
}: OnboardingLayoutProps) {
    return (
        <div className="vs-onboarding">
            <div className="vs-onboarding__bg" />
            <div className="vs-onboarding__grid" />
            <div className="vs-onboarding__frame">
                <header className="vs-onboarding__head">
                    {onBack ? (
                        <button type="button" className="vs-back-link vs-back-link--header" onClick={onBack}>
                            <Icon name="chevron-left" size={15} />
                            {backLabel}
                        </button>
                    ) : (
                        <div className="vs-back-link__spacer" aria-hidden />
                    )}
                    <Logo size="sm" />
                    {showProgress && <ProgressBar step={step} />}
                </header>

                <main className="vs-onboarding__main">{children}</main>

                {footer && <footer className="vs-onboarding__foot">{footer}</footer>}
            </div>
        </div>
    );
}