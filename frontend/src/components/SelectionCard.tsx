import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '../utils/cn';
import Icon, { IconName } from './Icon';
import { getInterestVisual } from '../constants/interests';
import { PLAY_STYLE_ICONS } from '../constants/interests';

interface SelectionCardProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    title: string;
    slug: string;
    icon?: IconName;
    accentColor?: string;
    description?: string;
    selected?: boolean;
    kind?: 'interest' | 'play-style' | 'default';
}

const SelectionCard = forwardRef<HTMLButtonElement, SelectionCardProps>(
    (
        {
            title,
            slug,
            description,
            accentColor,
            selected,
            kind = 'default',
            className,
            ...rest
        },
        ref
    ) => {
        const icon =
            kind === 'play-style'
                ? (PLAY_STYLE_ICONS[slug] as IconName | undefined)
                : undefined;

        const visual =
            kind === 'interest' ? getInterestVisual(slug) : null;

        return (
            <button
                ref={ref}
                type="button"
                className={cn('vs-chip', selected && 'vs-chip--active', className)}
                style={
                    selected && visual
                        ? { backgroundImage: visual.gradient, borderColor: 'transparent' }
                        : selected && accentColor
                        ? { borderColor: accentColor, boxShadow: `0 0 22px -6px ${accentColor}` }
                        : undefined
                }
                aria-pressed={selected}
                {...rest}
            >
                <div className="vs-chip__body">
                    <span
                        className="vs-chip__icon"
                        style={
                            visual
                                ? {
                                      background: selected ? 'rgba(255,255,255,0.18)' : visual.gradient,
                                  }
                                : undefined
                        }
                    >
                        {icon ? (
                            <Icon name={icon} size={16} className="vs-chip__lucide" />
                        ) : (
                            <span className={cn(visual && 'vs-chip__glyph')}>
                                {visual?.emojiGlyph ?? title?.charAt(0)}
                            </span>
                        )}
                    </span>
                    <span className="vs-chip__text">
                        <span className="vs-chip__title">{title}</span>
                        {description && <span className="vs-chip__desc">{description}</span>}
                    </span>
                </div>
                {selected && <span className="vs-chip__check" />}
            </button>
        );
    }
);

SelectionCard.displayName = 'SelectionCard';
export default SelectionCard;