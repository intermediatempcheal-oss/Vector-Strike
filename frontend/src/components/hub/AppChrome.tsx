import { ReactNode, useEffect } from 'react';
import HubChrome, { NavTarget } from './HubChrome';
import { useAppStore } from '../../store/app';
import { useAuthStore } from '../../store/auth';

/**
 * Global authenticated shell: persistent navbar, desktop sidebar, mobile
 * bottom nav, profile DP menu and logout — shared by every authenticated page
 * so navigation never needs to be re-built per page.
 */
export default function AppChrome({
    active,
    search,
    noticeDot = false,
    children,
}: {
    active?: NavTarget;
    search?: ReactNode;
    noticeDot?: boolean;
    children: ReactNode;
}) {
    const { user } = useAuthStore();
    const profile = useAppStore((s) => s.profile);
    const displayName = profile?.display_name || user?.full_name || user?.username || 'Pilot';

    useEffect(() => {
        void useAppStore.getState().ensure();
    }, []);

    return (
        <HubChrome
            active={active}
            profile={profile}
            user={user}
            displayName={displayName}
            noticeDot={noticeDot}
            search={search}
        >
            {children}
        </HubChrome>
    );
}