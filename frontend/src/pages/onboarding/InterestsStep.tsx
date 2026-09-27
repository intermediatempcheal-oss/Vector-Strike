import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingLayout from '../../components/OnboardingLayout';
import StepShell from '../../components/StepShell';
import Button from '../../components/Button';
import SelectionCard from '../../components/SelectionCard';
import { useOnboardingStore } from '../../store/onboarding';
import { OnboardingService } from '../../services/onboarding';
import { ApiRequestError } from '../../services/auth';
import { CatalogItem } from '../../types/onboarding';

const FALLBACK_INTERESTS: CatalogItem[] = [
    { slug: 'mathematics', label: 'Math', description: 'Numbers, patterns & proofs', icon: '∑', accent: '#8b5cf6', sort_order: 0 },
    { slug: 'science', label: 'Science', description: 'How the world works', icon: '◬', accent: '#38bdf8', sort_order: 1 },
    { slug: 'space', label: 'Space', description: 'Galaxies, rockets & stars', icon: '✶', accent: '#22d3ee', sort_order: 2 },
    { slug: 'coding', label: 'Coding', description: 'Logic & building with code', icon: '</>', accent: '#818cf8', sort_order: 3 },
    { slug: 'strategy', label: 'Strategy', description: 'Plan ahead, outsmart rivals', icon: '♞', accent: '#c084fc', sort_order: 4 },
    { slug: 'puzzles', label: 'Puzzles', description: 'Crack tricky challenges', icon: '◫', accent: '#60a5fa', sort_order: 5 },
];

export default function InterestsStep() {
    const navigate = useNavigate();
    const step = useOnboardingStore((s) => s.step);
    const set = useOnboardingStore((s) => s.set);
    const interests = useOnboardingStore((s) => s.interests);

    const [catalog, setCatalog] = useState<CatalogItem[]>(FALLBACK_INTERESTS);
    const [min, setMin] = useState(3);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let alive = true;
        OnboardingService.fetchConfig()
            .then((cfg) => {
                if (!alive) return;
                if (cfg.interests?.length) setCatalog(cfg.interests);
                setMin(cfg.min_interests ?? 3);
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
        const next = interests.includes(slug)
            ? interests.filter((i) => i !== slug)
            : [...interests, slug];
        set({ interests: next });
    };

    const canContinue = useMemo(() => interests.length >= min, [interests, min]);

    return (
        <OnboardingLayout step="interests">
            <StepShell
                eyebrow="STEP 3 · TRAIN YOUR BRAIN, YOUR WAY"
                title="What gets you excited?"
                subtitle={`Pick at least ${min} subjects — we’ll use these to recommend the right challenges.`}
                aside={
                    <div className="vs-hud">
                        <span className="vs-hud__pill">
                            {interests.length} selected
                            {min > interests.length ? ` · need ${min}` : ''}
                        </span>
                    </div>
                }
            >
                {error && <div className="vs-alert vs-alert--warn">{error}</div>}
                <div className="vs-chip-grid vs-chip-grid--interests">
                    {catalog.map((item) => (
                        <SelectionCard
                            key={item.slug}
                            kind="interest"
                            slug={item.slug}
                            title={item.label}
                            description={item.description}
                            accentColor={item.accent}
                            selected={interests.includes(item.slug)}
                            onClick={() => toggle(item.slug)}
                        />
                    ))}
                </div>
                <div className="vs-step__actions">
                    <Button
                        size="xl"
                        disabled={!canContinue}
                        onClick={() => navigate('/onboarding/play-style')}
                    >
                        Save my interests
                    </Button>
                </div>
            </StepShell>
        </OnboardingLayout>
    );
}