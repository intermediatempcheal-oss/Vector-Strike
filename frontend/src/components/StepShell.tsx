import { ReactNode } from 'react';
import { cn } from '../utils/cn';

interface StepShellProps {
    eyebrow?: string;
    title: string;
    subtitle?: ReactNode;
    children: ReactNode;
    aside?: ReactNode;
    className?: string;
    wide?: boolean;
}

export default function StepShell({ eyebrow, title, subtitle, children, aside, className, wide }: StepShellProps) {
    return (
        <div className={cn('vs-step', wide && 'vs-step--wide', className)}>
            <div className="vs-step__copy">
                {eyebrow && <span className="vs-step__eyebrow">{eyebrow}</span>}
                <h1 className="vs-step__title">{title}</h1>
                {subtitle && <div className="vs-step__subtitle">{subtitle}</div>}
                {children}
            </div>
            {aside && <div className="vs-step__aside">{aside}</div>}
        </div>
    );
}