import { FormEvent, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import HubChrome from '../components/hub/HubChrome';
import CategoryCarousel from '../components/hub/CategoryCarousel';
import Icon from '../components/Icon';
import Button from '../components/Button';
import { fetchHub, fetchHubCategories, fetchHubCategory, fetchCatalog, searchHub } from '../services/hub';
import {
    CategoryPage,
    CatalogPage,
    HubFeed,
    HubSearchResult,
} from '../types/hub';
import type { HomeFeed } from '../types/home';
import { useAuthStore } from '../store/auth';
import { fetchHome } from '../services/home';
import {
    EmptyState,
    GameCardSkeleton,
    GameCardView,
    SectionHead,
} from '../components/hub/HubBits';

const PAGE_SIZE = 12;

export default function GameHubPage() {
    const { ident } = useParams<{ ident?: string }>();
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { user } = useAuthStore();

    const q = searchParams.get('q') ?? '';

    const [profile, setProfile] = useState<HomeFeed['profile']>(null);
    const [categories, setCategories] = useState<HomeFeed['hub_categories']>([]);

    useEffect(() => {
        fetchHome()
            .then((feed) => setProfile(feed.profile))
            .catch(() => undefined);
        fetchHubCategories()
            .then(setCategories)
            .catch(() => undefined);
    }, []);

    const displayName = profile?.display_name || user?.full_name || user?.username || 'Pilot';
    const activeIdent = ident ?? (q ? 'search' : '');

    let body: ReactNode;
    if (q.trim()) {
        body = <SearchResults key={q} query={q.trim()} onPickCategory={(i) => navigate(`/game-hub/${i}`)} />;
    } else if (ident) {
        body = (
            <CategoryPageView
                key={ident}
                ident={ident}
                onPickCategory={(i) => navigate(`/game-hub/${i}`)}
            />
        );
    } else {
        body = <HubHome />;
    }

    return (
        <HubChrome
            active="hub"
            profile={profile}
            user={user}
            displayName={displayName}
            search={<HubSearchBox />}
        >
            <div className="vs-gamehub">
                <section className="vs-gamehub__hero">
                    <div className="vs-gamehub__herohead">
                        <span className="vs-gamehub__eyebrow">
                            <Icon name="gamepad" size={15} /> GAME HUB
                        </span>
                        <h1>Pick a run. Sharpen a skill.</h1>
                        <p>Every game here is live, playable and tracked — no fake scores, no dead links.</p>
                    </div>
                </section>

                <CategoryCarousel categories={categories} activeIdent={activeIdent} />

                {body}
            </div>
        </HubChrome>
    );
}

function HubSearchBox() {
    const [value, setValue] = useState('');
    const [searchParams, setSearchParams] = useSearchParams();

    useEffect(() => {
        const q = searchParams.get('q') ?? '';
        if (q) setValue(q);
    }, [searchParams]);

    function submit(e: FormEvent) {
        e.preventDefault();
        const q = value.trim();
        setSearchParams(q ? { q } : {});
    }

    return (
        <form className="vs-hub__search" onSubmit={submit}>
            <Icon name="search" size={16} className="vs-hub__searchicon" />
            <input
                className="vs-hub__searchinput"
                value={value}
                onChange={(e) => setValue(e.target.value)}
                placeholder="Search games…"
                aria-label="Search games"
            />
            {value && (
                <button type="button" className="vs-hub__searchclear" onClick={() => setValue('')} aria-label="Clear search">
                    <Icon name="x" size={14} />
                </button>
            )}
        </form>
    );
}

function HubHome() {
    const [hub, setHub] = useState<HubFeed | null>(null);
    const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading');
    const [catalog, setCatalog] = useState<CatalogPage | null>(null);

    useEffect(() => {
        let cancelled = false;
        setState('loading');
        Promise.all([fetchHub(), fetchCatalog({ sort: 'release', page: 1, page_size: PAGE_SIZE })])
            .then(([h, c]) => {
                if (cancelled) return;
                setHub(h);
                setCatalog(c);
                setState('ready');
            })
            .catch(() => {
                if (!cancelled) setState('error');
            });
        return () => {
            cancelled = true;
        };
    }, []);

    if (state === 'loading') {
        return (
            <div className="vs-hub__sections">
                <SectionSkeleton />
                <SectionSkeleton />
                <SectionSkeleton />
            </div>
        );
    }

    if (state === 'error' || !hub) {
        return (
            <EmptyState
                icon="alert"
                title="The hub is offline."
                body="We couldn’t reach the game hub. Check your connection and try again."
                action={{ label: 'Retry', onClick: () => window.location.reload() }}
            />
        );
    }

    return (
        <div className="vs-hub__sections">
            {hub.continue_running.length > 0 && (
                <HubSection title="Continue running" icon="play">
                    {hub.continue_running.map((g) => (
                        <GameCardView key={g.slug} game={g} />
                    ))}
                </HubSection>
            )}

            <HubSection
                title="Quick runs"
                icon="timer"
                subtitle="Under six minutes — perfect between things."
            >
                {hub.quick_runs.map((g) => (
                    <GameCardView key={g.slug} game={g} />
                ))}
            </HubSection>

            {hub.deep_runs.length > 0 && (
                <HubSection title="Deep dives" icon="clock" subtitle="Longer sessions with more levels.">
                    {hub.deep_runs.map((g) => (
                        <GameCardView key={g.slug} game={g} />
                    ))}
                </HubSection>
            )}

            {hub.trending.available && (
                <HubSection title="Trending now" icon="flame" subtitle="Most played in the last week.">
                    {hub.trending.games.map((g) => (
                        <GameCardView key={g.slug} game={g} />
                    ))}
                </HubSection>
            )}

            {hub.new_drops.length > 0 && (
                <HubSection title="New drops" icon="sparkles" subtitle="Fresh additions to the hub.">
                    {hub.new_drops.map((g) => (
                        <GameCardView key={g.slug} game={g} />
                    ))}
                </HubSection>
            )}

            {hub.challenge_mode.length > 0 && (
                <HubSection title="Challenge mode" icon="crown" subtitle="Pressure runs with a real target.">
                    {hub.challenge_mode.map((g) => (
                        <GameCardView key={g.slug} game={g} />
                    ))}
                </HubSection>
            )}

            {hub.recommended.length > 0 && (
                <HubSection title="Recommended for you" icon="sparkles">
                    {hub.recommended.map((g) => (
                        <GameCardView key={g.slug} game={g} />
                    ))}
                </HubSection>
            )}

            <BrowseAll catalog={catalog} />
        </div>
    );
}

function BrowseAll({ catalog }: { catalog: CatalogPage | null }) {
    const [items, setItems] = useState<CatalogPage['results']>(catalog?.results ?? []);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(catalog?.has_more ?? false);
    const [total, setTotal] = useState(catalog?.total ?? 0);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        setItems(catalog?.results ?? []);
        setPage(catalog?.page ?? 1);
        setHasMore(catalog?.has_more ?? false);
        setTotal(catalog?.total ?? 0);
    }, [catalog]);

    const totalText = total > 0 ? `${total} live games` : 'Everything live';

    async function loadMore() {
        if (!hasMore || loading) return;
        setLoading(true);
        try {
            const next = await fetchCatalog({ sort: 'release', page: page + 1, page_size: PAGE_SIZE });
            setItems((prev) => [...prev, ...next.results]);
            setPage(next.page);
            setHasMore(next.has_more);
            setTotal(next.total);
        } finally {
            setLoading(false);
        }
    }

    return (
        <section className="vs-hub__section" id="browse">
            <SectionHead title="Browse everything" icon="layers" subtitle={totalText} />
            {items.length === 0 ? (
                <EmptyState
                    icon="layers"
                    title="Nothing here yet."
                    body="The catalog is still being seeded. Try the categories above."
                />
            ) : (
                <div className="vs-hub__grid">
                    {items.map((g) => (
                        <GameCardView key={g.slug} game={g} />
                    ))}
                </div>
            )}
            {hasMore && (
                <div className="vs-hub__loadmore">
                    <Button variant="outline" icon="refresh" loading={loading} onClick={() => void loadMore()}>
                        Load more
                    </Button>
                </div>
            )}
        </section>
    );
}

