import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { cn } from '../utils/cn';
import Icon, { IconName } from '../components/Icon';
import Button from '../components/Button';
import HubChrome from '../components/hub/HubChrome';
import CategoryCarousel from '../components/hub/CategoryCarousel';
import {
    Avatar,
    EmptyState,
    GameCardView,
    SectionHead,
    formatDate,
    formatRank,
    formatSkill,
} from '../components/hub/HubBits';
import { useAuthStore } from '../store/auth';
import { fetchHome } from '../services/home';
import {
    Achievement,
    CategorySummary,
    DailyChallenge,
    GameCard,
    HomeEvent,
    HomeFeed,
    Mission,
} from '../types/home';

type LoadState = 'loading' | 'ready' | 'error';

const ACHIEVEMENT_ICONS: Record<string, IconName> = {
    gamepad: 'gamepad',
    puzzle: 'puzzle',
    bolt: 'bolt',
    rocket: 'rocket',
    compass: 'compass',
    star: 'star',
    shield: 'shield',
    brain: 'brain',
};

export default function HomePage() {
    const navigate = useNavigate();
    const location = useLocation();
    const { user } = useAuthStore();
    const [state, setState] = useState<LoadState>('loading');
    const [feed, setFeed] = useState<HomeFeed | null>(null);
    const [errorMsg, setErrorMsg] = useState('');
    const [loadKey, setLoadKey] = useState(0);

    const [activeCategory, setActiveCategory] = useState('all');

    useEffect(() => {
        let cancelled = false;
        setState('loading');
        setActiveCategory('all');
        setFeed(null);
        fetchHome()
            .then((data) => {
                if (cancelled) return;
                setFeed(data);
                setState('ready');
            })
            .catch((err: unknown) => {
                if (cancelled) return;
                setErrorMsg(err instanceof Error ? err.message : 'Something went wrong.');
                setState('error');
            });
        return () => {
            cancelled = true;
        };
    }, [loadKey]);

    const reducedMotion = useMemo(
        () => typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches,
        []
    );

    // Deep-link scroll: /home#hub-... navigates straight to a section.
    useEffect(() => {
        const id = location.hash.replace('#', '');
        if (!id) return;
        const timer = window.setTimeout(() => {
            const el = document.getElementById(id);
            if (!el) return;
            el.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'start' });
        }, 80);
        return () => window.clearTimeout(timer);
    }, [location.hash, reducedMotion]);

    const profile = feed?.profile ?? null;
    const displayName = profile?.display_name || user?.full_name || user?.username || 'Pilot';
    const vectorId = user?.vector_id ?? '';

    const exploreGames = useMemo(() => {
        if (!feed) return [];
        return feed.games.filter((g) => {
            const inCategory = activeCategory === 'all' || g.categories.includes(activeCategory) || g.category.slug === activeCategory;
            return inCategory;
        });
    }, [feed, activeCategory]);

    if (state === 'loading') {
        return <HomeLoader />;
    }

    if (state === 'error' || !feed) {
        return (
            <div className="vs-hub vs-hub--error">
                <div className="vs-hub__errorcard animate-pop">
                    <span className="vs-hub__erroricon">
                        <Icon name="alert" size={28} />
                    </span>
                    <h1>We couldn’t load your Game Hub.</h1>
                    <p>{errorMsg || 'Please try again in a moment.'}</p>
                    <div className="vs-hub__erroractions">
                        <Button variant="outline" size="lg" icon="refresh" onClick={() => setLoadKey((k) => k + 1)}>
                            Retry
                        </Button>
                        <Button variant="ghost" size="lg" icon="layers" onClick={() => navigate('/game-hub')}>
                            Open game hub
                        </Button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <HubChrome
            active="home"
            profile={profile}
            user={user}
            displayName={displayName}
            search={<HomeSearchBox games={feed.games} />}
        >
            <main className="vs-hub__main" id="hub-top">
                {/* Hero */}
                <section className="vs-hub__hero animate-fade-up">
                    <div className="vs-hub__heroglow" aria-hidden />
                    <div className="vs-hub__herocontent">
                        <span className="vs-hub__eyebrow">YOUR GAME HUB</span>
                        <h1 className="vs-hub__herotitle">
                            Welcome back, {displayName}
                            {user?.verification_status === 'verified' || user?.age_verified ? (
                                <span className="vs-badge vs-badge--verified">Verified</span>
                            ) : null}
                            !
                        </h1>
                        <p className="vs-hub__herosub">
                            {profile
                                ? `Level ${profile.level} · ${formatRank(profile.rank)} · ${profile.xp} XP earned. Every game below is real and playable — no fake scores.`
                                : 'Your custom arcade is ready. Real games, real runs, honest progress.'}
                        </p>
                        <div className="vs-hub__heroactions">
                            {feed.continue_playing.length > 0 ? (
                                <Button size="lg" icon="play" onClick={() => scrollTo('hub-continue')}>
                                    Continue playing
                                </Button>
                            ) : (
                                <Button size="lg" icon="gamepad" onClick={() => navigate('/game-hub')}>
                                    Open game hub
                                </Button>
                            )}
                            <Button size="lg" variant="outline" iconRight="chevron" onClick={() => navigate('/game-hub')}>
                                Game Hub
                            </Button>
                        </div>
                    </div>
                    <div className="vs-hub__herostats">
                        <HeroStat value={feed.stats.games_played} label="Games played" icon="gamepad" />
                        <HeroStat value={feed.stats.categories_played} label="Categories" icon="layers" />
                        <HeroStat value={feed.stats.total_game_xp} label="Game XP" icon="bolt" />
                    </div>
                </section>

                {/* Rank / level card */}
                <section className="vs-hub__rank" id="hub-rank">
                    <div className="vs-hub__rankcard">
                        <div className="vs-hub__rankleft">
                            <Avatar profile={profile} name={displayName} size="lg" />
                            <div className="vs-hub__rankinfo">
                                <span className="vs-hub__ranklabel">{formatRank(profile?.rank)}</span>
                                <h2>{displayName}</h2>
                                <small>{formatSkill(profile?.skill_level)} · {vectorId}</small>
                            </div>
                        </div>
                        <div className="vs-hub__rankxp">
                            <div className="vs-hub__rankxphead">
                                <span>Level {profile?.level ?? 1}</span>
                                <span>
                                    {profile?.xp ?? 0} / {profile?.xp_for_next ?? 100} XP
                                </span>
                            </div>
                            <div className="vs-hub__bar vs-hub__bar--lg">
                                <div className="vs-hub__barfill" style={{ width: `${profile?.xp_progress ?? 0}%` }} />
                            </div>
                            <small className="vs-hub__rankxphint">
                                {profile
                                    ? `${profile.xp_for_next - profile.xp} XP to Level ${profile.level + 1}`
                                    : 'Play games to start earning XP.'}
                            </small>
                        </div>
                    </div>
                </section>

                {/* Continue / Start Your First */}
                {feed.continue_playing.length > 0 ? (
                    <SectionHead id="hub-continue" title="Continue Playing" icon="play" subtitle="Pick up where you left off." />
                ) : (
                    feed.start_your_first_challenge && (
                        <SectionHead id="hub-continue" title="Start Your First Challenge" icon="rocket" subtitle="Your arcade is waiting for you." />
                    )
                )}
                {feed.continue_playing.length > 0 ? (
                    <GameScroller games={feed.continue_playing} />
                ) : (
                    feed.start_your_first_challenge && (
                        <div className="vs-hub__firstchallenge animate-fade-up">
                            <p className="vs-hub__firstcopy">
                                Explore games that match what you love. Pick one and earn your first XP.
                            </p>
                            <div className="vs-hub__chips">
                                {feed.start_your_first_challenge.interests.map((i) => (
                                    <span key={i.slug} className="vs-chip">
                                        <Icon name="sparkles" size={14} /> {i.label}
                                    </span>
                                ))}
                            </div>
                            <Button variant="outline" size="md" icon="gamepad" onClick={() => navigate('/game-hub')}>
                                Open game hub
                            </Button>
                        </div>
                    )
                )}

                {/* Recommendations */}
                {feed.recommendations.length > 0 && (
                    <>
                        <SectionHead id="hub-recommended" title="Recommended For You" icon="sparkles" subtitle="Chosen from your interests and play style." />
                        <GameScroller games={feed.recommendations} />
                    </>
                )}

                {/* Quick runs */}
                {feed.quick_runs.length > 0 && (
                    <>
                        <div className="vs-homesec__head">
                            <SectionHead
                                id="hub-quick"
                                title="Quick Runs"
                                icon="timer"
                                subtitle="Under six minutes — perfect for a break."
                            />
                            <Button variant="ghost" size="sm" iconRight="chevron" onClick={() => navigate('/game-hub')}>
                                View all
                            </Button>
                        </div>
                        <GameScroller games={feed.quick_runs} />
                    </>
                )}

                {/* Explore the hub */}
                {feed.hub_categories.length > 0 && (
                    <>
                        <div className="vs-homesec__head">
                            <SectionHead
                                id="hub-explore-hub"
                                title="Explore the Hub"
                                icon="gamepad"
                                subtitle="Pick a track — every game inside is live, playable and tracked."
                            />
                            <Button size="sm" iconRight="chevron" onClick={() => navigate('/game-hub')}>
                                Open game hub
                            </Button>
                        </div>
                        <CategoryCarousel categories={feed.hub_categories} />
                    </>
                )}

                {/* Discovery sections */}
                {feed.sections.map((s) => (
                    <div key={s.key}>
                        <SectionHead title={s.title} icon="compass" />
                        <GameScroller games={s.games} />
                    </div>
                ))}

                {/* Explore */}
                <SectionHead id="hub-explore" title="Explore Games" icon="layers" subtitle="All {count} games in your age range." count={feed.games.length} />
                <div className="vs-hub__cats" role="tablist" aria-label="Game categories">
                    <button
                        className={cn('vs-hub__cat', activeCategory === 'all' && 'vs-hub__cat--active')}
                        onClick={() => setActiveCategory('all')}
                    >
                        All <span>{feed.games.length}</span>
                    </button>
                    {feed.categories.map((c: CategorySummary) => (
                        <button
                            key={c.slug}
                            className={cn('vs-hub__cat', activeCategory === c.slug && 'vs-hub__cat--active')}
                            onClick={() => setActiveCategory(c.slug)}
                        >
                            {c.label} <span>{c.games_count}</span>
                        </button>
                    ))}
                </div>
                {exploreGames.length > 0 ? (
                    <div className="vs-hub__grid">
                        {exploreGames.map((g) => (
                            <GameCardView key={g.slug} game={g} />
                        ))}
                    </div>
                ) : (
                    <EmptyState icon="search" title="No games found" body="Nothing matches your current filter. Try another category." />
                )}

                {/* Trending */}
                <SectionHead id="hub-trending" title="Trending Now" icon="flame" />
                {feed.trending.available ? (
                    <GameScroller games={feed.trending.games} live />
                ) : (
                    <EmptyState
                        icon="flame"
                        title="Trending is warming up"
                        body="The most-played games will appear here as the community gets moving."
                    />
                )}

                {/* New releases */}
                <SectionHead id="hub-new" title="New Releases" icon="sparkles" />
                {feed.new_games.length > 0 ? (
                    <GameScroller games={feed.new_games} />
                ) : (
                    <EmptyState icon="rocket" title="No new games yet" body="New titles will appear here as they launch." />
                )}

                {/* Daily challenge */}
                <SectionHead id="hub-challenge" title="Today’s Challenge" icon="target" />
                {feed.daily_challenge ? (
                    <ChallengeCard challenge={feed.daily_challenge} onPlay={() => navigate('/game-hub')} />
                ) : (
                    <EmptyState icon="target" title="No challenge active" body="A new daily challenge appears every day. Check back soon." />
                )}

                {/* Missions */}
                <SectionHead id="hub-missions" title="Missions" icon="check" subtitle={`${feed.missions.filter((m) => m.completed).length}/${feed.missions.length} completed`} />
                {feed.missions.length > 0 ? (
                    <div className="vs-hub__missions">
                        {feed.missions.map((m) => (
                            <MissionCard key={m.slug} mission={m} />
                        ))}
                    </div>
                ) : (
                    <EmptyState icon="check" title="No missions available" body="Missions will appear here soon. Keep playing to unlock goals." />
                )}

                {/* Achievements */}
                <SectionHead id="hub-achievements" title="Recent Achievements" icon="star" />
                {feed.achievements.length > 0 ? (
                    <div className="vs-hub__achgrid">
                        {feed.achievements.map((a) => (
                            <AchievementCard key={a.slug} ach={a} />
                        ))}
                    </div>
                ) : (
                    <EmptyState
                        icon="star"
                        title="Your first achievement is waiting."
                        body="Complete games, keep streaks and explore new categories to unlock badges."
                    />
                )}

                {/* Events */}
                <SectionHead id="hub-events" title="Live & Upcoming Events" icon="calendar" />
                {feed.events.length > 0 ? (
                    <div className="vs-hub__eventgrid">
                        {feed.events.map((e) => (
                            <EventCard key={e.slug} event={e} />
                        ))}
                    </div>
                ) : (
                    <EmptyState icon="calendar" title="No events right now" body="Tournaments and live challenges will show up here when they open." />
                )}

                <footer className="vs-hub__foot">
                    <span>VECTOR STRIKE · Player ID {vectorId}</span>
                </footer>
            </main>
        </HubChrome>
    );
}

