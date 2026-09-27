import { ReactNode, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../components/Button';
import Icon, { IconName } from '../components/Icon';
import HubChrome from '../components/hub/HubChrome';
import { useAuthStore } from '../store/auth';
import { fetchHome } from '../services/home';
import { ProfileProgress } from '../types/home';

interface SectionPageProps {
    title: string;
    subtitle: string;
    icon?: IconName;
    active?: 'home' | 'hub';
    children: ReactNode;
    action?: { label: string; onClick: () => void; variant?: 'primary' | 'outline' | 'ghost' };
}

export function SectionPage({ title, subtitle, icon = 'gamepad', active = 'hub', children, action }: SectionPageProps) {
    const navigate = useNavigate();
    const { user } = useAuthStore();
    const [profile, setProfile] = useState<ProfileProgress | null>(null);

    useEffect(() => {
        let cancelled = false;
        fetchHome()
            .then((feed) => {
                if (!cancelled) setProfile(feed.profile ?? null);
            })
            .catch(() => undefined)
            .finally(() => {
                if (!cancelled) {
                    // no-op; the page can still render with the authenticated user fallback
                }
            });
        return () => {
            cancelled = true;
        };
    }, []);

    const displayName = profile?.display_name || user?.full_name || user?.username || 'Pilot';

    return (
        <HubChrome
            active={active}
            profile={profile}
            user={user}
            displayName={displayName}
            search={
                <div className="vs-section-page__search" onClick={() => navigate('/game-hub')}>
                    <Icon name="search" size={16} className="vs-section-page__searchicon" />
                    <span>Search games</span>
                </div>
            }
        >
            <div className="vs-section-page">
                <header className="vs-section-page__header">
                    <div className="vs-section-page__titlewrap">
                        <span className="vs-section-page__eyebrow">
                            <Icon name={icon} size={15} />
                            VECTOR STRIKE
                        </span>
                        <h1>{title}</h1>
                        <p>{subtitle}</p>
                    </div>
                    {action && (
                        <Button size="lg" variant={action.variant ?? 'outline'} onClick={action.onClick}>
                            {action.label}
                        </Button>
                    )}
                </header>
                <div className="vs-section-page__content">{children}</div>
            </div>
        </HubChrome>
    );
}

export function MessagesPage() {
    return (
        <SectionPage title="Messages" subtitle="Your conversations, updates and team activity live here." icon="message" active="hub">
            <div className="vs-section-page__grid">
                <div className="vs-section-page__card vs-section-page__card--empty">
                    <Icon name="message" size={28} />
                    <h3>No conversations yet</h3>
                    <p>When a message arrives, it will appear here with the full conversation history and reply flow.</p>
                </div>
            </div>
        </SectionPage>
    );
}

export function NotificationsPage() {
    return (
        <SectionPage title="Notifications" subtitle="Achievement updates, events and account activity are collected here." icon="bell" active="hub">
            <div className="vs-section-page__grid">
                <div className="vs-section-page__card vs-section-page__card--empty">
                    <Icon name="bell" size={28} />
                    <h3>No notifications yet</h3>
                    <p>New achievements, challenge updates and security events will appear here once they are available.</p>
                </div>
            </div>
        </SectionPage>
    );
}

export function ProfilePage() {
    const { user } = useAuthStore();
    const [profile, setProfile] = useState<ProfileProgress | null>(null);

    useEffect(() => {
        fetchHome().then((feed) => setProfile(feed.profile ?? null)).catch(() => undefined);
    }, []);

    const displayName = profile?.display_name || user?.full_name || user?.username || 'Pilot';
    const vectorId = user?.vector_id ?? 'VS-UNKNOWN';

    return (
        <SectionPage title="Profile" subtitle="Your identity, progression and account snapshot." icon="user" active="home">
            <div className="vs-section-page__grid vs-section-page__grid--two">
                <div className="vs-section-page__card">
                    <div className="vs-section-page__profilehead">
                        <div className="vs-section-page__avatar">{displayName.slice(0, 2).toUpperCase()}</div>
                        <div>
                            <h3>{displayName}</h3>
                            <small>@{user?.username ?? 'pilot'}</small>
                        </div>
                    </div>
                    <div className="vs-section-page__meta">
                        <span>Vector ID</span>
                        <b>{vectorId}</b>
                    </div>
                    <div className="vs-section-page__meta">
                        <span>Level</span>
                        <b>{profile?.level ?? 1}</b>
                    </div>
                    <div className="vs-section-page__meta">
                        <span>XP</span>
                        <b>{profile?.xp ?? 0}</b>
                    </div>
                </div>
                <div className="vs-section-page__card">
                    <h3>Account status</h3>
                    <div className="vs-section-page__meta">
                        <span>Verification</span>
                        <b>{user?.verification_status ?? 'pending'}</b>
                    </div>
                    <div className="vs-section-page__meta">
                        <span>Account</span>
                        <b>{user?.account_status ?? 'active'}</b>
                    </div>
                    <div className="vs-section-page__meta">
                        <span>Region</span>
                        <b>{user?.region || 'Not set'}</b>
                    </div>
                </div>
            </div>
        </SectionPage>
    );
}

export function ProgressPage() {
    const [profile, setProfile] = useState<ProfileProgress | null>(null);

    useEffect(() => {
        fetchHome().then((feed) => setProfile(feed.profile ?? null)).catch(() => undefined);
    }, []);

    return (
        <SectionPage title="Progress" subtitle="Track your current progression, milestones, and category momentum." icon="check" active="home">
            <div className="vs-section-page__grid vs-section-page__grid--three">
                <div className="vs-section-page__stat">
                    <span>Level</span>
                    <b>{profile?.level ?? 1}</b>
                </div>
                <div className="vs-section-page__stat">
                    <span>XP</span>
                    <b>{profile?.xp ?? 0}</b>
                </div>
                <div className="vs-section-page__stat">
                    <span>XP to next level</span>
                    <b>{Math.max(0, (profile?.xp_for_next ?? 100) - (profile?.xp ?? 0))}</b>
                </div>
            </div>
        </SectionPage>
    );
}

export function ChallengesPage() {
    return (
        <SectionPage title="Challenges" subtitle="Live objectives and daily pressure runs." icon="target" active="hub">
            <div className="vs-section-page__grid">
                <div className="vs-section-page__card vs-section-page__card--empty">
                    <Icon name="target" size={28} />
                    <h3>No active challenge</h3>
                    <p>Daily challenge data is loaded from the backend when available. Check back for the next active run.</p>
                </div>
            </div>
        </SectionPage>
    );
}

export function LeaderboardsPage() {
    return (
        <SectionPage title="Leaderboards" subtitle="The current rank feed and category standings." icon="trophy" active="hub">
            <div className="vs-section-page__grid">
                <div className="vs-section-page__card vs-section-page__card--empty">
                    <Icon name="trophy" size={28} />
                    <h3>Rankings are loading</h3>
                    <p>Live leaderboard data will appear here once the backend ranking feed is active.</p>
                </div>
            </div>
        </SectionPage>
    );
}

export function TournamentsPage() {
    return (
        <SectionPage title="Tournaments" subtitle="Current brackets, qualifiers and upcoming entries." icon="medal" active="hub">
            <div className="vs-section-page__grid">
                <div className="vs-section-page__card vs-section-page__card--empty">
                    <Icon name="medal" size={28} />
                    <h3>No tournament is active</h3>
                    <p>Upcoming competition windows will appear here when they are opened by the backend.</p>
                </div>
            </div>
        </SectionPage>
    );
}

export function MissionsPage() {
    return (
        <SectionPage title="Missions" subtitle="Objectives, milestones and reward progress for your account." icon="check" active="hub">
            <div className="vs-section-page__grid">
                <div className="vs-section-page__card vs-section-page__card--empty">
                    <Icon name="check" size={28} />
                    <h3>No missions available</h3>
                    <p>Mission reward data appears here once your account has active backend tasks.</p>
                </div>
            </div>
        </SectionPage>
    );
}

export function AchievementsPage() {
    return (
        <SectionPage title="Achievements" subtitle="Your earned badges, milestones and stats history." icon="star" active="hub">
            <div className="vs-section-page__grid">
                <div className="vs-section-page__card vs-section-page__card--empty">
                    <Icon name="star" size={28} />
                    <h3>No achievements unlocked yet</h3>
                    <p>Badge progress will appear here as soon as the first qualifying runs are recorded.</p>
                </div>
            </div>
        </SectionPage>
    );
}

export function SocialPage() {
    return (
        <SectionPage title="Social" subtitle="Friends, squads, communities and player activity." icon="users" active="home">
            <div className="vs-section-page__grid">
                <div className="vs-section-page__card vs-section-page__card--empty">
                    <Icon name="users" size={28} />
                    <h3>Social feed is quiet</h3>
                    <p>When friends or squads are active, their activity and interactions will show here.</p>
                </div>
            </div>
        </SectionPage>
    );
}

export function PremiumPage() {
    return (
        <SectionPage title="Premium" subtitle="Your subscription status and premium access benefits." icon="rocket" active="home">
            <div className="vs-section-page__grid vs-section-page__grid--two">
                <div className="vs-section-page__card">
                    <h3>Standard</h3>
                    <p>Base access to the Vector Strike platform and daily challenges.</p>
                </div>
                <div className="vs-section-page__card">
                    <h3>Premium</h3>
                    <p>Premium features become available after real backend verification and entitlement setup.</p>
                </div>
            </div>
        </SectionPage>
    );
}

export function SettingsPage() {
    return (
        <SectionPage title="Settings" subtitle="Account, privacy, accessibility and gameplay preferences." icon="settings" active="home">
            <div className="vs-section-page__grid">
                <div className="vs-section-page__card">
                    <h3>Account settings</h3>
                    <p>Security, notifications and profile preferences are managed here once the backend settings endpoints are connected.</p>
                </div>
            </div>
        </SectionPage>
    );
}

export function AccountPage() {
    return (
        <SectionPage title="Account" subtitle="Manage your identity, security and access controls." icon="shield" active="home">
            <div className="vs-section-page__grid">
                <div className="vs-section-page__card">
                    <h3>Account controls</h3>
                    <p>Use server-backed account management to update security preferences and data access settings.</p>
                </div>
            </div>
        </SectionPage>
    );
}
