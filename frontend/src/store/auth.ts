import { create } from 'zustand';
import { SessionState, SessionUser } from '../types/auth';
import {
    fetchCsrfToken,
    fetchSession,
    loginRequest,
    logoutRequest,
    refreshAccessToken,
} from '../services/auth';
import { ApiRequestError } from '../services/auth';

interface AuthState {
    initialized: boolean;
    authenticating: boolean;
    authenticated: boolean;
    onboarding_complete: boolean;
    user: SessionUser | null;

    init: () => Promise<void>;
    login: (identifier: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    applySession: (session: SessionState) => void;
    setUser: (fn: (user: SessionUser) => SessionUser) => void;
}

export const useAuthStore = create<AuthState>((set, get) => ({
    initialized: false,
    authenticating: true,
    authenticated: false,
    onboarding_complete: false,
    user: null,

    init: async () => {
        if (get().initialized) return;
        await fetchCsrfToken().catch(() => undefined);
        // JWT boot: if a rotating refresh cookie exists, exchange it for a
        // fresh access token before reading the session. Falls back cleanly to
        // the Django session cookie (admin/dev) when no refresh cookie exists.
        await refreshAccessToken().catch(() => false);
        const session = await fetchSession();
        set({
            initialized: true,
            authenticating: false,
            authenticated: session.authenticated,
            onboarding_complete: session.onboarding_complete,
            user: session.user,
        });
    },

    login: async (identifier, password) => {
        const session = await loginRequest(identifier, password);
        applyServerSession(set, session);
    },

    logout: async () => {
        try {
            await logoutRequest();
        } catch {
            // still clear local session
        }
        set({
            initialized: true,
            authenticating: false,
            authenticated: false,
            onboarding_complete: false,
            user: null,
        });
        localStorage.removeItem('vs-auth-session-cache');
    },

    applySession: (session) => {
        applyServerSession(set, session);
    },

    setUser: (fn) => {
        const user = get().user;
        if (!user) return;
        set({ user: fn(user) });
    },
}));

function applyServerSession(
    set: (partial: Partial<AuthState>) => void,
    session: SessionState
) {
    set({
        initialized: true,
        authenticating: false,
        authenticated: session.authenticated,
        onboarding_complete: session.onboarding_complete,
        user: session.user,
    });
}

export function isApiAuthError(err: unknown): err is ApiRequestError {
    return err instanceof ApiRequestError && (err.code === 'auth_failed' || err.status === 401);
}