/* ------------------------------------------------------------------ */
/* Small building blocks                                               */
/* ------------------------------------------------------------------ */

function HomeLoader() {
    const hints = ['Loading your games…', 'Preparing your arcade…', 'Fetching your stats…', 'Warming up the servers…'];
    const [hint] = useState(() => hints[Math.floor(Math.random() * hints.length)]);
    return (
        <div className="vs-hub-loader" role="status" aria-label="Loading your Game Hub">
            <div className="vs-hub-loader__ring">
                <div className="vs-hub-loader__orbit" aria-hidden />
                <AvatarSkeleton />
            </div>
            <p className="vs-hub-loader__headline">{hint}</p>
            <div className="vs-hub-loader__skeleton" aria-hidden>
                <div className="vs-hub-loader__hero" />
                <div className="vs-hub-loader__row">
                    <div className="vs-hub-loader__card" />
                    <div className="vs-hub-loader__card" />
                    <div className="vs-hub-loader__card" />
                    <div className="vs-hub-loader__card" />
                </div>
            </div>
        </div>
    );
}

function AvatarSkeleton() {
    return (
        <div className="vs-avatar vs-avatar--xl vs-avatar--skeleton">
            <img src="/assets/branding/logo-mark.svg" alt="" aria-hidden draggable={false} />
        </div>
    );
}

