import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingLayout from '../../components/OnboardingLayout';
import StepShell from '../../components/StepShell';
import Button from '../../components/Button';
import SelectionCard from '../../components/SelectionCard';
import { useOnboardingStore } from '../../store/onboarding';
import { OnboardingService } from '../../services/onboarding';
import { ApiRequestError } from '../../services/auth';
import { CatalogItem } from '../../types/onboarding';

const FALLBACK_PLAY_STYLES: CatalogItem[] = [
    { slug: 'fast-competitive', label: 'Fast & competitive', description: 'Quick rounds, instant wins', icon: 'bolt', accent: '#f59e0b', sort_order: 0 },
    { slug: 'puzzle-solver', label: 'Puzzle solver', description: 'Savour every tricky layer', icon: 'puzzle', accent: '#22d3ee', sort_order: 1 },
    { slug: 'strategy', label: 'Strategic master', description: 'Think many moves ahead', icon: 'brain', accent: '#a855f7', sort_order: 2 },
    { slug: 'explore', label: 'Explorer', description: 'Wander and discover', icon: 'compass', accent: '#34d399', sort_order: 3 },
    { slug: 'challenge-myself', label: 'Personal best', description: 'Beat your own records', icon: 'target', accent: '#f472b6', sort_order: 4 },
    { slug: 'social', label: 'Team player', description: 'Play with friends', icon: 'users', accent: '#60a5fa', sort_order: 5 },
];

export default function PlayStyleStep() {
    const navigate = useNavigate();
    const step = useOnboardingStore((s) => s.step);
    const set = useOnboardingStore((s) => s.set);
    const playStyles = useOnboardingStore((s) => s.playStyles);
    const minLocal = 1;

    const [catalog, setCatalog] = useState<CatalogItem[]>(FALLBACK_PLAY_STYLES);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let alive = true;
        OnboardingService.fetchConfig()
            .then((cfg) => {
                if (!alive) return;
                if (cfg.play_styles?.length) setCatalog(cfg.play_styles);
            })
            .catch((err: unknown) => {
                if (!alive) return;
                if (err instanceof ApiRequestError) setError(err.message);
            });
        return () => {
            alive = false;
        };
    }, [step]);

    const toggle = (slug: string) => {
        const next = playStyles.includes(slug)
            ? playStyles.filter((i) => i !== slug)
            : [...playStyles, slug];
        set({ playStyles: next });
    };

    return (
        <OnboardingLayout step="play-style">
            <StepShell
                eyebrow="STEP 4 · HOW DO YOU LIKE TO PLAY?"
                title="Pick your style"
                subtitle="Choose one or more — this shapes your playlists and matchmaking preferences."
            >
                {error && <div className="vs-alert vs-alert--warn">{error}</div>}
                <div className="vs-chip-grid vs-chip-grid--styles">
                    {catalog.map((item) => (
                        <SelectionCard
                            key={item.slug}
                            kind="play-style"
                            slug={item.slug}
                            title={item.label}
                            description={item.description}
                            accentColor={item.accent}
                            selected={playStyles.includes(item.slug)}
                            onClick={() => toggle(item.slug)}
                        />
                    ))}
                </div>
                <div className="vs-step__actions">
                    <Button
                        size="xl"
                        disabled={playStyles.length < minLocal}
                        onClick={() => navigate('/onboarding/profile')}
                    >
                        Continue
                    </Button>
                </div>
            </StepShell>
        </OnboardingLayout>
    );
}