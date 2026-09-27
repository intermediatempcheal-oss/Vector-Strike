import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import OnboardingLayout from '../../components/OnboardingLayout';
import StepShell from '../../components/StepShell';
import Icon, { IconName } from '../../components/Icon';

const STAGES: Array<{ icon: IconName; label: string; ms: number }> = [
    { icon: 'shield', label: 'Validating your identity details…', ms: 900 },
    { icon: 'sparkles', label: 'Generating your unique Vector ID…', ms: 1100 },
    { icon: 'target', label: 'Building your challenge playlists…', ms: 1200 },
    { icon: 'rocket', label: 'Opening the gates…', ms: 800 },
];

export default function CreatingStep() {
    const navigate = useNavigate();
    const [stage, setStage] = useState(0);

    useEffect(() => {
        let current = 0;
        let timer: ReturnType<typeof setTimeout>;
        const advance = () => {
            if (current >= STAGES.length) {
                navigate('/onboarding/complete', { replace: true });
                return;
            }
            setStage(current);
            timer = setTimeout(() => {
                current += 1;
                advance();
            }, STAGES[current].ms);
        };
        advance();
        return () => clearTimeout(timer);
    }, [navigate]);

    const total = STAGES.reduce((acc, s) => acc + s.ms, 0);
    const elapsedMs = STAGES.slice(0, stage).reduce((acc, s) => acc + s.ms, 0);
    const pct = Math.min(100, Math.round((elapsedMs / total) * 100));

    const current = STAGES[stage] ?? STAGES[STAGES.length - 1];

    return (
        <OnboardingLayout step="creating" showProgress={false}>
            <StepShell
                eyebrow="ONE MOMENT PLEASE"
                title="Opening up your arcade…"
                subtitle="We’re putting the finishing touches on your Vector Strike identity and playlists."
            >
                <div className="vs-creating">
                    <div className="vs-creating__artifact" key={stage}>
                        <Icon name={current.icon} size={56} />
                    </div>
                    <div className="vs-creating__stages">
                        {STAGES.map((s, i) => (
                            <div
                                key={s.label}
                                className="vs-creating__stage"
                                data-active={i === stage}
                                data-done={i < stage}
                            >
                                <span className="vs-creating__dot">
                                    {i < stage ? <Icon name="check" size={12} /> : i}
                                </span>
                                <span>{s.label}</span>
                            </div>
                        ))}
                    </div>
                    <div className="vs-creating__bar">
                        <div className="vs-creating__fill" style={{ width: `${Math.max(4, pct)}%` }} />
                    </div>
                </div>
            </StepShell>
        </OnboardingLayout>
    );
}