function HomeSearchBox({ games }: { games: GameCard[] }) {
    const [query, setQuery] = useState('');
    const [focused, setFocused] = useState(false);
    const navigate = useNavigate();
    const boxRef = useRef<HTMLDivElement>(null);

    const results = useMemo(() => {
        const q = query.trim().toLowerCase();
        if (!q || !games) return [];
        return games
            .filter((g) => [g.title, g.tagline, g.category.label, g.difficulty_label].join(' ').toLowerCase().includes(q))
            .slice(0, 6);
    }, [query, games]);

    useEffect(() => {
        function onDoc(e: MouseEvent) {
            if (boxRef.current && !boxRef.current.contains(e.target as Node)) setFocused(false);
        }
        document.addEventListener('mousedown', onDoc);
        return () => document.removeEventListener('mousedown', onDoc);
    }, []);

    const open = focused && query.trim().length > 0;

    return (
        <div className="vs-hub__search" role="search" ref={boxRef}>
            <Icon name="search" size={18} className="vs-hub__searchicon" />
            <input
                type="text"
                className="vs-hub__searchinput"
                placeholder="Search games…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onFocus={() => setFocused(true)}
                aria-label="Search games"
            />
            {query && (
                <button className="vs-hub__searchclear" aria-label="Clear search" onClick={() => setQuery('')}>
                    <Icon name="x" size={16} />
                </button>
            )}
            {open && (
                <div className="vs-hub__searchpanel">
                    {results.length === 0 ? (
                        <div className="vs-hub__searchempty">
                            No games match “{query.trim()}”. Search the full hub instead.
                        </div>
                    ) : (
                        results.map((g) => (
                            <button
                                key={g.slug}
                                className="vs-hub__searchitem"
                                onClick={() => {
                                    setFocused(false);
                                    setQuery('');
                                    navigate(`/games/${g.slug}`);
                                }}
                            >
                                <span className="vs-hub__searchthumb">{g.title.charAt(0)}</span>
                                <span className="vs-hub__searchmeta">
                                    <b>{g.title}</b>
                                    <small>{g.category.label} · {g.difficulty_label}</small>
                                </span>
                                <Icon name="arrow" size={14} className="vs-hub__searchgo" />
                            </button>
                        ))
                    )}
                </div>
            )}
        </div>
    );
}

