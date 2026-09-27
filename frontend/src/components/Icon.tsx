import { ReactNode } from 'react';
import { cn } from '../utils/cn';

export type IconName =
    | 'bolt'
    | 'puzzle'
    | 'brain'
    | 'compass'
    | 'target'
    | 'users'
    | 'book'
    | 'message'
    | 'check'
    | 'chevron'
    | 'arrow'
    | 'lock'
    | 'upload'
    | 'shield'
    | 'info'
    | 'sparkles'
    | 'rocket'
    | 'user'
    | 'phone'
    | 'calendar'
    | 'globe'
    | 'eye'
    | 'eye-off'
    | 'alert'
    | 'refresh'
    | 'gamepad'
    | 'home'
    | 'search'
    | 'bell'
    | 'menu'
    | 'x'
    | 'trophy'
    | 'logout'
    | 'settings'
    | 'help'
    | 'star'
    | 'flame'
    | 'play'
    | 'layers'
    | 'medal'
    | 'clock'
    | 'pause'
    | 'rotate'
    | 'chevron-left'
    | 'chevron-right'
    | 'list'
    | 'filter'
    | 'grid'
    | 'timer'
    | 'crown'
    | 'diamond'
    | 'chart'
    | 'swap';

const PATHS: Record<IconName, ReactNode> = {
    bolt: <path d="M13 2 4 14h6l-1 8 9-12h-6l1-8z" />,
    puzzle: (
        <>
            <path d="M9 3h4v2a2 2 0 0 0 4 0V3h4v4h-2a2 2 0 0 0 0 4h2v4h-4a2 2 0 0 0-4 0v2a2 2 0 0 1-4 0v-2a2 2 0 0 0-4 0H3V7h2a2 2 0 0 0 4 0V3z" />
        </>
    ),
    brain: (
        <>
            <path d="M12 4a3 3 0 0 0-3 3v1H7a3 3 0 0 0-2 5.2A3 3 0 0 0 8 17h1v1a3 3 0 0 0 6 0v-9a3 3 0 0 0-3-3z" />
            <path d="M12 4a3 3 0 0 1 3 3v1h2a3 3 0 0 1 2 5.2A3 3 0 0 1 16 17h-1v1a3 3 0 0 1-6 0" />
        </>
    ),
    compass: (
        <>
            <circle cx="12" cy="12" r="9" />
            <path d="m15.5 8.5-2 5-5 2 2-5 5-2z" />
        </>
    ),
    target: (
        <>
            <circle cx="12" cy="12" r="9" />
            <circle cx="12" cy="12" r="5" />
            <circle cx="12" cy="12" r="1" fill="currentColor" />
        </>
    ),
    users: (
        <>
            <circle cx="9" cy="8" r="3.2" />
            <path d="M3.5 19c.4-3 2.6-4.6 5.5-4.6s5.1 1.6 5.5 4.6" />
            <path d="M16 5.2a3 3 0 0 1 0 5.6M17.5 14.6c1.6.7 2.6 2 2.9 4" />
        </>
    ),
    book: (
        <>
            <path d="M4 5a2 2 0 0 1 2-2h14v16H6a2 2 0 0 0-2 2V5z" />
            <path d="M4 5a2 2 0 0 1 2-2h14v16H6a2 2 0 0 0-2 2z" />
            <path d="M8 7h8M8 11h5" />
        </>
    ),
    message: (
        <>
            <path d="M5 7.5A2.5 2.5 0 0 1 7.5 5h9A2.5 2.5 0 0 1 19 7.5v6A2.5 2.5 0 0 1 16.5 16H12l-4 3v-3H7.5A2.5 2.5 0 0 1 5 13.5v-6z" />
            <path d="M8.8 9.5h6.4M8.8 12h4.8" />
        </>
    ),
    check: <path d="M5 12.5 9.5 17 19 7" />,
    chevron: <path d="m9 18 6-6-6-6" />,
    arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
    lock: (
        <>
            <rect x="5" y="11" width="14" height="9" rx="2" />
            <path d="M8 11V8a4 4 0 0 1 8 0v3" />
        </>
    ),
    upload: (
        <>
            <path d="M12 16V4M6 10l6-6 6 6" />
            <path d="M5 20h14" />
        </>
    ),
    shield: (
        <>
            <path d="M12 3 20 6v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3z" />
            <path d="m9.5 12 2 2 3.5-4" />
        </>
    ),
    info: (
        <>
            <circle cx="12" cy="12" r="9" />
            <path d="M12 11v5M12 8h.01" />
        </>
    ),
    sparkles: (
        <>
            <path d="M12 3l1.8 4.9L19 10l-5.2 2.1L12 17l-1.8-4.9L5 10l5.2-2.1L12 3z" />
            <path d="M19 15l.9 2.4L22 18.5l-2.1.9L19 22l-.9-2.6L16 18.5l2.1-1.1L19 15z" />
        </>
    ),
    rocket: (
        <>
            <path d="M5 15c-1.5 1.5-2 5-2 5s3.5-.5 5-2c.9-1 .7-2.5-.3-3.3a2.4 2.4 0 0 0-2.7.3zM8.5 10.5C9.5 6 13 3 19 3c0 6-3 9.5-7.5 10.5" />
            <circle cx="15" cy="9" r="1.5" />
        </>
    ),
    user: (
        <>
            <circle cx="12" cy="8" r="3.5" />
            <path d="M5 20c.6-3.4 3.2-5 7-5s6.4 1.6 7 5" />
        </>
    ),
    phone: <path d="M5 4h4l1.5 4-2 1.5a11 11 0 0 0 6 6L16 13l4 1.5V19a2 2 0 0 1-2 2C9 21 3 15 3 6a2 2 0 0 1 2-2z" />,
    calendar: (
        <>
            <rect x="3.5" y="5" width="17" height="16" rx="2.5" />
            <path d="M8 3v4M16 3v4M3.5 10.5h17" />
        </>
    ),
    globe: (
        <>
            <circle cx="12" cy="12" r="9" />
            <path d="M3 12h18M12 3c2.5 2.5 2.5 15 0 18M12 3c-2.5 2.5-2.5 15 0 18" />
        </>
    ),
    eye: (
        <>
            <path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z" />
            <circle cx="12" cy="12" r="3" />
        </>
    ),
    'eye-off': (
        <>
            <path d="M3 3l18 18M10.5 5.2A9.8 9.8 0 0 1 12 5.5c6 0 9.5 6.5 9.5 6.5a17 17 0 0 1-3.2 4M6.6 6.6A16.5 16.5 0 0 0 2.5 12S6 18.5 12 18.5c1.6 0 3-.3 4.2-.9" />
        </>
    ),
    alert: (
        <>
            <circle cx="12" cy="12" r="9" />
            <path d="M12 7.5V13M12 16.5h.01" />
        </>
    ),
    refresh: (
        <>
            <path d="M20 12a8 8 0 1 1-2.34-5.66" />
            <path d="M20 4v5h-5" />
        </>
    ),
    gamepad: (
        <>
            <path d="M7.5 8.5h1M8 8v1" />
            <path d="M16.2 7.3C12 5.6 6 5.6 4.4 8.9c-1.4 3-.5 8.9 2.3 8.9 1.6 0 2.6-1 4.5-1s2.9 1 4.5 1c2.8 0 3.7-5.9 2.3-8.9-.6-1.2-1.8-1.6-2.1-1.6z" />
            <path d="M17 12.5v-2M18 11.5h2" />
        </>
    ),
    home: (
        <>
            <path d="M3 10.5 12 3l9 7.5" />
            <path d="M5.5 9.5V21h13V9.5" />
            <path d="M9.5 21v-6h5v6" />
        </>
    ),
    search: (
        <>
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-4.2-4.2" />
        </>
    ),
    bell: (
        <>
            <path d="M6 16v-5a6 6 0 0 1 12 0v5l2 3H4l2-3z" />
            <path d="M10 21a2 2 0 0 0 4 0" />
        </>
    ),
    menu: (
        <>
            <path d="M4 7h16M4 12h16M4 17h16" />
        </>
    ),
    x: <path d="m6 6 12 12M18 6 6 18" />,
    trophy: (
        <>
            <path d="M8 4h8v5a4 4 0 0 1-8 0V4z" />
            <path d="M8 5H4v1a4 4 0 0 0 4 4M16 5h4v1a4 4 0 0 1-4 4" />
            <path d="M12 13v4M8 21h8M9.5 17h5l.5 4h-6l.5-4z" />
        </>
    ),
    logout: (
        <>
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
            <path d="m16 17 5-5-5-5M21 12H9" />
        </>
    ),
    settings: (
        <>
            <circle cx="12" cy="12" r="3.2" />
            <path d="M19 12a7 7 0 0 0-.14-1.4l2-1.55-2-3.46-2.36.95a7 7 0 0 0-2.42-1.4L13.7 2.8h-3.4l-.38 2.34a7 7 0 0 0-2.42 1.4L5.14 5.6l-2 3.46 2 1.55A7 7 0 0 0 5 12c0 .48.05.95.14 1.4l-2 1.55 2 3.46 2.36-.95a7 7 0 0 0 2.42 1.4l.38 2.34h3.4l.38-2.34a7 7 0 0 0 2.42-1.4l2.36.95 2-3.46-2-1.55c.09-.45.14-.92.14-1.4z" />
        </>
    ),
    help: (
        <>
            <circle cx="12" cy="12" r="9" />
            <path d="M9.3 9a2.8 2.8 0 0 1 5.4 1c0 1.8-2.7 2.2-2.7 4M12 17.5h.01" />
        </>
    ),
    star: (
        <>
            <path d="m12 3 2.7 5.5 6.1.9-4.4 4.3 1 6.1-5.4-2.9-5.4 2.9 1-6.1L3.2 9.4l6.1-.9L12 3z" />
        </>
    ),
    flame: (
        <>
            <path d="M12 3c.4 3.2-.6 4.9-2 6.5C8.3 11.4 7 13 7 15.5a5 5 0 0 0 10 0c0-2-.8-3.3-2.1-4.9-.3 1-.7 1.6-1.5 2-.2-2.6-1-6.1-1.4-9.6z" />
        </>
    ),
    play: <path d="M7 5v14l11-7L7 5z" />,
    layers: (
        <>
            <path d="m12 3 9 5-9 5-9-5 9-5z" />
            <path d="m3 13 9 5 9-5" />
        </>
    ),
    medal: (
        <>
            <circle cx="12" cy="15" r="5" />
            <path d="m8.5 12.5-2-7 4 1.5L12 3l1.5 4 4-1.5-2 7" />
        </>
    ),
    clock: (
        <>
            <circle cx="12" cy="12" r="9" />
            <path d="M12 7v5l3.5 2" />
        </>
    ),
    pause: (
        <>
            <path d="M9 5v14M15 5v14" />
        </>
    ),
    rotate: (
        <>
            <path d="M20 12a8 8 0 1 1-2.34-5.66" />
            <path d="M20 4v5h-5" />
        </>
    ),
    'chevron-left': <path d="m15 6-6 6 6 6" />,
    'chevron-right': <path d="m9 6 6 6-6 6" />,
    list: (
        <>
            <path d="M9 6h11M9 12h11M9 18h11" />
            <path d="M4 6h.01M4 12h.01M4 18h.01" />
        </>
    ),
    filter: (
        <>
            <path d="M4 5h16l-6 7v6l-4 2v-8L4 5z" />
        </>
    ),
    grid: (
        <>
            <rect x="4" y="4" width="7" height="7" rx="1.5" />
            <rect x="13" y="4" width="7" height="7" rx="1.5" />
            <rect x="4" y="13" width="7" height="7" rx="1.5" />
            <rect x="13" y="13" width="7" height="7" rx="1.5" />
        </>
    ),
    timer: (
        <>
            <circle cx="12" cy="13" r="8" />
            <path d="M12 13V9M9 2h6" />
        </>
    ),
    crown: (
        <>
            <path d="M4 18h16M4 18l-1-9 5 4 4-7 4 7 5-4-1 9" />
        </>
    ),
    diamond: (
        <>
            <path d="M12 3l7 7-7 11-7-11 7-7z" />
        </>
    ),
    chart: (
        <>
            <path d="M4 20V4" />
            <path d="M4 20h16" />
            <path d="M8 16v-4M12 16V8M16 16v-6" />
        </>
    ),
    swap: (
        <>
            <path d="M8 4 4 8l4 4" />
            <path d="M4 8h12M16 20l4-4-4-4" />
            <path d="M20 16H8" />
        </>
    ),
};

interface IconProps {
    name: IconName;
    size?: number | string;
    className?: string;
    strokeWidth?: number;
}

export default function Icon({ name, size = 18, className, strokeWidth = 1.8 }: IconProps) {
    return (
        <svg
            width={size}
            height={size}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn('vs-icon', className)}
            aria-hidden
        >
            {PATHS[name]}
        </svg>
    );
}