function HubSection({
    title,
    icon,
    subtitle,
    children,
}: {
    title: string;
    icon: Parameters<typeof Icon>[0]['name'];
    subtitle?: string;
    children: ReactNode;
}) {
    return (
        <section className="vs-hub__section">
            <SectionHead title={title} icon={icon} subtitle={subtitle} />
            <div className="vs-hub__scroller">
                {children}
            </div>
        </section>
    );
}

function SectionSkeleton() {
    return (
        <section className="vs-hub__section">
            <div className="vs-skeleton vs-skeleton--block vs-hub__sktitle" />
            <div className="vs-hub__scroller">
                <GameCardSkeleton />
                <GameCardSkeleton />
            </div>
        </section>
    );
}

function CategoryPageView({ ident, onPickCategory }: { ident: string; onPickCategory: (i: string) => void }) {
    const [page, setPage] = useState<CategoryPage | null>(null);
    const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading');
    const [allGames, setAllGames] = useState<CategoryPage['games'] | null>(null);
    const [loadMore, setLoadMore] = useState(false);

    useEffect(() => {
        let cancelled = false;
        setState('loading');
        setPage(null);
        setAllGames(null);
        fetchHubCategory(ident, 1)
            .then((p) => {
                if (cancelled) return;
                setPage(p);
                setAllGames(p.games);
                setState('ready');
            })
            .catch(() => {
                if (!cancelled) setState('error');
            });
        return () => {
            cancelled = true;
        };
    }, [ident]);

    if (state === 'loading') {
        return (
            <div className="vs-hub__sections">
                <SectionSkeleton />
                <SectionSkeleton />
            </div>
        );
    }

    if (state === 'error' || !page) {
        return (
            <EmptyState
                icon="alert"
                title="Couldn’t load this category."
                body="Check the address and try again."
                action={{ label: 'Back to all games', onClick: () => onPickCategory('all') }}
            />
        );
    }

    const cat = page.category;
    const isGhost = !cat.accent && cat.games_count === 0;

    if (isGhost) {
        return (
            <EmptyState
                icon="compass"
                title={`Nothing under "${cat.label}" yet.`}
                body="That track hasn’t been seeded. Browse everything, or jump into any of the categories above."
                action={{ label: 'Browse all games', onClick: () => onPickCategory('all') }}
            />
        );
    }

    async function loadMoreGames() {
        if (!allGames || !allGames.has_more || loadMore) return;
        setLoadMore(true);
        try {
            const next = await fetchHubCategory(ident, allGames.page + 1);
            setAllGames((prev) =>
                prev
                    ? {
                          ...next.games,
                          results: [...prev.results, ...next.games.results],
                      }
                    : next.games
            );
        } finally {
            setLoadMore(false);
        }
    }

    return (
        <div className="vs-hub__sections" key={ident}>
            <section className="vs-cat__hero" style={{ ['--cat-accent' as string]: cat.accent || '#7c5cff' }}>
                <span className="vs-cat__icon" style={{ ['--cat-accent' as string]: cat.accent || '#7c5cff' }}>
                    <Icon name={(cat.icon as never) ?? 'puzzle'} size={26} />
                </span>
                <div>
                    <h2>{cat.label}</h2>
                    <p>{cat.tagline || 'A live track in the game hub.'}</p>
                    <span className="vs-cat__count">
                        {cat.games_count} {cat.games_count === 1 ? 'game' : 'games'}
                    </span>
                </div>
            </section>

            {page.featured.length > 0 && (
                <HubSection title="Featured in this track" icon="star">
                    {page.featured.map((g) => (
                        <GameCardView key={g.slug} game={g} />
                    ))}
                </HubSection>
            )}

            {page.quick_runs.length > 0 && (
                <HubSection title="Quick runs" icon="timer">
                    {page.quick_runs.map((g) => (
                        <GameCardView key={g.slug} game={g} />
                    ))}
                </HubSection>
            )}

            {page.deep_runs.length > 0 && (
                <HubSection title="Deep dives" icon="clock">
                    {page.deep_runs.map((g) => (
                        <GameCardView key={g.slug} game={g} />
                    ))}
                </HubSection>
            )}

            <section className="vs-hub__section">
                <SectionHead
                    title="All games"
                    icon="layers"
                    subtitle={allGames ? `${allGames.total} ${allGames.total === 1 ? 'game' : 'games'}` : undefined}
                />
                {allGames && allGames.results.length === 0 ? (
                    <EmptyState
                    icon="layers"
                    title="No games in this track yet."
                    body="Check back soon."
                />
                ) : (
                    <div className="vs-hub__grid">
                        {(allGames?.results ?? []).map((g) => (
                            <GameCardView key={g.slug} game={g} />
                        ))}
                    </div>
                )}
                {allGames?.has_more && (
                    <div className="vs-hub__loadmore">
                        <Button variant="outline" icon="refresh" loading={loadMore} onClick={() => void loadMoreGames()}>
                            Load more
                        </Button>
                    </div>
                )}
            </section>
        </div>
    );
}

