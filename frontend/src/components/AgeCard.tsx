import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '../utils/cn';
import Icon, { IconName } from './Icon';

interface AgeCardProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    label: string;
    hint: string;
    icon: IconName;
    selected?: boolean;
}

const AgeCard = forwardRef<HTMLButtonElement, AgeCardProps>(
    ({ label, hint, icon, selected, className, ...rest }, ref) => {
        return (
            <button
                ref={ref}
                type="button"
                className={cn('vs-age-card', selected && 'vs-age-card--active', className)}
                aria-pressed={selected}
                {...rest}
            >
                <span className="vs-age-card__icon">
                    <Icon name={icon} size={24} />
                </span>
                <span className="vs-age-card__text">
                    <span className="vs-age-card__label">{label}</span>
                    <span className="vs-age-card__hint">{hint}</span>
                </span>
                <span className="vs-age-card__radio" aria-hidden>
                    {selected && <span />}
                </span>
            </button>
        );
    }
);

AgeCard.displayName = 'AgeCard';
export default AgeCard;