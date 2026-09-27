import { request, ApiResult, setAccessToken } from './api';
import { RegisterResponse } from '../types/auth';
import {
    BranchInfo,
    OnboardingConfig,
    OnboardingProgressResume,
    RegistrationPayload,
    UploadDocumentResult,
    UsernameCheckResult,
} from '../types/onboarding';
import { ApiRequestError } from './auth';
import { useAuthStore } from '../store/auth';

export class OnboardingService {
    private static config: OnboardingConfig | null = null;

    static async fetchConfig(force = false): Promise<OnboardingConfig> {
        if (this.config && !force) return this.config;
        const res = await request<OnboardingConfig>('/onboarding/config/', { skipCsrf: true });
        if (!res.ok || !res.data) {
            throw new ApiRequestError(res as { status: number; error?: { code: string; message: string; fields: Record<string, unknown> } });
        }
        this.config = res.data;
        return res.data;
    }

    static async getInterests(): Promise<{ count: number; results: OnboardingConfig['interests'] }> {
        const res = await request<{ count: number; results: OnboardingConfig['interests'] }>('/interests/', { skipCsrf: true });
        if (!res.ok || !res.data) throw new ApiRequestError(res);
        return res.data;
    }

    static async checkAge(dateOfBirth: string, region?: string): Promise<BranchInfo> {
        const res = await request<BranchInfo>('/onboarding/age-check/', {
            method: 'POST',
            body: { date_of_birth: dateOfBirth, region: region ?? '' },
        });
        if (!res.ok || !res.data) throw new ApiRequestError(res);
        return res.data;
    }

    static async checkUsername(username: string): Promise<UsernameCheckResult> {
        const res = await request<UsernameCheckResult>('/username/check/', {
            method: 'POST',
            body: { username },
        });
        if (!res.ok || !res.data) {
            throw new ApiRequestError(res);
        }
        return res.data;
    }

    static async uploadDocument(file: File, region?: string): Promise<UploadDocumentResult> {
        const formData = new FormData();
        formData.append('document', file);
        if (region) formData.append('region', region);
        const res = await request<UploadDocumentResult>('/verification/upload/', {
            method: 'POST',
            formData,
        });
        if (!res.ok || !res.data) throw new ApiRequestError(res);
        return res.data;
    }

    static async register(payload: RegistrationPayload): Promise<RegisterResponse> {
        const res = await request<RegisterResponse & { access?: string }>('/accounts/register/', {
            method: 'POST',
            body: payload,
        });
        if (!res.ok || !res.data) throw new ApiRequestError(res);
        if (res.data.access) setAccessToken(res.data.access);
        useAuthStore.getState().applySession({
            authenticated: true,
            onboarding_complete: res.data.onboarding_complete,
            user: res.data.user,
        });
        return res.data;
    }

    static async fetchFirstExperience(): Promise<{
        interests: string[];
        play_styles: string[];
        recommendations: NonNullable<RegisterResponse['recommendations']>;
    }> {
        const res = await request<{
            interests: string[];
            play_styles: string[];
            recommendations: NonNullable<RegisterResponse['recommendations']>;
        }>('/onboarding/first-experience/', { skipCsrf: true });
        if (!res.ok || !res.data) throw new ApiRequestError(res);
        return res.data;
    }

    static async saveProgress(step: string): Promise<OnboardingProgressResume> {
        const res = await request<OnboardingProgressResume>('/onboarding/progress/', {
            method: 'PUT',
            body: { current_step: step },
        });
        if (!res.ok || !res.data) throw new ApiRequestError(res);
        return res.data;
    }
}

export type { ApiResult };