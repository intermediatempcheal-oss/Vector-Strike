import { useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import HubChrome from '../components/hub/HubChrome';
import Button from '../components/Button';
import Icon from '../components/Icon';
import { fetchGameDetail } from '../services/hub';
import { GameDetail } from '../types/hub';
import { useAuthStore } from '../store/auth';
import type { HomeFeed } from '../types/home';
import { fetchHome } from '../services/home';
import {
    EmptyState,
    GameCardView,
    SectionHead,
    Stars,
    formatDate,
    formatDuration,
    formatPlaytime,
} from '../components/hub/HubBits';
import { PLAY_KIND_ICONS } from '../components/hub/runtimes';
import { cn } from '../utils/cn';

export default function GameDetailPage() {
    const { slug } = useParams<{ slug: string }>();
    const navigate = useNavigate();
    const { user } = useAuthStore();

    const [detail, setDetail] = useState<GameDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [profile, setProfile] = useState<HomeFeed['profile']>(null);

    useEffect(() => {
        let cancelled = false;
        if (!slug) return;
        setLoading(true);
        setError('');
        fetchGameDetail(slug)
            .then((d) => {
                if (!cancelled) setDetail(d);
            })
            .catch((err) => {
                if (!cancelled) setError(err instanceof Error ? err.message : 'Could not load this game.');
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });
        fetchHome()
            .then((feed) => {
                if (!cancelled) setProfile(feed.profile);
            })
            .catch(() => undefined);
        return () => {
            cancelled = true;
        };
    }, [slug]);

    const displayName = profile?.display_name || user?.full_name || user?.username || 'Pilot';

    return (
        <HubChrome
            active="hub"
            profile={profile}
            user={user}
            displayName={displayName}
            search={<div className="vs-hub__searchspacer" />}
        >
            <div className="vs-game">
                {loading && <GameDetailSkeleton />}

                {error && !loading && (
                    <EmptyState
                        icon="alert"
                        title="We couldn’t load this game."
                        body="It may have been pulled from the hub or there’s a network hiccup."
                        action={{ label: 'Back to hub', onClick: () => navigate('/game-hub') }}
                    />
                )}

                {!loading && !error && detail && (
                    <>
                        <section className={cn('vs-game__hero')} style={{ ['--cat-accent' as string]: detail.category.accent }}>
                            <div className="vs-game__herogrid">
                                <div className="vs-game__art">
                                    <span
                                        className="vs-game__artbadge"
                                        style={{ ['--cat-accent' as string]: detail.category.accent }}
                                    >
                                        <Icon name={kindIcon(detail.play_kind ?? '')} size={30} />
                                    </span>
                                    <img src={detail.banner} alt="" loading="lazy" />
                                </div>

                                <div className="vs-game__head">
                                    <div className="vs-game__chips">
                                        <span
                                            className="vs-game__cat"
                                            style={{ ['--cat-accent' as string]: detail.category.accent }}
                                        >
                                            <Icon name={detail.category.icon as never} size={14} />
                                            {detail.category.label}
                                        </span>
                                        {detail.is_new && (
                                            <span className="vs-game__tag vs-game__tag--new">
                                                <Icon name="sparkles" size={13} /> New
                                            </span>
                                        )}
                                        {detail.is_featured && (
                                            <span className="vs-game__tag">
                                                <Icon name="flame" size={13} /> Featured
                                            </span>
                                        )}
                                        <span className="vs-game__tag">{detail.game_type.replace(/-/g, ' ')}</span>
                                        {detail.content_rating && <span className="vs-game__tag">{detail.content_rating}</span>}
                                    </div>

                                    <h1>{detail.title}</h1>
                                    <p className="vs-game__tagline">{detail.tagline}</p>
                                    <p className="vs-game__desc">{detail.description}</p>

                                    <div className="vs-game__metas">
                                        <Meta label="Difficulty" value={detail.difficulty_label} icon="target">
                                            <Stars stars={detail.difficulty_stars} />
                                        </Meta>
                                        <Meta label="Play kind" value={playKindLabel(detail.play_kind ?? '')} icon="gamepad" />
                                        <Meta label="Average run" value={formatDuration(detail.duration_minutes)} icon="clock" />
                                        <Meta label="Age range" value={`${detail.minimum_age}–${detail.maximum_age}`} icon="users" />
                                        {detail.release_date && (
                                            <Meta label="Added" value={formatDate(detail.release_date)} icon="calendar" />
                                        )}
                                    </div>

                                    <div className="vs-game__cta">
                                        <Button size="xl" icon="play" onClick={() => navigate(`/games/${detail.slug}/play`)}>
                                            Play now
                                        </Button>
                                        {detail.play_count > 0 && (
                                            <Button
                                                size="xl"
                                                variant="outline"
                                                icon="rotate"
                                                onClick={() => navigate(`/games/${detail.slug}/play`)}
                                            >
                                                Replay
                                            </Button>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </section>

                        <div className="vs-game__body">
                            <section className="vs-game__panel">
                                <SectionHead title="How to play" icon="book" />
                                <div className="vs-game__howto">
                                    <div className="vs-game__inst">
                                        <h3>Objective</h3>
                                        <p>{detail.instructions}</p>
                                    </div>
                                    {detail.controls && (
                                        <div className="vs-game__inst">
                                            <h3>Controls</h3>
                                            <p>{detail.controls}</p>
                                        </div>
                                    )}
                                </div>
                            </section>

                            <section className="vs-game__panel vs-game__progresspanel">
                                <SectionHead title="Your progress" icon="chart" />
                                {detail.play_count === 0 ? (
                                    <div className="vs-game__fresh">
                                        <Icon name="sparkles" size={22} />
                                        <p>You haven’t run this game yet. First run counts towards your progress.</p>
                                    </div>
                                ) : (
                                    <ProgressGrid detail={detail} />
                                )}
                            </section>

                            {detail.related_games.length > 0 && (
                                <>
                                    <SectionHead title="More like this" icon="layers" subtitle="Same family, same feel." />
                                    <div className="vs-hub__scroller">
                                        {detail.related_games.map((g) => (
                                            <GameCardView key={g.slug} game={g} />
                                        ))}
                                    </div>
                                </>
                            )}
                        </div>
                    </>
                )}
            </div>
        </HubChrome>
    );
}

function Meta({
    label,
    value,
    icon,
    children,
}: {
    label: string;
    value: string;
    icon: Parameters<typeof Icon>[0]['name'];
    children?: ReactNode;
}) {
    return (
        <div className="vs-game__meta-item">
            <span className="vs-game__metaicon">
                <Icon name={icon} size={16} />
            </span>
            <small>{label}</small>
            {children ?? <b>{value}</b>}
        </div>
    );
}

function ProgressGrid({ detail }: { detail: GameDetail }) {
    const completion = Number(detail.progress?.completion_percentage ?? 0) || 0;
    const bar = Math.max(0, Math.min(100, completion));
    return (
        <div className="vs-game__stats">
            <Stat label="Runs" value={detail.play_count} />
            <Stat label="Best score" value={detail.best_score > 0 ? detail.best_score : '—'} />
            <Stat label="Best accuracy" value={detail.best_score > 0 ? `${detail.best_accuracy}%` : '—'} />
            <Stat label="Highest level" value={`L${detail.best_level}`} />
            <div className="vs-game__stage">
                <div className="vs-game__stagerow">
                    <span>Stage progress</span>
                    <b>{completion}%</b>
                </div>
                <div className="vs-game__stagebar">
                    <div className="vs-game__stagefill" style={{ width: `${bar}%` }} />
                </div>
            </div>
            {detail.last_result && (
                <div className="vs-game__lastrun">
                    <span className="vs-game__lastrunic">
                        <Icon name={detail.last_result.status === 'completed' ? 'trophy' : 'target'} size={14} />
                    </span>
                    Best run {formatDate(detail.last_result.started_at)}
                    <em>
                        {detail.last_result.score} pts · {detail.last_result.accuracy}% ·{' '}
                        {formatPlaytime(detail.last_result.duration_seconds)}
                    </em>
                </div>
            )}
        </div>
    );
}

function Stat({ label, value }: { label: string; value: string | number }) {
    return (
        <div className="vs-game__stat">
            <b>{value}</b>
            <small>{label}</small>
        </div>
    );
}

function GameDetailSkeleton() {
    return (
        <div className="vs-game">
            <section className="vs-game__hero">
                <div className="vs-game__herogrid">
                    <div className="vs-game__art vs-game__art--skel" />
                    <div className="vs-game__head">
<div className="vs-game__chips">
                        <div className="vs-skeleton vs-skeleton--pill" />
                        <div className="vs-skeleton vs-skeleton--pill" />
                    </div>
                        <div className="vs-skeleton vs-skeleton--block vs-game__skeletitle" />
                        <div className="vs-skeleton vs-skeleton--block vs-game__skeletag" />
                    </div>
                </div>
            </section>
            <div className="vs-game__body">
                <div className="vs-skeleton vs-skeleton--block vs-game__skeletonpanel" />
            </div>
        </div>
    );
}

function kindIcon(kind: string) {
    return (PLAY_KIND_ICONS[kind] as never) ?? 'gamepad';
}

function playKindLabel(kind: string) {
    const map: Record<string, string> = {
        'quanta-calc': 'Quanta calc',
        'logix-seq': 'Logix sequence',
        'pulse-timing': 'Pulse timing',
        'vector-dodge': 'Vector dodge',
        'cipher-sort': 'Cipher sort',
        'synapse-match': 'Synapse match',
        'forge-order': 'Forge order',
        'orbit-gather': 'Orbit gather',
    };
    return map[kind] ?? kind;
}