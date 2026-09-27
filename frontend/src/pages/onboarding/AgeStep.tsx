import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingLayout from '../../components/OnboardingLayout';
import StepShell from '../../components/StepShell';
import Button from '../../components/Button';
import AgeCard from '../../components/AgeCard';
import Icon, { IconName } from '../../components/Icon';
import { useOnboardingStore } from '../../store/onboarding';
import { OnboardingService } from '../../services/onboarding';
import { ApiRequestError } from '../../services/auth';
import { AgeRange } from '../../types/onboarding';

const DEFAULT_RANGES: AgeRange[] = [
    { value: 'younger', label: '12 and under' },
    { value: 'teens', label: '13 – 15' },
    { value: 'teen-plus', label: '16 – 17' },
    { value: 'adult', label: '18+' },
];

const RANGE_ICONS: Record<string, IconName> = {
    younger: 'gamepad',
    teens: 'rocket',
    'teen-plus': 'target',
    adult: 'users',
};

export default function AgeStep() {
    const navigate = useNavigate();
    const step = useOnboardingStore((s) => s.step);
    const set = useOnboardingStore((s) => s.set);
    const ageRange = useOnboardingStore((s) => s.ageRange);

    const [ranges, setRanges] = useState<AgeRange[]>(DEFAULT_RANGES);
    const [loadError, setLoadError] = useState<string | null>(null);

    useEffect(() => {
        OnboardingService.fetchConfig()
            .then((cfg) => setRanges(cfg.age_ranges))
            .catch((err: unknown) => {
                const msg =
                    err instanceof ApiRequestError
                        ? err.message
                        : 'We couldn’t load the age options right now.';
                setLoadError(msg);
            });
    }, [step]);

    return (
        <OnboardingLayout step="age">
            <StepShell
                eyebrow="STEP 2 · JUST SO WE GET IT RIGHT"
                title="How old are you?"
                subtitle="Your age shapes the challenges we unlock for you — and which parts of Vector Strike need a grown-up’s nod."
                aside={
                    <div className="vs-note vs-note--info">
                        <Icon name="shield" size={16} />
                        <p>
                            Vector Strike keeps age gates strictly. If you’re in a region that
                            requires parental permission, we’ll guide you through it in the next
                            steps.
                        </p>
                    </div>
                }
            >
                <div className="vs-age-grid">
                    {ranges.map((r) => (
                        <AgeCard
                            key={r.value}
                            label={r.label}
                            hint="Choose the range that’s true for you"
                            icon={RANGE_ICONS[r.value] ?? 'gamepad'}
                            selected={ageRange === r.value}
                            onClick={() => set({ ageRange: r.value })}
                        />
                    ))}
                </div>
                {loadError && <div className="vs-alert vs-alert--warn">{loadError}</div>}
                <div className="vs-step__actions">
                    <Button
                        size="xl"
                        disabled={!ageRange}
                        onClick={() => navigate('/onboarding/interests')}
                    >
                        Continue
                    </Button>
                </div>
            </StepShell>
        </OnboardingLayout>
    );
}