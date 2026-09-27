import { cn } from '../utils/cn';
import { useEffect, useRef, useState } from 'react';

interface LogoProps {
    size?: 'sm' | 'md' | 'lg';
    className?: string;
    showWordmark?: boolean;
}

const SIZES = {
    sm: { mark: 40, text: 'text-base', sub: 'text-[11px]' },
    md: { mark: 52, text: 'text-xl', sub: 'text-xs' },
    lg: { mark: 72, text: 'text-3xl', sub: 'text-sm' },
};

export default function Logo({ size = 'md', className, showWordmark = true }: LogoProps) {
    const s = SIZES[size];
    return (
        <div className={cn('vs-logo', showWordmark && 'vs-logo--row', className)}>
            <img
                src="/assets/branding/logo-mark.svg"
                alt=""
                aria-hidden
                width={s.mark}
                height={s.mark}
                className="vs-logo__mark"
                draggable={false}
            />
            {showWordmark && (
                <div className="vs-logo__text">
                    <span className={cn('vs-logo__word', s.text)}>VECTOR STRIKE</span>
                    <span className={cn('vs-logo__sub', s.sub)}>Learn by playing</span>
                </div>
            )}
        </div>
    );
}

function useMounted(active: boolean) {
    const [mounted, setMounted] = useState(active);
    useEffect(() => {
        if (active) setMounted(true);
    }, [active]);
    return mounted;
}

export function SplashLogo({ onDone }: { onDone: () => void }) {
    const [phase, setPhase] = useState<'hidden' | 'mode' | 'slice' | 'done'>('hidden');
    const started = useRef(false);

    useEffect(() => {
        if (started.current) return;
        started.current = true;
        const t1 = setTimeout(() => setPhase('mode'), 150);
        const t2 = setTimeout(() => setPhase('slice'), 950);
        const t3 = setTimeout(() => setPhase('done'), 1750);
        const t4 = setTimeout(onDone, 2300);
        return () => {
            clearTimeout(t1);
            clearTimeout(t2);
            clearTimeout(t3);
            clearTimeout(t4);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <div className="vs-splash-logo" aria-hidden>
            <Logo size="lg" showWordmark className="vs-splash-logo__inner" />
            <div className="vs-splash-logo__mode" data-phase={phase} />
        </div>
    );
}

export { useMounted };