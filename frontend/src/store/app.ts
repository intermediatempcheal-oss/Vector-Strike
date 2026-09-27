import { useEffect } from 'react';
import { create } from 'zustand';
import { fetchHome } from '../services/home';
import { HomeFeed, ProfileProgress } from '../types/home';

interface AppState {
    feed: HomeFeed | null;
    profile: ProfileProgress | null;
    loading: boolean;
    loadedOnce: boolean;
    /** Load (or refresh with force=true) the authenticated home feed + profile. */
    ensure: (force?: boolean) => Promise<HomeFeed | null>;
    setFeed: (feed: HomeFeed | null) => void;
    clear: () => void;
}

export const useAppStore = create<AppState>((set, get) => ({
    feed: null,
    profile: null,
    loading: false,
    loadedOnce: false,

    ensure: async (force = false) => {
        if (get().loading && !force) return get().feed;
        if (get().feed && !force) return get().feed;
        set({ loading: true });
        try {
            const feed = await fetchHome();
            set({ feed, profile: feed.profile, loading: false, loadedOnce: true });
            return feed;
        } catch (err) {
            set({ loading: false });
            throw err;
        }
    },

    setFeed: (feed) => set({ feed, profile: feed?.profile ?? null }),

    clear: () => set({ feed: null, profile: null, loadedOnce: false, loading: false }),
}));

/**
 * Shared profile for the global chrome. Fetches once through the app store
 * and reuses the cached feed across page transitions.
 */
export function useProfile(): {
    profile: ProfileProgress | null;
    loading: boolean;
    loadedOnce: boolean;
} {
    const profile = useAppStore((s) => s.profile);
    const loading = useAppStore((s) => s.loading);
    const loadedOnce = useAppStore((s) => s.loadedOnce);

    useEffect(() => {
        void useAppStore.getState().ensure();
    }, []);

    return { profile, loading, loadedOnce };
}