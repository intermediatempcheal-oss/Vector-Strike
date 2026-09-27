import { request, setAccessToken, getAccessToken, refreshAccessToken } from './api';
import { SessionState } from '../types/auth';

export async function fetchCsrfToken(): Promise<void> {
    await request<{ csrfToken: string }>('/auth/csrf/', { skipCsrf: true, timeoutMs: 8000 });
}

export async function fetchSession(): Promise<SessionState> {
    const res = await request<SessionState>('/auth/session/', { skipCsrf: true });
    if (!res.ok || !res.data) {
        return { authenticated: false, onboarding_complete: false, user: null };
    }
    return res.data;
}

export async function loginRequest(
    identifier: string,
    password: string
): Promise<SessionState> {
    const res = await request<SessionState & { access?: string }>('/auth/login/', {
        method: 'POST',
        body: { identifier, password },
    });
    if (!res.ok) throw new ApiRequestError(res);
    if (res.data?.access) setAccessToken(res.data.access);
    return res.data as SessionState;
}

export async function logoutRequest(): Promise<void> {
    try {
        await request('/auth/logout/', { method: 'POST' });
    } finally {
        setAccessToken(null);
    }
}

export { getAccessToken, refreshAccessToken };

export async function forgotPasswordRequest(identifier: string): Promise<void> {
    const res = await request<{ sent: boolean }>('/auth/password/reset/', {
        method: 'POST',
        body: { identifier },
    });
    if (!res.ok) throw new ApiRequestError(res);
}

export async function resetPasswordRequest(
    token: string,
    newPassword: string
): Promise<void> {
    const res = await request<{ reset: boolean }>('/auth/password/reset/confirm/', {
        method: 'POST',
        body: { token, new_password: newPassword },
    });
    if (!res.ok) throw new ApiRequestError(res);
}

export async function verifyEmailRequest(token: string): Promise<{ email: string }> {
    const res = await request<{ verified: boolean; email?: string }>('/auth/email/verify/', {
        method: 'POST',
        body: { token },
    });
    if (!res.ok || !res.data) throw new ApiRequestError(res);
    return { email: res.data.email ?? '' };
}

export async function resendVerificationEmail(): Promise<void> {
    const res = await request<{ sent: boolean }>('/auth/email/verify/request/', {
        method: 'POST',
        body: {},
    });
    if (!res.ok) throw new ApiRequestError(res);
}

export class ApiRequestError extends Error {
    code: string;
    fields: Record<string, unknown>;
    status: number;

    constructor(result: { status: number; error?: { code: string; message: string; fields: Record<string, unknown> } }) {
        super(result.error?.message ?? 'Request failed');
        this.name = 'ApiRequestError';
        this.code = result.error?.code ?? 'error';
        this.fields = result.error?.fields ?? {};
        this.status = result.status;
    }
}