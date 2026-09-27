import { request } from './api';
import { HomeFeed } from '../types/home';

export async function fetchHome(): Promise<HomeFeed> {
    const res = await request<HomeFeed>('/home/', { skipCsrf: true });
    if (!res.ok || !res.data) {
        const err = new Error(res.error?.message ?? 'Request failed') as Error & {
            code: string;
            status: number;
        };
        err.code = res.error?.code ?? 'error';
        err.status = res.status;
        throw err;
    }
    return res.data;
}