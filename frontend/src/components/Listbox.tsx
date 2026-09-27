import { useEffect, useMemo, useRef, useState } from 'react';
import { cn } from '../utils/cn';

export function useAutofocus<T extends HTMLElement>(active = true) {
    const ref = useRef<T>(null);
    useEffect(() => {
        if (active) {
            const t = setTimeout(() => ref.current?.focus(), 60);
            return () => clearTimeout(t);
        }
    }, [active]);
    return ref;
}

export function Listbox<T>({
    options,
    value,
    onChange,
    getKey,
    getLabel,
    placeholder = 'Search or select…',
    emptyLabel = 'No matches yet.',
    className,
}: {
    options: T[];
    value: string | null;
    onChange: (key: string) => void;
    getKey: (o: T) => string;
    getLabel: (o: T) => string;
    placeholder?: string;
    emptyLabel?: string;
    className?: string;
}) {
    const [open, setOpen] = useState(false);
    const [query, setQuery] = useState('');
    const boxRef = useRef<HTMLDivElement>(null);

    const filtered = useMemo(() => {
        const q = query.trim().toLowerCase();
        if (!q) return options;
        return options.filter((o) => getLabel(o).toLowerCase().includes(q));
    }, [options, query, getLabel]);

    const selected = options.find((o) => getKey(o) === value) ?? null;

    useEffect(() => {
        const onDoc = (e: MouseEvent) => {
            if (boxRef.current && !boxRef.current.contains(e.target as Node)) {
                setOpen(false);
            }
        };
        document.addEventListener('mousedown', onDoc);
        return () => document.removeEventListener('mousedown', onDoc);
    }, []);

    return (
        <div ref={boxRef} className={cn('vs-listbox', className)}>
            <button
                type="button"
                className="vs-listbox__trigger"
                onClick={() => {
                    setOpen((v) => !v);
                    setQuery('');
                }}
                aria-haspopup="listbox"
                aria-expanded={open}
            >
                <span>{selected ? getLabel(selected) : placeholder}</span>
                <span className={cn('vs-listbox__caret', open && 'vs-rotate-180')}>▾</span>
            </button>
            {open && (
                <div className="vs-listbox__menu">
                    <input
                        className="vs-listbox__search"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Type to filter…"
                        autoFocus
                    />
                    <div className="vs-listbox__options" role="listbox">
                        {filtered.length === 0 && (
                            <div className="vs-listbox__empty">{emptyLabel}</div>
                        )}
                        {filtered.map((o) => {
                            const key = getKey(o);
                            const active = key === value;
                            return (
                                <button
                                    key={key}
                                    type="button"
                                    role="option"
                                    aria-selected={active}
                                    className={cn(active && 'vs-listbox__opt--active')}
                                    onClick={() => {
                                        onChange(key);
                                        setOpen(false);
                                    }}
                                >
                                    {getLabel(o)}
                                    {active && <span className="vs-listbox__tick">✓</span>}
                                </button>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}