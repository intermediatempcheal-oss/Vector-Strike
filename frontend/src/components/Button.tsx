import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '../utils/cn';
import Icon, { IconName } from './Icon';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'ghost' | 'outline' | 'danger';
    size?: 'sm' | 'md' | 'lg' | 'xl';
    loading?: boolean;
    icon?: IconName;
    iconRight?: IconName;
    fullWidth?: boolean;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    (
        {
            variant = 'primary',
            size = 'md',
            loading = false,
            icon,
            iconRight,
            fullWidth,
            className,
            children,
            disabled,
            ...rest
        },
        ref
    ) => {
        return (
            <button
                ref={ref}
                className={cn(
                    'vs-btn',
                    `vs-btn--${variant}`,
                    `vs-btn--${size}`,
                    fullWidth && 'vs-btn--full',
                    className
                )}
                disabled={disabled || loading}
                {...rest}
            >
                {loading ? (
                    <span className="vs-btn__spinner" aria-hidden />
                ) : (
                    icon && <Icon name={icon} size={18} />
                )}
                {children}
                {iconRight && !loading && <Icon name={iconRight} size={18} />}
            </button>
        );
    }
);

Button.displayName = 'Button';
export default Button;