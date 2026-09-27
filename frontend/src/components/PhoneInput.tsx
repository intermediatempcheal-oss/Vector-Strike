import { useEffect, useRef, useState } from 'react';
import { cn } from '../utils/cn';
import Icon from './Icon';
import { COUNTRIES, formatAsTyped, inferCountry, parseToE164 } from '../utils/phone';

interface PhoneInputProps {
    label?: string;
    value: string;
    onChange: (value: string, e164: string | null, country: string | null) => void;
    error?: string | null;
    placeholder?: string;
    className?: string;
    autoComplete?: string;
}

export default function PhoneInput({
    label,
    value,
    onChange,
    error,
    placeholder = '812 345 6789',
    className,
    autoComplete = 'tel',
}: PhoneInputProps) {
    const [country, setCountry] = useState<string>('US');
    const [open, setOpen] = useState(false);
    const [query, setQuery] = useState('');
    const listRef = useRef<HTMLDivElement>(null);

    const current = COUNTRIES.find((c) => c.code === country) ?? COUNTRIES[0];

    useEffect(() => {
        const onDoc = (e: MouseEvent) => {
            if (listRef.current && !listRef.current.contains(e.target as Node)) {
                setOpen(false);
            }
        };
        document.addEventListener('mousedown', onDoc);
        return () => document.removeEventListener('mousedown', onDoc);
    }, []);

    const handleCountry = (code: string, dial: string) => {
        setCountry(code);
        const bare = value.replace(/\D/g, '');
        const combined = `${dial}${bare}`;
        const e164 = parseToE164(combined, code);
        onChange(formatAsTyped(value, code), e164, code);
        setOpen(false);
        setQuery('');
    };

    const handleText = (raw: string) => {
        const typed = formatAsTyped(raw, country);
        const detected = inferCountry(typed);
        const effective = detected ?? country;
        if (detected && detected !== country) setCountry(detected);
        const e164 = parseToE164(typed, effective);
        onChange(typed, e164, effective);
    };

    const filtered = COUNTRIES.filter((c) => {
        const q = query.trim().toLowerCase();
        if (!q) return true;
        return (
            c.name.toLowerCase().includes(q) ||
            c.code.toLowerCase().includes(q) ||
            c.dial.includes(q.replace('+', ''))
        );
    });

    return (
        <div
            className={cn('vs-field', className)}
            ref={listRef}
        >
            {label && <label className="vs-field__label">{label}</label>}
            <div
                className={cn(
                    'vs-field__inner vs-phone',
                    error && 'vs-field__inner--error'
                )}
            >
                <button
                    type="button"
                    className="vs-phone__country"
                    onClick={() => setOpen((v) => !v)}
                    aria-haspopup="listbox"
                    aria-expanded={open}
                >
                    <span className="vs-phone__dial">{current.dial}</span>
                    <Icon name="chevron" size={13} className={cn(open && 'vs-rotate-180')} />
                </button>
                <input
                    className="vs-field__input"
                    value={value}
                    onChange={(e) => handleText(e.target.value)}
                    placeholder={placeholder}
                    autoComplete={autoComplete}
                    inputMode="tel"
                    aria-label={label ?? 'Phone number'}
                />
            </div>
            {open && (
                <div className="vs-phone__list">
                    <div className="vs-phone__search">
                        <Icon name="globe" size={14} />
                        <input
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            placeholder="Search country…"
                            autoFocus
                        />
                    </div>
                    <div className="vs-phone__options" role="listbox">
                        {filtered.map((c) => (
                            <button
                                key={c.code}
                                type="button"
                                className={cn(c.code === country && 'vs-phone__opt--active')}
                                onClick={() => handleCountry(c.code, c.dial)}
                                role="option"
                                aria-selected={c.code === country}
                            >
                                <span className="vs-phone__opt-code">{c.code}</span>
                                <span className="vs-phone__opt-name">{c.name}</span>
                                <span className="vs-phone__opt-dial">{c.dial}</span>
                            </button>
                        ))}
                    </div>
                </div>
            )}
            {error && <div className="vs-field__error">{error}</div>}
        </div>
    );
}