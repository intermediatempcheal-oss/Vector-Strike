import { useState } from 'react';
import type { MouseEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../../utils/cn';
import Icon, { IconName } from '../Icon';
import { GameCard, ProfileProgress } from '../../types/home';

export function formatRank(rank?: string | null): string {
    if (!rank) return 'Rookie';
    return rank
        .split(/[_\s]+/)
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(' ');
}

export function formatSkill(skill?: string | null): string {
    if (!skill) return 'Beginner';
    return skill.charAt(0).toUpperCase() + skill.slice(1);
}

export function formatDate(iso: string): string {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
}

export function formatDuration(minutes?: number | null): string {
    if (!minutes || minutes <= 0) return 'Short run';
    if (minutes < 60) return `${minutes} min`;
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    return m ? `${h}h ${m}m` : `${h}h`;
}

export function formatPlaytime(seconds: number): string {
    if (seconds < 60) return `${seconds}s`;
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return s ? `${m}m ${s}s` : `${m}m`;
}

export function Avatar({
    profile,
    name,
    size = 'md',
}: {
    profile: ProfileProgress | null;
    name: string;
    size?: 'sm' | 'md' | 'lg' | 'xl';
}) {
    const [imgError, setImgError] = useState(false);
    const initials = (name || 'P')
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map((w) => w[0])
        .join('')
        .toUpperCase();
    const src = profile?.avatar || profile?.avatar_url || '';
    if (src && !imgError) {
        return (
            <img
                src={src}
                alt=""
                aria-hidden
                className={cn('vs-avatar', `vs-avatar--${size}`)}
                onError={() => setImgError(true)}
                draggable={false}
            />
        );
    }
    return (
        <span className={cn('vs-avatar vs-avatar--initials', `vs-avatar--${size}`)} aria-hidden>
            {initials}
        </span>
    );
}

export function GameThumb({ game, className }: { game: GameCard; className?: string }) {
    const [error, setError] = useState(false);
    if (game.thumbnail && !error) {
        return (
            <img
                src={game.thumbnail}
                alt=""
                loading="lazy"
                className={className}
                onError={() => setError(true)}
                draggable={false}
            />
        );
    }
    return <div className={cn(className, 'vs-hub__thumbfallback')}>{game.title.charAt(0) || '?'}</div>;
}

export function Stars({ stars }: { stars: boolean[] }) {
    return (
        <span className="vs-hub__stars" aria-label="Difficulty">
            {stars.map((on, i) => (
                <Icon key={i} name="star" size={12} className={cn('vs-hub__star', !on && 'vs-hub__star--off')} />
            ))}
        </span>
    );
}

export function SectionHead({
    title,
    icon,
    subtitle,
    id,
    count,
}: {
    title: string;
    icon: IconName;
    subtitle?: string;
    id?: string;
    count?: number;
}) {
    return (
        <div className="vs-hub__sectionhead" id={id}>
            <span className="vs-hub__sectionicon">
                <Icon name={icon} size={16} />
            </span>
            <div>
                <h2>
                    {title}
                    {typeof count === 'number' && <small>{count}</small>}
                </h2>
                {subtitle && <p>{subtitle}</p>}
            </div>
        </div>
    );
}

export function EmptyState({
    icon,
    title,
    body,
    action,
}: {
    icon: IconName;
    title: string;
    body: string;
    action?: { label: string; onClick: () => void };
}) {
    return (
        <div className="vs-hub__empty animate-fade-in">
            <span className="vs-hub__emptyicon">
                <Icon name={icon} size={22} />
            </span>
            <b>{title}</b>
            <p>{body}</p>
            {action && (
                <button className="vs-btn vs-btn--outline vs-btn--md" onClick={action.onClick}>
                    {action.label}
                </button>
            )}
        </div>
    );
}

/** Live action label for a game card, driven by real progress. */
export function actionFor(game: GameCard): { label: string; icon: IconName; kind?: string } {
    if (game.progress?.completion_percentage != null && game.progress.completion_percentage >= 100) {
        return { label: 'Replay', icon: 'rotate', kind: 'replay' };
    }
    if (game.progress?.games_played && game.progress.games_played > 0) {
        return { label: 'Continue', icon: 'play', kind: 'continue' };
    }
    if (game.is_new) {
        return { label: 'Play', icon: 'play', kind: 'new' };
    }
    return { label: 'Play', icon: 'play', kind: 'play' };
}

export function GameCardView({
    game,
    live = false,
    compact = false,
}: {
    game: GameCard;
    live?: boolean;
    compact?: boolean;
}) {
    const navigate = useNavigate();
    const action = actionFor(game);
    const openDetail = () => navigate(`/games/${game.slug}`);
    const openPlay = (e: MouseEvent) => {
        e.stopPropagation();
        navigate(`/games/${game.slug}/play`);
    };
    return (
        <article className={cn('vs-hub__gcard', compact && 'vs-hub__gcard--compact')} onClick={openDetail}>
            <div className="vs-hub__gthumbwrap">
                <GameThumb game={game} className="vs-hub__gthumb" />
                {game.is_new && <span className="vs-hub__newbadge">New</span>}
                {game.is_featured && !game.is_new && <span className="vs-hub__featbadge">Featured</span>}
            </div>
            <div className="vs-hub__gbody">
                <div className="vs-hub__gmeta">
                    <span className="vs-hub__gcat">{game.category.label}</span>
                    <Stars stars={game.difficulty_stars} />
                </div>
                <h3>{game.title}</h3>
                <p className="vs-hub__gtag">{game.tagline}</p>
                <div className="vs-hub__gchips">
                    {game.mechanics && <span className="vs-hub__gchip">{game.mechanics}</span>}
                    {game.duration_minutes ? (
                        <span className="vs-hub__gchip">
                            <Icon name="clock" size={12} /> {formatDuration(game.duration_minutes)}
                        </span>
                    ) : null}
                </div>
                <div className="vs-hub__gfoot">
                    {live && 'active_members' in game ? (
                        <span className="vs-hub__glive">
                            <Icon name="users" size={13} /> {(game as GameCard & { active_members: number }).active_members} active
                        </span>
                    ) : game.progress ? (
                        <span className="vs-hub__gprogress">
                            <span className="vs-hub__bar">
                                <span
                                    className="vs-hub__barfill"
                                    style={{ width: `${game.progress.completion_percentage}%` }}
                                />
                            </span>
                            {game.progress.completion_percentage}%
                        </span>
                    ) : (
                        <span className="vs-hub__gdiff">{game.difficulty_label}</span>
                    )}
                    <button
                        className="vs-btn vs-btn--sm vs-btn--solid vs-hub__gplay"
                        onClick={openPlay}
                        aria-label={`${action.label} ${game.title}`}
                    >
                        <Icon name={action.icon} size={13} /> {action.label}
                    </button>
                </div>
            </div>
        </article>
    );
}

export function GameCardSkeleton() {
    return (
        <div className="vs-hub__gcard-skel" aria-hidden>
            <div className="vs-hub__gcard-skelthumb" />
            <div className="vs-hub__gcard-skelbody">
                <div className="vs-hub__gcard-skelchip" />
                <div className="vs-hub__gcard-skeltitle" />
                <div className="vs-hub__gcard-skeltag" />
            </div>
        </div>
    );
}