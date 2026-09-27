import {
    ChangeEvent,
    InputHTMLAttributes,
    ReactNode,
    forwardRef,
    useEffect,
    useId,
    useState,
} from 'react';
import { cn } from '../utils/cn';
import Icon, { IconName } from './Icon';

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string | null;
    hint?: ReactNode;
    icon?: IconName;
    trailing?: ReactNode;
    success?: boolean;
}

const TextField = forwardRef<HTMLInputElement, TextFieldProps>(
    ({ label, error, hint, icon, trailing, success, className, ...rest }, ref) => {
        const uid = useId();
        const [focused, setFocused] = useState(false);
        const [touched, setTouched] = useState(false);
        const showError = Boolean(error) && touched;

        useEffect(() => {
            if (error) setTouched(true);
        }, [error]);

        return (
            <div className={cn('vs-field', className)}>
                {label && (
                    <label className="vs-field__label" htmlFor={uid}>
                        {label}
                    </label>
                )}
                <div
                    className={cn(
                        'vs-field__inner',
                        focused && 'vs-field__inner--focus',
                        showError && 'vs-field__inner--error',
                        success && !error && 'vs-field__inner--success'
                    )}
                >
                    {icon && (
                        <span className="vs-field__adorn vs-field__adorn--left">
                            <Icon name={icon} size={16} />
                        </span>
                    )}
                    <input
                        ref={ref}
                        id={uid}
                        className="vs-field__input"
                        onFocus={(e) => {
                            setFocused(true);
                            rest.onFocus?.(e);
                        }}
                        onBlur={(e) => {
                            setFocused(false);
                            setTouched(true);
                            rest.onBlur?.(e);
                        }}
                        onChange={(e: ChangeEvent<HTMLInputElement>) => {
                            setTouched(true);
                            rest.onChange?.(e);
                        }}
                        {...rest}
                    />
                    {trailing}
                </div>
                {hint && !showError && <div className="vs-field__hint">{hint}</div>}
                {showError && <div className="vs-field__error">{error}</div>}
            </div>
        );
    }
);

TextField.displayName = 'TextField';
export default TextField;