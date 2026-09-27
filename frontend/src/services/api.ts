import { ApiErrorBody, ApiResult, NetworkError } from '../types/api';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';

function getCookie(name: string): string | null {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop()?.split(';').shift() ?? null;
    return null;
}

interface RequestOptions {
    method?: string;
    body?: unknown;
    formData?: FormData;
    headers?: Record<string, string>;
    timeoutMs?: number;
    skipCsrf?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<ApiResult<T>> {
    const { method = 'GET', body, formData, headers = {}, timeoutMs = 25000, skipCsrf = false } = options;

    const hadToken = Boolean(getAccessToken());
    const canRetryAuth = hadToken && !NO_AUTO_REFRESH.has(path.split('?')[0]);

    for (let attempt = 0; attempt <= (canRetryAuth ? 1 : 0); attempt++) {
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), timeoutMs);

        const requestHeaders = new Headers(headers);
        if (body !== undefined && !formData) {
            requestHeaders.set('Content-Type', 'application/json');
        }
        if (!skipCsrf) {
            const token = getCookie('csrftoken');
            if (token) requestHeaders.set('X-CSRFToken', token);
        }
        const currentToken = getAccessToken();
        if (currentToken) {
            requestHeaders.set('Authorization', `Bearer ${currentToken}`);
        }

        let response: Response;
        try {
            response = await fetch(`${API_BASE}${path}`, {
                method,
                credentials: 'include',
                headers: requestHeaders,
                body: formData ?? (body !== undefined ? JSON.stringify(body) : undefined),
                signal: controller.signal,
            });
        } catch (err) {
            clearTimeout(timer);
            if (err instanceof DOMException && err.name === 'AbortError') {
                return {
                    ok: false,
                    status: 0,
                    error: {
                        code: 'timeout',
                        message: 'The request took too long. Please try again.',
                        fields: {},
                    },
                };
            }
            return {
                ok: false,
                status: 0,
                error: {
                    code: 'network',
                    message: 'We couldn’t reach the server. Check your connection and try again.',
                    fields: {},
                },
            };
        }
        clearTimeout(timer);

        if (response.status === 401 && canRetryAuth && attempt === 0) {
            const refreshed = await refreshAccessToken();
            if (!refreshed) {
                setAccessToken(null);
            }
            if (refreshed) continue; // retry once with the fresh token
        }

        let payload: ApiErrorBody | unknown = null;
        const text = await response.text();
        try {
            payload = text ? JSON.parse(text) : null;
        } catch {
            payload = null;
        }

        if (!response.ok) {
            const err = (payload as ApiErrorBody)?.error;
            return {
                ok: false,
                status: response.status,
                error: {
                    code: err?.code ?? 'http_error',
                    message: err?.message ?? friendlyStatus(response.status),
                    fields: err?.fields ?? {},
                },
            };
        }

        return { ok: true, status: response.status, data: payload as T };
    }

    return {
        ok: false,
        status: 401,
        error: {
            code: 'auth_failed',
            message: 'Please sign in again.',
            fields: {},
        },
    };
}

function friendlyStatus(status: number): string {
    if (status === 429) return 'You’re moving too fast. Give it a moment and try again.';
    if (status >= 500) return 'We couldn’t complete that right now. Please try again.';
    if (status === 403) return 'You’re not allowed to do that.';
    if (status === 401) return 'Please sign in again.';
    return 'Something went wrong. Please try again.';
}

// ---------------------------------------------------------------------------
// JWT access token — kept in memory only (never persisted to storage) so a
// leaked token cannot be replayed after a reload. The refresh token itself
// lives in an HttpOnly SameSite=Lax cookie scoped to /api/v1/auth/.
// ---------------------------------------------------------------------------

let accessToken: string | null = null;
let refreshPromise: Promise<boolean> | null = null;

export function setAccessToken(token: string | null): void {
    accessToken = token || null;
}

export function getAccessToken(): string | null {
    return accessToken;
}

export async function refreshAccessToken(): Promise<boolean> {
    if (accessToken) return true;
    if (refreshPromise) return refreshPromise;
    refreshPromise = doRefresh().finally(() => {
        refreshPromise = null;
    });
    return refreshPromise;
}

async function doRefresh(): Promise<boolean> {
    try {
        const response = await fetch(`${API_BASE}/auth/token/refresh/`, {
            method: 'POST',
            credentials: 'include',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({}),
        });
        if (!response.ok) {
            setAccessToken(null);
            return false;
        }
        const payload = await response.json() as { access?: string };
        if (!payload.access) {
            setAccessToken(null);
            return false;
        }
        setAccessToken(payload.access);
        return true;
    } catch {
        setAccessToken(null);
        return false;
    }
}

// Paths where a 401 must NOT trigger an automatic refresh (bootstrap/login).
const NO_AUTO_REFRESH = new Set([
    '/auth/token/refresh/',
    '/auth/login/',
    '/auth/csrf/',
    '/auth/session/',
]);

export { getCookie, request };
export type { ApiResult, NetworkError };