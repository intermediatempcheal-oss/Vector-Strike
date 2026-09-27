import { useRef } from 'react';
import type { CSSProperties } from 'react';
import { useNavigate } from 'react-router-dom';
import { cn } from '../../utils/cn';
import Icon from '../Icon';
import { HubCategoryIdentity } from '../../types/home';

interface CategoryCarouselProps {
    categories: HubCategoryIdentity[];
    activeIdent?: string;
    basePath?: string;
    emptyText?: string;
}

export default function CategoryCarousel({
    categories,
    activeIdent,
    basePath = '/game-hub',
    emptyText = 'No categories available yet.',
}: CategoryCarouselProps) {
    const railRef = useRef<HTMLDivElement>(null);
    const navigate = useNavigate();

    if (!categories.length) {
        return <p className="vs-hub__carouselempty">{emptyText}</p>;
    }

    function step(dir: -1 | 1) {
        const el = railRef.current;
        if (!el) return;
        const amount = Math.max(120, el.clientWidth * 0.6);
        el.scrollBy({ left: dir * amount, behavior: 'smooth' });
    }

    return (
        <div className="vs-hub__carousel">
            <button
                className="vs-hub__carouselbtn vs-hub__carouselbtn--left"
                aria-label="Scroll categories left"
                onClick={() => step(-1)}
                tabIndex={-1}
            >
                <Icon name="chevron-left" size={18} />
            </button>
            <div className="vs-hub__carouselrail" ref={railRef} role="tablist" aria-label="Game categories">
                <button
                    className={cn('vs-hub__carouselitem', !activeIdent && 'vs-hub__carouselitem--active')}
                    role="tab"
                    aria-selected={!activeIdent}
                    onClick={() => navigate(`${basePath}`)}
                >
                    <span className="vs-hub__carouselglow" aria-hidden />
                    <b>ALL</b>
                    <small>Everything</small>
                </button>
                {categories.map((cat) => {
                    const active = activeIdent?.toLowerCase() === cat.slug.toLowerCase();
                    return (
                        <button
                            key={cat.slug}
                            className={cn('vs-hub__carouselitem', active && 'vs-hub__carouselitem--active')}
                            role="tab"
                            aria-selected={active}
                            style={cat.accent ? ({ '--cat-accent': cat.accent } as CSSProperties) : undefined}
                            onClick={() => navigate(`${basePath}/${cat.slug}`)}
                            onKeyDown={(e) => {
                                if (e.key === 'ArrowLeft') step(-1);
                                if (e.key === 'ArrowRight') step(1);
                            }}
                        >
                            <span className="vs-hub__carouselglow" aria-hidden />
                            <b>{cat.label}</b>
                            <small>{cat.games_count} game{cat.games_count === 1 ? '' : 's'}</small>
                        </button>
                    );
                })}
            </div>
            <button
                className="vs-hub__carouselbtn vs-hub__carouselbtn--right"
                aria-label="Scroll categories right"
                onClick={() => step(1)}
                tabIndex={-1}
            >
                <Icon name="chevron-right" size={18} />
            </button>
        </div>
    );
}