import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppChrome from '../components/hub/AppChrome';
import { EmptyState, GameCardView, SectionHead } from '../components/hub/HubBits';
import { useAppStore } from '../store/app';

export default function ProgressPage() {
    const navigate = useNavigate();
    const feed = useAppStore((s) => s.feed);
    const loading = useAppStore((s) => s.loading);
    const [retry, setRetry] = useState(0);

    useEffect(() => {
        if (!useAppStore.getState().feed) {
            void useAppStore.getState().ensure().catch(() => undefined);
        }
    }, [retry]);

    const profile = feed?.profile ?? null;
    const stats = feed?.stats;

    return (
        <AppChrome active="progress">
            <main className="vs-hub__main">
                <SectionHead icon="check" title="Your Progress" subtitle="Every number comes from your verified backend runs." />
                {loading && !feed ? (
                    <div className="vs-page-skel">
                        <div className="vs-page-skel__item" />
                        <div className="vs-page-skel__item" />
                    </div>
                ) : !feed ? (
                    <EmptyState
                        icon="alert"
                        title="Couldn't load your progress"
                        body="Something went wrong while loading your progress."
                        action={{ label: 'Retry', onClick: () => setRetry((r) => r + 1) }}
                    />
                ) : (
                    <>
                        <section className="vs-progress">
                            <div className="vs-progress__cards">
                                <div className="vs-progress__card">
                                    <span className="vs-progress__label">Level</span>
                                    <b>{profile?.level ?? 1}</b>
                                </div>
                                <div className="vs-progress__card">
                                    <span className="vs-progress__label">Total XP</span>
                                    <b>{profile?.xp ?? 0}</b>
                                </div>
                                <div className="vs-progress__card">
                                    <span className="vs-progress__label">Games played</span>
                                    <b>{stats?.games_played ?? 0}</b>
                                </div>
                                <div className="vs-progress__card">
                                    <span className="vs-progress__label">Categories</span>
                                    <b>{stats?.categories_played ?? 0}</b>
                                </div>
                            </div>
                            <div className="vs-hub__bar vs-hub__bar--lg vs-progress__bar">
                                <div className="vs-hub__barfill" style={{ width: `${profile?.xp_progress ?? 0}%` }} />
                            </div>
                            <small className="vs-progress__hint">
                                {profile ? `${profile.xp_for_next - profile.xp} XP to Level ${profile.level + 1}` : 'Play games to start earning XP.'}
                            </small>
                        </section>

                        {feed.continue_playing.length > 0 ? (
                            <>
                                <SectionHead icon="play" title="In progress" subtitle="Continue a run or open a fresh challenge." />
                                <div className="vs-hub__grid">
                                    {feed.continue_playing.map((g) => (
                                        <GameCardView key={g.slug} game={g} />
                                    ))}
                                </div>
                            </>
                        ) : (
                            <EmptyState
                                icon="play"
                                title="Nothing in progress yet"
                                body="Open the Game Hub and start your first real run."
                                action={{ label: 'Open game hub', onClick: () => navigate('/game-hub') }}
                            />
                        )}
                    </>
                )}
            </main>
        </AppChrome>
    );
}