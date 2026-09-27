import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppChrome from '../components/hub/AppChrome';
import { Avatar, EmptyState, SectionHead, formatRank, formatSkill } from '../components/hub/HubBits';
import Button from '../components/Button';
import Icon from '../components/Icon';
import { useAppStore } from '../store/app';
import { useAuthStore } from '../store/auth';

export default function ProfilePage() {
    const navigate = useNavigate();
    const { user } = useAuthStore();
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
    const displayName = profile?.display_name || user?.full_name || user?.username || 'Pilot';

    return (
        <AppChrome active="profile">
            <main className="vs-hub__main">
                <SectionHead icon="user" title="Profile" subtitle="Your identity, verified by the backend." />
                {loading && !feed ? (
                    <div className="vs-page-skel">
                        <div className="vs-page-skel__item" />
                        <div className="vs-page-skel__item" />
                    </div>
                ) : !feed ? (
                    <EmptyState
                        icon="alert"
                        title="Couldn't load your profile"
                        body="Something went wrong while loading your profile."
                        action={{ label: 'Retry', onClick: () => setRetry((r) => r + 1) }}
                    />
                ) : (
                    <>
                        <section className="vs-profile">
                            <div className="vs-profile__head">
                                <Avatar profile={profile} name={displayName} size="xl" />
                                <div className="vs-profile__identity">
                                    <div className="vs-profile__title">
                                        <h1>{displayName}</h1>
                                        {user?.verification_status === 'verified' || user?.age_verified ? (
                                            <span className="vs-badge vs-badge--verified">Verified</span>
                                        ) : null}
                                    </div>
                                    <p>
                                        @{user?.username ?? ''} · <span className="vs-profile__id">{user?.vector_id ?? ''}</span>
                                    </p>
                                    <div className="vs-profile__chips">
                                        <span className="vs-chip">
                                            <Icon name="star" size={14} /> Level {profile?.level ?? 1}
                                        </span>
                                        <span className="vs-chip">
                                            <Icon name="trophy" size={14} /> {formatRank(profile?.rank)}
                                        </span>
                                        <span className="vs-chip">
                                            <Icon name="bolt" size={14} /> {profile?.xp ?? 0} XP
                                        </span>
                                        <span className="vs-chip">
                                            <Icon name="compass" size={14} /> {formatSkill(profile?.skill_level)}
                                        </span>
                                    </div>
                                    <div className="vs-hub__bar vs-hub__bar--lg vs-profile__xp">
                                        <div className="vs-hub__barfill" style={{ width: `${profile?.xp_progress ?? 0}%` }} />
                                    </div>
                                    <small className="vs-profile__xphint">
                                        {profile ? `${profile.xp} / ${profile.xp_for_next} XP to Level ${profile.level + 1}` : ''}
                                    </small>
                                </div>
                            </div>

                            {stats ? (
                                <div className="vs-profile__stats">
                                    <ProfileStat label="Games played" value={stats.games_played} icon="gamepad" />
                                    <ProfileStat label="Categories" value={stats.categories_played} icon="layers" />
                                    <ProfileStat label="Game XP" value={stats.total_game_xp} icon="bolt" />
                                </div>
                            ) : null}

                            <div className="vs-profile__details">
                                <DetailRow label="Username" value={user?.username ?? '—'} />
                                <DetailRow label="Email" value={user?.email ?? '—'} />
                                <DetailRow label="Phone" value={user?.phone ?? '—'} />
                                <DetailRow label="Region" value={user?.region ? user.region.toUpperCase() : '—'} />
                                <DetailRow label="Age group" value={user?.age_group || '—'} />
                                <DetailRow label="Verification" value={profile ? (user?.verification_status ?? 'pending') : '—'} />
                            </div>

                            <div className="vs-profile__actions">
                                <Button variant="outline" size="md" icon="check" onClick={() => navigate('/progress')}>
                                    View progress
                                </Button>
                                <Button variant="ghost" size="md" icon="settings" onClick={() => navigate('/settings')}>
                                    Settings
                                </Button>
                            </div>
                        </section>
                    </>
                )}
            </main>
        </AppChrome>
    );
}

function ProfileStat({ label, value, icon }: { label: string; value: number; icon: 'gamepad' | 'layers' | 'bolt' }) {
    return (
        <div className="vs-profile__stat">
            <Icon name={icon} size={18} />
            <b>{value}</b>
            <span>{label}</span>
        </div>
    );
}

function DetailRow({ label, value }: { label: string; value: string }) {
    return (
        <div className="vs-profile__drow">
            <span>{label}</span>
            <b>{value}</b>
        </div>
    );
}