function SearchResults({ query, onPickCategory }: { query: string; onPickCategory: (i: string) => void }) {
    const [result, setResult] = useState<HubSearchResult | null>(null);
    const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading');

    useEffect(() => {
        let cancelled = false;
        setState('loading');
        searchHub(query)
            .then((r) => {
                if (cancelled) return;
                setResult(r);
                setState('ready');
            })
            .catch(() => {
                if (!cancelled) setState('error');
            });
        return () => {
            cancelled = true;
        };
    }, [query]);

    return (
        <div className="vs-hub__sections">
            <SectionHead title={`Results for “${query}”`} icon="search" subtitle="Live matches across the catalog" />
            {state === 'loading' && (
                <div className="vs-hub__grid">
                    <GameCardSkeleton />
                    <GameCardSkeleton />
                </div>
            )}
            {state === 'error' && (
                <EmptyState
                icon="alert"
                title="Search failed."
                body="Try again in a moment."
            />
            )}
            {state === 'ready' && result && (
                <>
                    {result.categories.length > 0 && (
                        <div className="vs-hub__searchcats">
                            {result.categories.map((c) => (
                                <button key={c.ident} className="vs-hub__searchcat" onClick={() => onPickCategory(c.ident)}>
                                    <Icon name={(c.icon as never) ?? 'puzzle'} size={16} />
                                    <span>
                                        <b>{c.label}</b>
                                        <small>{c.games_count} games</small>
                                    </span>
                                    <Icon name="chevron-right" size={14} />
                                </button>
                            ))}
                        </div>
                    )}
                    {result.games.length === 0 && result.categories.length === 0 ? (
                        <EmptyState
                            icon="search"
                            title={`Nothing matches “${query}”.`}
                            body="Try a different term, like “cipher”, “orbit” or “pulse”."
                        />
                    ) : result.games.length > 0 ? (
                        <div className="vs-hub__grid">
                            {result.games.map((g) => (
                                <GameCardView key={g.slug} game={g} />
                            ))}
                        </div>
                    ) : null}
                </>
            )}
        </div>
    );
}