function scrollTo(id: string) {
    const el = document.getElementById(id);
    if (!el) return;
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function HeroStat({ value, label, icon }: { value: number; label: string; icon: IconName }) {
    return (
        <div className="vs-hub__herosstat">
            <Icon name={icon} size={18} />
            <b>{value}</b>
            <span>{label}</span>
        </div>
    );
}

function GameScroller({ games, live }: { games: GameCard[]; live?: boolean }) {
    return (
        <div className={cn('vs-hub__scroller', live && 'vs-hub__scroller--live')}>
            {games.map((g) => (
                <GameCardView key={g.slug} game={g} live={Boolean(live)} />
            ))}
        </div>
    );
}

function ChallengeCard({ challenge, onPlay }: { challenge: DailyChallenge; onPlay: () => void }) {
    const expires = challenge.expires_at ? new Date(challenge.expires_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'later today';
    return (
        <div className="vs-hub__challengecard animate-fade-up">
            <img src={challenge.game.thumbnail} alt="" loading="lazy" className="vs-hub__challengethumb" onError={(e) => (e.currentTarget.style.display = 'none')} />
            <div className="vs-hub__challengebody">
                <span className="vs-hub__challengetag">
                    <span className="vs-hub__pulse" aria-hidden /> Ends at {expires}
                </span>
                <h3>{challenge.title}</h3>
                <p>{challenge.description}</p>
                <div className="vs-hub__challengegoals">
                    <span>
                        <Icon name="target" size={14} /> {challenge.goal}
                    </span>
                    <span>
                        <Icon name="bolt" size={14} /> +{challenge.reward_xp} XP
                    </span>
                    <span>
                        <Icon name="gamepad" size={14} /> {challenge.game.title}
                    </span>
                </div>
                <Button size="md" icon="play" onClick={onPlay}>
                    Play {challenge.game.title}
                </Button>
            </div>
        </div>
    );
}

function MissionCard({ mission }: { mission: Mission }) {
    const pct = Math.min(100, Math.round((mission.progress / mission.target) * 100));
    return (
        <div className={cn('vs-hub__mission', mission.completed && 'vs-hub__mission--done')}>
            <span className="vs-hub__missionicon">
                <Icon name={mission.completed ? 'check' : 'target'} size={20} />
            </span>
            <div className="vs-hub__missionbody">
                <div className="vs-hub__missionhead">
                    <b>{mission.title}</b>
                    <span className="vs-hub__missionxp">+{mission.xp_reward} XP</span>
                </div>
                <p>{mission.description}</p>
                <div className="vs-hub__missionprogress">
                    <span className="vs-hub__bar">
                        <span className="vs-hub__barfill" style={{ width: `${pct}%` }} />
                    </span>
                    <small>
                        {mission.completed ? 'Completed' : `${mission.progress} / ${mission.target}`}
                    </small>
                </div>
            </div>
        </div>
    );
}

function AchievementCard({ ach }: { ach: Achievement }) {
    const icon = ACHIEVEMENT_ICONS[ach.icon] ?? 'star';
    return (
        <div className="vs-hub__ach">
            <span className="vs-hub__achicon">
                <Icon name={icon} size={22} />
            </span>
            <div>
                <b>{ach.title}</b>
                <p>{ach.description}</p>
                <small>Unlocked {formatDate(ach.earned_at)}</small>
            </div>
        </div>
    );
}

function EventCard({ event }: { event: HomeEvent }) {
    return (
        <div className="vs-hub__eventcard">
            <div className="vs-hub__eventhead">
                <span className={cn('vs-hub__eventstatus', `vs-hub__eventstatus--${event.status.toLowerCase()}`)}>
                    {event.status === 'live' ? 'LIVE' : 'UPCOMING'}
                </span>
                <span className="vs-hub__eventdate">{formatDate(event.starts_at)}</span>
            </div>
            <h3>{event.title}</h3>
            <p>{event.description}</p>
        </div>
    );
}