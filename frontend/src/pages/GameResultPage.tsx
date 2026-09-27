import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { useLocation, useNavigate, useParams } from 'react-router-dom';
import HubChrome from '../components/hub/HubChrome';
import Button from '../components/Button';
import Icon from '../components/Icon';
import { GameDetail, GameSessionState, RunReport } from '../types/hub';
import type { ProfileProgress } from '../types/home';
import { useAuthStore } from '../store/auth';
import { fetchHome } from '../services/home';
import { GameCardView, formatDuration, formatPlaytime, SectionHead } from '../components/hub/HubBits';
import { cn } from '../utils/cn';

interface ResultState {
    detail: GameDetail;
    result: GameSessionState | null;
    report: RunReport;
    error?: string;
}

export default function GameResultPage() {
    const { slug } = useParams<{ slug: string }>();
    const navigate = useNavigate();
    const location = useLocation();
    const { user } = useAuthStore();
    const state = (location.state ?? null) as ResultState | null;

const [profile, setProfile] = useState<ProfileProgress | null>(null);
    const [recommended, setRecommended] = useState<GameDetail['related_games']>([]);

    useEffect(() => {
        if (!state) return;
        fetchHome()
            .then((feed) => {
                setProfile(feed.profile);
                const next = feed.recommendations.find((g) => g.slug !== slug);
                if (next) setRecommended([next]);
            })
            .catch(() => undefined);
    }, [state, slug]);

    if (!state || !slug) {
        return <RedirectToDetail slug={slug} />;
    }

    const { detail, result, report } = state;
    const won = report.outcome === 'completed';
    const displayName = profile?.display_name || user?.full_name || user?.username || 'Pilot';

    const accuracy = Math.max(0, Math.min(100, report.accuracy));
    const accLabel = accuracy >= 80 ? 'Sharp' : accuracy >= 50 ? 'Steady' : 'Rough';
    const profileDelta = result ? { xp: result.xp_earned, progress: Math.round(result.level_reached / 8 * 100) } : null;

    return (
        <HubChrome
            active="hub"
            profile={profile}
            user={user}
            displayName={displayName}
            search={<div className="vs-hub__searchspacer" />}
        >
            <div className="vs-result">
                <section className={cn('vs-result__hero', won ? 'vs-result__hero--win' : 'vs-result__hero--loss')}>
                    <span className="vs-result__badge">
                        <Icon name={won ? 'trophy' : 'target'} size={20} />
                        {won ? 'RUN COMPLETE' : 'RUN ENDED'}
                    </span>
                    <h1>{won ? 'Clean run.' : 'The run stopped here.'}</h1>
                    <p>
                        {detail.title} · {detail.category.label}
                    </p>
                    <div className="vs-result__avatars">
                        <span className="vs-result__rankchip">
                            Level {profile?.level ?? 1} · {profile?.rank ?? 'Rookie'}
                        </span>
                    </div>
                </section>

                {state.error && result === null && (
                    <div className="vs-result__warn">
                        <Icon name="alert" size={16} />
                        Your result couldn’t be saved to the server ({state.error}). Your progress shown here is from
                        this device only.
                    </div>
                )}

                <section className="vs-result__stats">
                    <Stat value={report.score} label="Score" icon="chart" />
                    <Stat value={`${accuracy}%`} label={`Accuracy · ${accLabel}`} icon="target" />
                    <Stat value={formatPlaytime(report.duration_seconds)} label="Time" icon="clock" />
                    <Stat value={`L${report.level_reached}`} label="Level reached" icon="layers" />
                    <Stat value={result ? result.xp_earned : 0} label="XP earned" icon="bolt" highlight={won} />
                </section>

                <section className="vs-result__summary">
                    <div className="vs-result__summarygrid">
                        <SummaryRow label="Best score">
                            {detail.best_score > 0 ? detail.best_score : '—'}
                        </SummaryRow>
                        <SummaryRow label="Best accuracy">
                            {detail.best_score > 0 ? `${detail.best_accuracy}%` : '—'}
                        </SummaryRow>
                        <SummaryRow label="Runs played">
                            {detail.play_count + (result ? 1 : 0)}
                        </SummaryRow>
                        <SummaryRow label="Stage progress">
                            {profileDelta ? `${profileDelta.progress}%` : `${Math.round(report.level_reached / 8 * 100)}%`}
                        </SummaryRow>
                    </div>
                </section>

                <section className="vs-result__actions">
                    <Button size="lg" icon="rotate" onClick={() => navigate(`/games/${detail.slug}/play`, { replace: true })}>
                        Replay
                    </Button>
                    <Button size="lg" variant="outline" icon="play" onClick={() => navigate(`/games/${detail.slug}/play`, { replace: true })}>
                        Next run
                    </Button>
                    <Button size="lg" variant="ghost" icon="layers" onClick={() => navigate('/game-hub')}>
                        Back to hub
                    </Button>
                </section>

                {recommended.length > 0 && (
                    <>
                        <SectionHead title="Recommended next" icon="sparkles" subtitle="Based on what you just played." />
                        <div className="vs-hub__scroller">
                            {recommended.map((g) => (
                                <GameCardView key={g.slug} game={g} />
                            ))}
                            {detail.related_games.slice(0, Math.max(0, 4 - recommended.length)).map((g) => (
                                <GameCardView key={g.slug} game={g} />
                            ))}
                        </div>
                    </>
                )}

                <div className="vs-result__foot">
                    <span>{detail.title} · {formatDuration(detail.duration_minutes)} run</span>
                </div>
            </div>
        </HubChrome>
    );
}

function RedirectToDetail({ slug }: { slug?: string }) {
    const navigate = useNavigate();
    useEffect(() => {
        if (slug) navigate(`/games/${slug}`, { replace: true });
        else navigate('/game-hub', { replace: true });
    }, [slug, navigate]);
    return null;
}

function Stat({ value, label, icon, highlight }: { value: string | number; label: string; icon: 'chart' | 'target' | 'clock' | 'layers' | 'bolt'; highlight?: boolean }) {
    return (
        <div className={cn('vs-result__stat', highlight && 'vs-result__stat--win')}>
            <span className="vs-result__staticon">
                <Icon name={icon} size={18} />
            </span>
            <b>{value}</b>
            <small>{label}</small>
        </div>
    );
}

function SummaryRow({ label, children }: { label: string; children: ReactNode }) {
    return (
        <div className="vs-result__row">
            <span>{label}</span>
            <b>{children}</b>
        </div>
    );
}
