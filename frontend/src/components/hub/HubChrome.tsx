import { ReactNode, useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { cn } from '../../utils/cn';
import Logo from '../Logo';
import Icon, { IconName } from '../Icon';
import Button from '../Button';
import { useAuthStore } from '../../store/auth';
import { ProfileProgress } from '../../types/home';
import { SessionUser } from '../../types/auth';
import { Avatar, formatRank } from './HubBits';

export type NavTarget =
    | 'home'
    | 'game-hub'
    | 'challenges'
    | 'leaderboards'
    | 'tournaments'
    | 'missions'
    | 'achievements'
    | 'social'
    | 'messages'
    | 'notifications'
    | 'profile'
    | 'progress'
    | 'premium'
    | 'settings'
    | 'account';

const ROUTES: Record<NavTarget, string> = {
    home: '/home',
    'game-hub': '/game-hub',
    challenges: '/challenges',
    leaderboards: '/leaderboards',
    tournaments: '/tournaments',
    missions: '/missions',
    achievements: '/achievements',
    social: '/social',
    messages: '/messages',
    notifications: '/notifications',
    profile: '/profile',
    progress: '/progress',
    premium: '/premium',
    settings: '/settings',
    account: '/account',
};

interface NavItem {
    key: NavTarget;
    label: string;
    icon: IconName;
    soon?: boolean;
}

const SIDE_NAV: NavItem[] = [
    { key: 'home', label: 'Home', icon: 'home' },
    { key: 'game-hub', label: 'Game Hub', icon: 'gamepad' },
    { key: 'challenges', label: 'Challenges', icon: 'target' },
    { key: 'leaderboards', label: 'Leaderboards', icon: 'trophy' },
    { key: 'tournaments', label: 'Tournaments', icon: 'medal' },
    { key: 'missions', label: 'Missions', icon: 'check' },
    { key: 'achievements', label: 'Achievements', icon: 'star' },
    { key: 'social', label: 'Social', icon: 'users' },
    { key: 'messages', label: 'Messages', icon: 'message' },
    { key: 'notifications', label: 'Notifications', icon: 'bell' },
    { key: 'profile', label: 'Profile', icon: 'user' },
    { key: 'premium', label: 'Premium', icon: 'rocket' },
    { key: 'settings', label: 'Settings', icon: 'settings' },
    { key: 'account', label: 'Account', icon: 'shield' },
];

const BOTTOM_NAV: Array<{ key: string; label: string; icon: IconName; target?: NavTarget }> = [
    { key: 'home', label: 'Home', icon: 'home', target: 'home' },
    { key: 'games', label: 'Game Hub', icon: 'gamepad', target: 'game-hub' },
    { key: 'challenges', label: 'Challenges', icon: 'target', target: 'challenges' },
    { key: 'tournaments', label: 'Tournaments', icon: 'medal', target: 'tournaments' },
    { key: 'rank', label: 'Rank', icon: 'trophy', target: 'leaderboards' },
];

interface HubChromeProps {
    active?: 'home' | 'hub' | NavTarget;
    profile: ProfileProgress | null;
    user: SessionUser | null;
    displayName: string;
    noticeDot?: boolean;
    search?: ReactNode;
    children: ReactNode;
}

const COLLAPSE_KEY = 'vs-rail-collapsed';

function activeForPath(pathname: string): NavTarget | null {
    if (pathname.startsWith('/game-hub') || pathname.startsWith('/games')) return 'game-hub';
    for (const key of Object.keys(ROUTES) as NavTarget[]) {
        if (pathname === ROUTES[key] || pathname.startsWith(`${ROUTES[key]}/`)) return key;
    }
    return null;
}

export default function HubChrome({
    active,
    profile,
    user,
    displayName,
    noticeDot = false,
    search,
    children,
}: HubChromeProps) {
    const navigate = useNavigate();
    const location = useLocation();
    const { logout } = useAuthStore();

    const [drawerOpen, setDrawerOpen] = useState(false);
    const [profileOpen, setProfileOpen] = useState(false);
    const [confirmOpen, setConfirmOpen] = useState(false);
    const [signingOut, setSigningOut] = useState(false);
    const [collapsed, setCollapsed] = useState(() => localStorage.getItem(COLLAPSE_KEY) === '1');

    useEffect(() => {
        localStorage.setItem(COLLAPSE_KEY, collapsed ? '1' : '0');
    }, [collapsed]);

    const activeKey: NavTarget = useMemo(() => {
        if (active === 'home' || active === 'hub') {
            return active === 'home' ? 'home' : 'game-hub';
        }
        return active ?? activeForPath(location.pathname) ?? 'home';
    }, [active, location.pathname]);

    function go(target: NavTarget | string, fromBottomProfile = false) {
        if (target === 'profile' && fromBottomProfile) {
            setProfileOpen(true);
            return;
        }
        setDrawerOpen(false);
        setProfileOpen(false);
        const route = ROUTES[target as NavTarget] ?? '';
        if (!route) return;
        if (route.startsWith('/home#')) {
            if (location.pathname === '/home') {
                const id = route.split('#')[1];
                document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
                return;
            }
            void navigate(route);
            return;
        }
        navigate(route);
    }

    async function handleLogout() {
        setSigningOut(true);
        await logout();
        setConfirmOpen(false);
        navigate('/login', { replace: true });
    }

    const vectorId = user?.vector_id ?? '';

    return (
        <div className={cn('vs-hub', collapsed && 'vs-hub--railcl')}>
            <header className="vs-hub__head">
                <div className="vs-hub__headtray">
                    <button
                        className="vs-hub__iconbtn vs-hub__menu"
                        aria-label="Open navigation"
                        onClick={() => setDrawerOpen(true)}
                    >
                        <Icon name="menu" size={22} />
                    </button>
                    <button
                        className="vs-hub__brand"
                        onClick={() => go('home')}
                        aria-label="Vector Strike home"
                    >
                        <Logo size="sm" showWordmark={false} />
                        <span className="vs-hub__brandname">VECTOR STRIKE</span>
                    </button>

                    {search ?? <div className="vs-hub__searchspacer" />}

                    <div className="vs-hub__headright">
                        <button
                            className="vs-hub__iconbtn"
                            aria-label="Notifications"
                            onClick={() => go('notifications')}
                        >
                            <Icon name="bell" size={20} />
                            {noticeDot && <span className="vs-hub__dot" aria-hidden />}
                        </button>

                        <button className="vs-hub__account" onClick={() => setProfileOpen((v) => !v)}>
                            <Avatar profile={profile} name={displayName} size="sm" />
                            <span className="vs-hub__accountinfo">
                                <b>{displayName}</b>
                                <small>
                                    @{user?.username ?? 'pilot'}
                                    {user?.verification_status === 'verified' || user?.age_verified ? (
                                        <span className="vs-badge vs-badge--verified vs-badge--tiny">Verified</span>
                                    ) : null}
                                </small>
                                <small>Level {profile?.level ?? 1} · {formatRank(profile?.rank)}</small>
                            </span>
                            <Icon
                                name="chevron"
                                size={14}
                                className={cn('vs-hub__caret', profileOpen && 'vs-hub__caret--open')}
                            />
                        </button>
                    </div>
                </div>
            </header>

            {profileOpen && (
                <>
                    <div className="vs-hub__profilebackdrop" onClick={() => setProfileOpen(false)} />
                    <div className="vs-hub__profilemenu animate-fade-up">
                        <div className="vs-hub__profilehead">
                            <Avatar profile={profile} name={displayName} size="md" />
                            <div>
                                <div className="vs-hub__profiletitle">
                                    <b>{displayName}</b>
                                    {user?.verification_status === 'verified' || user?.age_verified ? (
                                        <span className="vs-badge vs-badge--verified">Verified</span>
                                    ) : null}
                                </div>
                                <small>@{user?.username ?? ''}</small>
                                <span className="vs-hub__idline">{vectorId}</span>
                            </div>
                        </div>
                        <div className="vs-hub__profilexp">
                            <span className="vs-hub__profilexphead">
                                Level {profile?.level ?? 1} · {formatRank(profile?.rank)}
                            </span>
                            <div className="vs-hub__bar">
                                <div className="vs-hub__barfill" style={{ width: `${profile?.xp_progress ?? 0}%` }} />
                            </div>
                            <small>{profile?.xp ?? 0} / {profile?.xp_for_next ?? 100} XP</small>
                        </div>
                        <div className="vs-hub__profilelinks">
                            <button onClick={() => { setProfileOpen(false); go('profile'); }}>
                                <Icon name="user" size={16} /> Profile
                            </button>
                            <button onClick={() => { setProfileOpen(false); go('progress'); }}>
                                <Icon name="check" size={16} /> Progress
                            </button>
                            <button onClick={() => { setProfileOpen(false); go('achievements'); }}>
                                <Icon name="star" size={16} /> Achievements
                            </button>
                            <button onClick={() => { setProfileOpen(false); go('social'); }}>
                                <Icon name="users" size={16} /> Social
                            </button>
                            <button onClick={() => { setProfileOpen(false); go('messages'); }}>
                                <Icon name="message" size={16} /> Messages
                            </button>
                            <button onClick={() => { setProfileOpen(false); go('notifications'); }}>
                                <Icon name="bell" size={16} /> Notifications
                            </button>
                            <button onClick={() => { setProfileOpen(false); go('premium'); }}>
                                <Icon name="rocket" size={16} /> Premium
                            </button>
                            <button onClick={() => { setProfileOpen(false); go('settings'); }}>
                                <Icon name="settings" size={16} /> Settings
                            </button>
                            <button onClick={() => { setProfileOpen(false); go('account'); }}>
                                <Icon name="shield" size={16} /> Account
                            </button>
                        </div>
                        <div className="vs-hub__profilefoot">
                            <Button variant="danger" size="md" icon="logout" fullWidth onClick={() => { setProfileOpen(false); setConfirmOpen(true); }}>
                                Log out
                            </Button>
                        </div>
                    </div>
                </>
            )}

            {drawerOpen && (
                <>
                    <div className="vs-hub__drawerbackdrop" onClick={() => setDrawerOpen(false)} />
                    <aside className="vs-hub__drawer">
                        <div className="vs-hub__drawerhead">
                            <Logo size="sm" />
                            <button className="vs-hub__iconbtn" aria-label="Close navigation" onClick={() => setDrawerOpen(false)}>
                                <Icon name="x" size={22} />
                            </button>
                        </div>
                        <SideNav active={activeKey} onNavigate={go} />
                        <div className="vs-hub__drawerfoot">
                            <RankMini profile={profile} onClick={() => go('leaderboards')} />
                        </div>
                    </aside>
                </>
            )}

            <aside className="vs-hub__rail">
                <button className="vs-hub__railbrand" onClick={() => go('home')} aria-label="Vector Strike home">
                    <Logo size="sm" showWordmark={false} />
                    <span className="vs-hub__railname">VECTOR STRIKE</span>
                </button>
                <SideNav active={activeKey} onNavigate={go} />
                <div className="vs-hub__railfoot">
                    <button
                        className="vs-hub__collapsebtn"
                        onClick={() => setCollapsed((c) => !c)}
                        aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                        title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
                    >
                        <Icon name={collapsed ? 'chevron-right' : 'chevron-left'} size={16} />
                    </button>
                    <RankMini profile={profile} onClick={() => go('leaderboards')} />
                </div>
            </aside>

            <main className="vs-hub__main">{children}</main>

            <nav className="vs-hub__bottomnav" aria-label="Primary">
                {BOTTOM_NAV.map((item) => (
                    <button
                        key={item.key}
                        className={cn(
                            'vs-hub__bottomitem',
                            activeKey === (item.target ?? item.key) && 'vs-hub__bottomitem--active'
                        )}
                        onClick={() =>
                            item.key === 'more'
                                ? setDrawerOpen(true)
                                : item.key === 'profile' && !item.target
                                ? setProfileOpen(true)
                                : go(item.target ?? item.key)
                        }
                    >
                        <Icon name={item.icon} size={20} />
                        <span>{item.label}</span>
                    </button>
                ))}
            </nav>

            {confirmOpen && (
                <div className="vs-hub__confirm">
                    <div className="vs-hub__confirmcard animate-pop" role="dialog" aria-modal="true" aria-labelledby="logout-title">
                        <span className="vs-hub__confirmlogo">
                            <Logo size="md" showWordmark={false} />
                        </span>
                        <h2 id="logout-title">Sign out of Vector Strike?</h2>
                        <p>You’ll need to sign in again to access your Game Hub. Your progress is safe.</p>
                        <div className="vs-hub__confirmactions">
                            <Button variant="ghost" size="lg" onClick={() => setConfirmOpen(false)} disabled={signingOut}>
                                Cancel
                            </Button>
                            <Button variant="danger" size="lg" icon="logout" loading={signingOut} onClick={() => void handleLogout()}>
                                Sign out
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function SideNav({ active, onNavigate }: { active: NavTarget; onNavigate: (t: NavTarget) => void }) {
    return (
        <nav className="vs-hub__sidenav" aria-label="Sidebar">
            {SIDE_NAV.map((item) => (
                <button
                    key={item.key}
                    className={cn('vs-hub__navitem', active === item.key && 'vs-hub__navitem--active')}
                    disabled={item.soon}
                    onClick={() => onNavigate(item.key)}
                    title={item.label}
                >
                    <Icon name={item.icon} size={19} />
                    <span className="vs-hub__navlabel">{item.label}</span>
                    {item.soon && <span className="vs-hub__soon">Soon</span>}
                </button>
            ))}
        </nav>
    );
}

function RankMini({ profile, onClick }: { profile: ProfileProgress | null; onClick: () => void }) {
    return (
        <button className="vs-hub__rankmini" onClick={onClick}>
            <div className="vs-hub__rankminitop">
                <span>Level {profile?.level ?? 1}</span>
                <b>{formatRank(profile?.rank)}</b>
            </div>
            <div className="vs-hub__bar">
                <div className="vs-hub__barfill" style={{ width: `${profile?.xp_progress ?? 0}%` }} />
            </div>
            <small>{profile?.xp ?? 0} XP</small>
        </button>
    );
}